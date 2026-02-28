"""Command-line interface for DocGenie."""

from __future__ import annotations

import hashlib
import json
import webbrowser
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .config import load_config
from .core import CodebaseAnalyzer
from .diff_engine import compute_git_diff_summary
from .generator import ReadmeGenerator
from .html_generator import HTMLGenerator
from .index_store import IndexStore
from .logging import configure_logging, get_logger
from .pr_summary import render_pr_summary
from .readme_gate import evaluate_readme_readiness

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
    readiness = analysis_data.get("readme_readiness", {})
    if readiness:
        table.add_row("README readiness", f"{readiness.get('status')} ({readiness.get('score')}/100)")
    console.print(table)


def _validate_format(fmt: str) -> str:
    target_formats = fmt.lower()
    if target_formats not in {"markdown", "html", "both"}:
        typer.echo("Invalid format. Choose markdown, html, or both.")
        raise typer.Exit(code=1)
    return target_formats


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _run_analysis(
    path: Path,
    ignore: list[str],
    tree_sitter: bool,
    verbose: bool,
    config_overrides: dict[str, Any] | None = None,
) -> dict:
    config = load_config(path)
    if config_overrides:
        config = _deep_merge(config, config_overrides)
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


def _render_outputs(
    outputs: list[OutputSpec],
    analysis_data: dict,
    *,
    preview: bool,
    strict_readme: bool = False,
) -> None:
    quality_cfg = analysis_data.get("config", {}).get("quality", {})
    required_sections = quality_cfg.get("required_sections", []) if isinstance(quality_cfg, dict) else []
    min_confidence = str(quality_cfg.get("min_confidence", "medium")) if isinstance(quality_cfg, dict) else "medium"

    if not analysis_data.get("readme_readiness"):
        preview_readme = ReadmeGenerator().generate(analysis_data, None)
        analysis_data["readme_readiness"] = evaluate_readme_readiness(
            preview_readme,
            analysis_data=analysis_data,
            required_sections=required_sections if isinstance(required_sections, list) else None,
            min_confidence=min_confidence,
        )

    for output_format, output_path in outputs:
        if output_format == "markdown":
            generator = ReadmeGenerator()
            initial_content = generator.generate(analysis_data, None)
            readiness = evaluate_readme_readiness(
                initial_content,
                analysis_data=analysis_data,
                required_sections=required_sections if isinstance(required_sections, list) else None,
                min_confidence=min_confidence,
            )
            analysis_data["readme_readiness"] = readiness
            content = generator.generate(analysis_data, None if preview else str(output_path))
            if preview:
                console.rule("README Preview")
                typer.echo(content)
            else:
                console.log(f"[green]README generated:[/green] {output_path}")

            if readiness["status"] != "pass":
                console.log("[yellow]README readiness warning[/yellow]")
                for reason in readiness.get("reasons", []):
                    console.log(f"- {reason}")
                if strict_readme and readiness["status"] == "fail":
                    raise typer.Exit(code=1)
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
        "both",
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
    from_ref: str | None = typer.Option(None, "--from-ref", help="Git ref/tag/commit to diff from"),
    to_ref: str = typer.Option("HEAD", "--to-ref", help="Git ref/tag/commit to diff to"),
    include_diffs: bool = typer.Option(True, "--include-diffs/--no-diffs"),
    include_file_review: bool = typer.Option(True, "--include-file-review/--no-file-review"),
    include_output_links: bool = typer.Option(True, "--include-output-links/--no-output-links"),
    strict_readme: bool = typer.Option(False, "--strict-readme", help="Fail when readiness is low"),
    template_profile: str = typer.Option("pro", "--template-profile", help="legacy or pro"),
    json_logs: bool = typer.Option(False, "--json-logs", help="Output structured logs as JSON"),
) -> None:
    """Generate README and/or HTML docs for a codebase."""
    configure_logging(verbose=verbose, json_output=json_logs)
    logger = get_logger(__name__)

    target_formats = _validate_format(fmt)
    console.rule("[bold cyan]DocGenie")
    logger.info("Starting documentation generation", path=str(path), format=target_formats)

    config_overrides: dict[str, Any] = {
        "diff": {"enabled": include_diffs, "from_ref": from_ref, "to_ref": to_ref},
        "review": {"enabled": include_file_review},
        "output_links": {"enabled": include_output_links},
        "template_customizations": {"template_profile": template_profile},
    }

    analysis_data = _run_analysis(path, ignore, tree_sitter, verbose, config_overrides)
    outputs = _build_outputs(target_formats, output, path)
    _confirm_overwrite(outputs, preview=preview, force=force)
    _render_outputs(outputs, analysis_data, preview=preview, strict_readme=strict_readme)

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


@app.command("diff")
def diff_command(
    path: Path = typer.Argument(Path("."), exists=True, resolve_path=True),
    from_ref: str | None = typer.Option(None, "--from-ref"),
    to_ref: str = typer.Option("HEAD", "--to-ref"),
    fmt: str = typer.Option("text", "--format", "-f", help="text or json"),
    rename_detection: bool = typer.Option(True, "--rename-detection/--no-rename-detection"),
) -> None:
    """Show version-aware git diff metadata for documentation."""
    summary = compute_git_diff_summary(
        path,
        from_ref=from_ref,
        to_ref=to_ref,
        rename_detection=rename_detection,
    )
    if fmt == "json":
        typer.echo(json.dumps(summary, indent=2))
        return

    if not summary.get("available"):
        typer.echo(f"Diff unavailable: {summary.get('message')}")
        return

    typer.echo(f"Diff {summary.get('from_ref')} -> {summary.get('to_ref')}")
    totals = summary.get("totals", {})
    typer.echo(
        "Added: {added}, Modified: {modified}, Deleted: {deleted}, Renamed: {renamed}, Churn: {changes}".format(
            added=totals.get("added", 0),
            modified=totals.get("modified", 0),
            deleted=totals.get("deleted", 0),
            renamed=totals.get("renamed", 0),
            changes=totals.get("changes", 0),
        )
    )


@app.command("pr-summary")
def pr_summary_command(
    path: Path = typer.Argument(Path("."), exists=True, resolve_path=True),
    from_ref: str | None = typer.Option(None, "--from-ref"),
    to_ref: str = typer.Option("HEAD", "--to-ref"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    fmt: str = typer.Option("markdown", "--format", "-f", help="markdown or json"),
    max_files: int = typer.Option(10, "--max-files"),
    tree_sitter: bool = typer.Option(True, "--tree-sitter/--no-tree-sitter"),
) -> None:
    """Generate a PR-ready markdown summary from diff and review artifacts."""
    config_overrides: dict[str, Any] = {
        "diff": {"enabled": True, "from_ref": from_ref, "to_ref": to_ref},
        "review": {"enabled": True},
        "output_links": {"enabled": True},
    }
    analysis_data = _run_analysis(path, ignore=[], tree_sitter=tree_sitter, verbose=False, config_overrides=config_overrides)

    if not analysis_data.get("readme_readiness"):
        readme_content = ReadmeGenerator().generate(analysis_data, None)
        analysis_data["readme_readiness"] = evaluate_readme_readiness(
            readme_content,
            analysis_data=analysis_data,
        )

    if fmt.lower() == "json":
        payload = {
            "diff_summary": analysis_data.get("diff_summary", {}),
            "file_reviews": analysis_data.get("file_reviews", []),
            "output_links": analysis_data.get("output_links", []),
            "readme_readiness": analysis_data.get("readme_readiness", {}),
        }
        rendered = json.dumps(payload, indent=2)
    else:
        rendered = render_pr_summary(analysis_data, max_files=max_files)

    if output:
        output.write_text(rendered, encoding="utf-8")
        console.log(f"[green]PR summary generated:[/green] {output}")
    else:
        typer.echo(rendered)


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
  template_profile: pro
  include_trust_badges: true

diff:
  enabled: true
  from_ref: null
  to_ref: "HEAD"
  rename_detection: true

review:
  enabled: true
  risk_weights:
    churn: 0.35
    complexity: 0.35
    surface: 0.30
  max_files_per_folder: 50

output_links:
  enabled: true
  languages: ["python", "javascript", "typescript", "shell"]
  confidence_threshold: "low"

quality:
  readme_replacement_gate: "advisory"
  min_confidence: "medium"
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
