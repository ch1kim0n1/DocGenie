"""PR summary renderer for DocGenie."""

from __future__ import annotations

from typing import Any


def render_pr_summary(analysis_data: dict[str, Any], *, max_files: int = 10) -> str:
    """Render a markdown PR summary from analysis artifacts."""
    diff_summary = analysis_data.get("diff_summary", {})
    totals = diff_summary.get("totals", {}) if isinstance(diff_summary, dict) else {}
    file_reviews = analysis_data.get("file_reviews", [])
    output_links = analysis_data.get("output_links", [])
    readiness = analysis_data.get("readme_readiness", {})

    high_risk = [item for item in file_reviews if item.get("risk_level") == "high"][:max_files]
    top_changed = sorted(
        diff_summary.get("files", []),
        key=lambda item: int(item.get("churn", 0)),
        reverse=True,
    )[:max_files]

    from_ref = diff_summary.get("from_ref", "n/a")
    to_ref = diff_summary.get("to_ref", "n/a")
    lines = [
        "## DocGenie PR Summary",
        "",
        f"- Diff range: `{from_ref}` -> `{to_ref}`",
        (
            "- File changes: "
            f"added={totals.get('added', 0)}, modified={totals.get('modified', 0)}, "
            f"deleted={totals.get('deleted', 0)}, renamed={totals.get('renamed', 0)}"
        ),
        f"- Total churn: {totals.get('changes', 0)} lines",
    ]

    if readiness:
        status = readiness.get("status", "unknown")
        score = readiness.get("score", 0)
        lines.append(f"- README readiness: **{status}** ({score}/100)")

    lines.extend(["", "### Highest-Churn Files", ""])
    if top_changed:
        for item in top_changed:
            p = item.get("path")
            ct = item.get("change_type")
            add = item.get("added_lines", 0)
            dele = item.get("deleted_lines", 0)
            lines.append(f"- `{p}` ({ct}) +{add}/-{dele}")
    else:
        lines.append("- No file-level churn data available.")

    lines.extend(["", "### High-Risk Files", ""])
    if high_risk:
        for item in high_risk:
            p = item.get("path")
            rl = item.get("risk_level")
            rs = item.get("risk_score")
            lines.append(f"- `{p}` risk={rl} score={rs}")
    else:
        lines.append("- No high-risk files detected.")

    lines.extend(["", "### Output Flow Notes", ""])
    if output_links:
        for item in output_links[:max_files]:
            target = item.get("target_file") or "unresolved"
            src = item.get("source_file")
            sl = item.get("source_line")
            conf = item.get("confidence")
            lines.append(f"- `{src}:{sl}` -> `{target}` ({conf})")
    else:
        lines.append("- No output links detected.")

    lines.extend(
        [
            "",
            "### Checklist",
            "",
            "- [ ] Review high-risk files",
            "- [ ] Validate unresolved output links",
            "- [ ] Confirm README readiness status",
        ]
    )

    return "\n".join(lines) + "\n"
