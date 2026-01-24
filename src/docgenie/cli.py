"""Command-line interface for DocGenie."""

from __future__ import annotations

import json
import webbrowser
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .core import CodebaseAnalyzer
from .generator import ReadmeGenerator
from .html_generator import HTMLGenerator
from .logging import configure_logging, get_logger

app = typer.Typer(add_completion=False, help="DocGenie - Auto-documentation for any codebase.")
console = Console()

OutputSpec = tuple[str, Path]


def _print_summary(analysis_data: dict, target_formats: str) -> None:
    table = Table(title="DocGenie Summary", show_lines=True)
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Project", analysis_data.get("project_name", "unknown"))
    table.add_row("Files", str(analysis_data.get("files_analyzed", 0)))
    table.add_row("Languages", ", ".join(analysis_data.get("languages", {}).keys()))
    table.add_row("Functions", str(len(analysis_data.get("functions", []))))
    table.add_row("Classes", str(len(analysis_data.get("classes", []))))
    table.add_row("Format", target_formats)
    repo = analysis_data.get("git_info", {}).get("remote_url")
    if repo:
        table.add_row("Repository", repo)
    console.print(table)


def _validate_format(fmt: str) -> str:
    target_formats = fmt.lower()
    if target_formats not in {"markdown", "html", "both"}:
        typer.echo("Invalid format. Choose markdown, html, or both.")
        raise typer.Exit(code=1)
    return target_formats


def _run_analysis(path: Path, ignore: list[str], tree_sitter: bool, verbose: bool) -> dict:
    analyzer = CodebaseAnalyzer(str(path), ignore, enable_tree_sitter=tree_sitter)
    with Progress(console=console, transient=True) as progress:
        task = progress.add_task("Analyzing codebase...", total=100)
        analysis_data = analyzer.analyze()
        progress.update(task, completed=100)
    if verbose:
        console.log("Analysis complete")
    return analysis_data


def _build_outputs(target_formats: str, output: Path | None, base: Path) -> list[OutputSpec]:
    outputs: list[OutputSpec] = []
    if target_formats in {"markdown", "both"}:
        outputs.append(("markdown", _resolve_output(output, base, "README.md")))
    if target_formats in {"html", "both"}:
        outputs.append(("html", _resolve_output(output, base, "docs.html")))
    return outputs


def _confirm_overwrite(outputs: list[OutputSpec], *, preview: bool, force: bool) -> None:
    if preview or force:
        return
    for _, out_path in outputs:
        if out_path.exists() and not typer.confirm(f"{out_path.name} exists. Overwrite?"):
            typer.echo("Operation cancelled.")
            raise typer.Exit(code=1)


def _render_outputs(outputs: list[OutputSpec], analysis_data: dict, *, preview: bool) -> None:
    for output_format, output_path in outputs:
        if output_format == "markdown":
            generator = ReadmeGenerator()
            content = generator.generate(analysis_data, None if preview else str(output_path))
            if preview:
                console.rule("README Preview")
                typer.echo(content)
            else:
                console.log(f"[green]README generated:[/green] {output_path}")
        else:
            html_generator = HTMLGenerator()
            content = html_generator.generate_from_analysis(
                analysis_data, None if preview else str(output_path)
            )
            if preview:
                console.rule("HTML Preview (truncated)")
                typer.echo("\n".join(content.splitlines()[:80]))
            else:
                console.log(f"[green]HTML generated:[/green] {output_path}")


@app.command("generate")
def generate(  # noqa: PLR0913
    path: Path = typer.Argument(
        Path("."), exists=True, file_okay=False, dir_okay=True, resolve_path=True
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output path for documentation."
    ),
    fmt: str = typer.Option(
        "markdown",
        "--format",
        "--fmt",
        help="Output format",
        case_sensitive=False,
        rich_help_panel="Output",
    ),
    ignore: list[str] = typer.Option([], "--ignore", "-i", help="Additional ignore patterns"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview without saving"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    tree_sitter: bool = typer.Option(
        True,
        "--tree-sitter/--no-tree-sitter",
        help="Enable tree-sitter parsing when available",
    ),
    json_logs: bool = typer.Option(False, "--json-logs", help="Output structured logs as JSON"),
) -> None:
    """Generate README and/or HTML docs for a codebase."""
    configure_logging(verbose=verbose, json_output=json_logs)
    logger = get_logger(__name__)

    target_formats = _validate_format(fmt)
    console.rule("[bold cyan]DocGenie")
    logger.info("Starting documentation generation", path=str(path), format=target_formats)

    analysis_data = _run_analysis(path, ignore, tree_sitter, verbose)
    outputs = _build_outputs(target_formats, output, path)
    _confirm_overwrite(outputs, preview=preview, force=force)
    _render_outputs(outputs, analysis_data, preview=preview)

    if not preview:
        _print_summary(analysis_data, target_formats)


def _resolve_output(output: Path | None, base: Path, default_name: str) -> Path:
    if output is None:
        return base / default_name
    if output.is_dir():
        return output / default_name
    return output


@app.command("analyze")
def analyze(
    path: Path = typer.Argument(Path("."), exists=True, resolve_path=True),
    fmt: str = typer.Option("text", "--format", "-f", help="Output format"),
    tree_sitter: bool = typer.Option(
        True,
        "--tree-sitter/--no-tree-sitter",
        help="Enable tree-sitter parsing when available",
    ),
) -> None:
    """Analyze a codebase and print structured results."""
    analyzer = CodebaseAnalyzer(str(path), enable_tree_sitter=tree_sitter)
    analysis_data = analyzer.analyze()

    if fmt == "json":
        typer.echo(json.dumps(analysis_data, indent=2))
    elif fmt == "yaml":
        typer.echo(yaml.dump(analysis_data, default_flow_style=False))
    else:
        typer.echo("🔍 Codebase Analysis Results")
        typer.echo(f"Path: {analysis_data.get('root_path')}")
        typer.echo(f"Files analyzed: {analysis_data['files_analyzed']}")
        typer.echo(f"Languages: {', '.join(analysis_data['languages'].keys())}")
        typer.echo(f"Functions: {len(analysis_data['functions'])}")
        typer.echo(f"Classes: {len(analysis_data['classes'])}")


@app.command("init")
def init_project_config(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
) -> None:
    """Create a starter .docgenie.yaml configuration file."""
    config_path = Path(".docgenie.yaml")
    if config_path.exists() and not force:
        typer.echo("Config already exists. Use --force to overwrite.")
        raise typer.Exit(code=1)

    template = """# DocGenie configuration
ignore_patterns:
  - "*.log"
  - "build/"
  - "dist/"

template_customizations:
  include_api_docs: true
  include_directory_tree: true
  max_functions_documented: 25
"""
    config_path.write_text(template, encoding="utf-8")
    console.log(f"[green]Created {config_path}[/green]")


@app.command("html")
def html_command(  # noqa: PLR0913
    input_path: Path = typer.Argument(..., exists=True, resolve_path=True),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output HTML path"),
    source: str = typer.Option("readme", "--source", "-s", help="readme or codebase"),
    title: str | None = typer.Option(None, "--title", "-t", help="Custom HTML title"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    open_browser: bool = typer.Option(
        False,
        "--open-browser",
        "--open",
        help="Open generated HTML in browser",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    tree_sitter: bool = typer.Option(True, "--tree-sitter/--no-tree-sitter"),
) -> None:
    """Convert README to HTML or generate HTML from codebase analysis."""
    html_generator = HTMLGenerator()
    output_path = output
    if not output_path:
        output_path = (input_path.parent if source == "readme" else input_path) / "docs.html"
    elif output_path.is_dir():
        output_path = output_path / "docs.html"

    if (
        output_path.exists()
        and (not force)
        and (not typer.confirm(f"{output_path} exists. Overwrite?"))
    ):
        raise typer.Exit(code=1)

    if source == "readme":
        if not input_path.is_file() or input_path.suffix.lower() != ".md":
            typer.echo("Input must be a markdown file when --source readme")
            raise typer.Exit(code=1)
        readme_content = input_path.read_text(encoding="utf-8")
        project_name = title or _extract_title(readme_content) or input_path.stem
        html_generator.generate_from_readme(readme_content, str(output_path), project_name)
    else:
        analyzer = CodebaseAnalyzer(str(input_path), enable_tree_sitter=tree_sitter)
        if verbose:
            console.log(f"Analyzing codebase at {input_path}")
        analysis_data = analyzer.analyze()
        html_generator.generate_from_analysis(analysis_data, str(output_path))

    console.log(f"[green]HTML generated:[/green] {output_path}")
    if open_browser:
        webbrowser.open(output_path.resolve().as_uri())


def _extract_title(content: str) -> str | None:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


if __name__ == "__main__":
    app()
