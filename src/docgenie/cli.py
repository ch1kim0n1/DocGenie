"""Command-line interface for DocGenie."""

from __future__ import annotations

import hashlib
import json
import webbrowser
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .config import load_config
from .core import CodebaseAnalyzer
from .generator import ReadmeGenerator
from .html_generator import HTMLGenerator
from .index_store import IndexStore
from .logging import configure_logging, get_logger

app = typer.Typer(add_completion=False, help="DocGenie - Auto-documentation for any codebase.")
index_app = typer.Typer(add_completion=False, help="Manage persistent DocGenie index store.")
app.add_typer(index_app, name="index")
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


def _run_analysis(
    path: Path,
    ignore: list[str],
    tree_sitter: bool,
    verbose: bool,
    config_overrides: dict | None = None,
) -> dict:
    config = load_config(path)
    if config_overrides:
        for key, value in config_overrides.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    # Merge CLI ignore patterns with config ignore patterns
    config_ignore = config.get("ignore_patterns", [])
    combined_ignore = list(set(ignore + config_ignore))

    analyzer = CodebaseAnalyzer(
        str(path),
        combined_ignore,
        enable_tree_sitter=tree_sitter,
        config=config,
    )
    with Progress(console=console, transient=True) as progress:
        task = progress.add_task("Analyzing codebase...", total=100)
        analysis_data = analyzer.analyze()
        progress.update(task, completed=100)
    if verbose:
        console.log("Analysis complete")
    return analysis_data


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _section_hashes(content: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for block in content.split("\n## "):
        if not block.strip():
            continue
        title = block.splitlines()[0].lstrip("# ").strip()
        hashes[title or "document"] = _content_hash(block)
    return hashes


def _record_artifact(path: Path, target: str, content: str, root: Path) -> None:
    try:
        store = IndexStore(root)
        run_id = store.latest_run_id()
        if run_id is not None:
            store.add_doc_artifact(
                run_id=run_id,
                artifact_path=str(path),
                target=target,
                content_hash=_content_hash(content),
                section_hashes=_section_hashes(content),
            )
            store.commit()
        store.close()
    except OSError:
        pass


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
    mode: str = typer.Option("auto", "--mode", help="Output mode: auto|single|package"),
    engine: str = typer.Option("hybrid", "--engine", help="Engine: hybrid|stateless"),
    incremental: bool = typer.Option(
        True,
        "--incremental/--no-incremental",
        help="Enable incremental analysis",
    ),
    max_file_size_kb: int = typer.Option(
        512, "--max-file-size-kb", help="Skip files larger than this size in KB"
    ),
    redaction_mode: str = typer.Option(
        "strict",
        "--redaction-mode",
        help="Redaction mode: strict|balanced|open",
    ),
    json_logs: bool = typer.Option(False, "--json-logs", help="Output structured logs as JSON"),
) -> None:
    """Generate README and/or HTML docs for a codebase."""
    configure_logging(verbose=verbose, json_output=json_logs)
    logger = get_logger(__name__)

    target_formats = _validate_format(fmt)
    console.rule("[bold cyan]DocGenie")
    logger.info("Starting documentation generation", path=str(path), format=target_formats)

    config_overrides = {
        "analysis": {
            "engine": "hybrid_index" if engine == "hybrid" else "stateless",
            "incremental": incremental,
            "max_file_size_kb": max_file_size_kb,
        },
        "monorepo": {"mode": mode},
        "safety": {"redaction_mode": redaction_mode},
    }
    analysis_data = _run_analysis(
        path, ignore, tree_sitter, verbose, config_overrides=config_overrides
    )
    outputs = _build_outputs(target_formats, output, path)
    _confirm_overwrite(outputs, preview=preview, force=force)
    monorepo_config = (
        analysis_data.get("config", {}).get("monorepo", {})
        if isinstance(analysis_data.get("config"), dict)
        else {}
    )
    package_mode = mode == "package" or (
        mode == "auto" and len(analysis_data.get("packages", [])) > 1
    )
    generate_root_doc = bool(monorepo_config.get("root_doc", True)) or not package_mode
    per_package_docs = bool(monorepo_config.get("per_package_docs", True))
    package_output_dir = Path(str(monorepo_config.get("package_output_dir", ".docgenie/packages")))

    for output_format, output_path in outputs:
        if output_format == "markdown":
            generator = ReadmeGenerator()
            if generate_root_doc:
                content = generator.generate(analysis_data, None if preview else str(output_path))
                if preview:
                    console.rule("README Preview")
                    typer.echo(content)
                else:
                    console.log(f"[green]README generated:[/green] {output_path}")
                    _record_artifact(output_path, "root", content, path)
            if package_mode and per_package_docs and not preview:
                pkg_artifacts = generator.generate_package_docs(
                    analysis_data, path / package_output_dir
                )
                for pkg_name, pkg_content in pkg_artifacts.items():
                    artifact_path = path / package_output_dir / pkg_name / "README.md"
                    _record_artifact(artifact_path, pkg_name, pkg_content, path)
        else:
            html_generator = HTMLGenerator()
            if generate_root_doc:
                content = html_generator.generate_from_analysis(
                    analysis_data, None if preview else str(output_path)
                )
                if preview:
                    console.rule("HTML Preview (truncated)")
                    typer.echo("\n".join(content.splitlines()[:80]))
                else:
                    console.log(f"[green]HTML generated:[/green] {output_path}")
                    _record_artifact(output_path, "root_html", content, path)

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
    metrics_json: Path | None = typer.Option(
        None, "--metrics-json", help="Optional path to write run metrics as JSON"
    ),
    engine: str = typer.Option("hybrid", "--engine", help="Engine: hybrid|stateless"),
    incremental: bool = typer.Option(True, "--incremental/--no-incremental"),
) -> None:
    """Analyze a codebase and print structured results."""
    analysis_data = _run_analysis(
        path,
        ignore=[],
        tree_sitter=tree_sitter,
        verbose=False,
        config_overrides={
            "analysis": {
                "engine": "hybrid_index" if engine == "hybrid" else "stateless",
                "incremental": incremental,
            }
        },
    )

    if metrics_json is not None:
        metrics_json.write_text(
            json.dumps(analysis_data.get("run_metrics", {}), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    if fmt == "json":
        typer.echo(json.dumps(analysis_data, indent=2))
    elif fmt == "yaml":
        typer.echo(yaml.dump(analysis_data, default_flow_style=False))
    else:
        typer.echo("Codebase Analysis Results")
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

analysis:
  use_gitignore: true
  exclude_generated: true
  include_hidden: false
  max_file_size_kb: 512
  generated_patterns: []
  engine: hybrid_index
  incremental: true
  parallelism: auto
  hard_file_cap: 300000
  full_rescan_interval_runs: 20

monorepo:
  mode: auto
  root_doc: true
  per_package_docs: true
  package_output_dir: ".docgenie/packages"

quality:
  confidence_enabled: true
  include_warnings: true
  min_confidence_for_api_docs: low

safety:
  redaction_mode: strict
  redact_patterns: []
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


@index_app.command("rebuild")
def index_rebuild(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False, resolve_path=True),
) -> None:
    """Rebuild persistent index for a repository."""
    store = IndexStore(path)
    store.clear_all()
    store.commit()
    store.close()
    typer.echo(f"Index rebuilt at {path / '.docgenie' / 'index.db'}")


@index_app.command("stats")
def index_stats(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False, resolve_path=True),
) -> None:
    """Print index statistics."""
    store = IndexStore(path)
    stats = store.stats()
    store.close()
    typer.echo(json.dumps(stats, indent=2, sort_keys=True))


@app.command("diff")
def diff_command(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False, resolve_path=True),
    since: str = typer.Option(..., "--since", help="Run ID or git ref"),
) -> None:
    """Show documentation impact since a prior indexed run/git ref."""
    store = IndexStore(path)
    latest = store.latest_run_id()
    if latest is None:
        typer.echo("No runs in index yet.")
        store.close()
        raise typer.Exit(code=1)

    # Git ref mode falls back to previous run for compatibility.
    base_id = int(since) if since.isdigit() else max(1, latest - 1)

    latest_artifacts = {a["artifact_path"]: a for a in store.list_artifacts_for_run(latest)}
    base_artifacts = {a["artifact_path"]: a for a in store.list_artifacts_for_run(base_id)}
    changed: list[str] = []
    for artifact_path, latest_art in latest_artifacts.items():
        base_art = base_artifacts.get(artifact_path)
        if not base_art or base_art.get("content_hash") != latest_art.get("content_hash"):
            changed.append(artifact_path)

    typer.echo(
        json.dumps(
            {
                "latest_run_id": latest,
                "base_run_id": base_id,
                "changed_artifacts": sorted(changed),
                "changed_count": len(changed),
            },
            indent=2,
            sort_keys=True,
        )
    )
    store.close()


if __name__ == "__main__":
    app()
