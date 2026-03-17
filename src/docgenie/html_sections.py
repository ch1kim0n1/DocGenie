"""Composable HTML section helpers for DocGenie output."""

from __future__ import annotations

import json
import re
from typing import Any


def impact_graph_block(graph_data: dict[str, Any] | None) -> str:
    payload_dict = graph_data or {
        "nodes": [],
        "edges": [],
        "total_nodes": 0,
        "total_edges": 0,
    }
    payload = json.dumps(payload_dict, sort_keys=True)
    total_nodes_default = len(payload_dict.get("nodes", [])) or 0
    total_nodes = int(payload_dict.get("total_nodes", total_nodes_default))
    total_edges_default = len(payload_dict.get("edges", [])) or 0
    total_edges = int(payload_dict.get("total_edges", total_edges_default))
    nodes_list = payload_dict.get("nodes", [])
    shown_nodes = (
        len(nodes_list) if isinstance(nodes_list, list) else 0
    )
    edges_list = payload_dict.get("edges", [])
    shown_edges = (
        len(edges_list) if isinstance(edges_list, list) else 0
    )
    truncated = bool(payload_dict.get("truncated", False))
    summary = (
        f"Showing {shown_nodes}/{total_nodes} nodes and {shown_edges}/{total_edges} edges"
        if truncated
        else f"{shown_nodes} nodes and {shown_edges} edges"
    )
    return (
        "<section class=\"impact-graph-card\">"
        "<div class=\"impact-graph-header\"><h2>Impact Graph</h2></div>"
        "<p class=\"impact-graph-hint\">Dependency and output-flow impact for changed files.</p>"
        "<div class=\"impact-graph-controls\">"
        "<button id=\"impact-reset\" type=\"button\" class=\"impact-btn\">Reset View</button>"
        "<button id=\"impact-layout\" type=\"button\" "
        "class=\"impact-btn\">Hierarchical view</button>"
        "</div>"
        "<svg id=\"impact-graph\" aria-label=\"Impact graph\"></svg>"
        "<div class=\"impact-graph-legend\">"
        f"Blue: files, Teal: modules, Amber: output targets. {summary}."
        "</div>"
        f"<script id=\"impact-graph-data\" type=\"application/json\">{payload}</script>"
        "</section>"
    )


def build_impact_graph_data(analysis_data: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, label: str, node_type: str) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label, "type": node_type}

    file_imports = analysis_data.get("file_imports", {})
    if isinstance(file_imports, dict):
        for path, imports in file_imports.items():
            file_id = f"file:{path}"
            add_node(file_id, str(path), "file")
            if isinstance(imports, list):
                for imported in imports[:8]:
                    module_id = f"module:{imported}"
                    add_node(module_id, str(imported), "module")
                    edges.append({"source": file_id, "target": module_id, "kind": "import"})

    for link in analysis_data.get("output_links", [])[:60]:
        source = str(link.get("source_file", ""))
        target = str(link.get("target_file") or "unresolved-output")
        if not source:
            continue
        src_id = f"file:{source}"
        tgt_id = f"output:{target}"
        add_node(src_id, source, "file")
        add_node(tgt_id, target, "output")
        edges.append({"source": src_id, "target": tgt_id, "kind": "output"})

    diff_summary = analysis_data.get("diff_summary", {})
    if isinstance(diff_summary, dict):
        for item in diff_summary.get("files", []):
            path = str(item.get("path", ""))
            if path:
                add_node(f"file:{path}", path, "file")

    all_nodes = list(nodes.values())
    all_edges = list(edges)
    max_nodes = 600
    max_edges = 1400
    render_nodes = all_nodes[:max_nodes]
    allowed_ids = {n.get("id", "") for n in render_nodes}
    render_edges = [
        e
        for e in all_edges
        if (
            str(e.get("source", "")) in allowed_ids
            and str(e.get("target", "")) in allowed_ids
        )
    ][:max_edges]
    truncated = (
        len(all_nodes) > len(render_nodes)
        or len(all_edges) > len(render_edges)
    )
    return {
        "nodes": render_nodes,
        "edges": render_edges,
        "total_nodes": len(all_nodes),
        "total_edges": len(all_edges),
        "truncated": truncated,
    }


def normalize_heading_ids(content: str, toc_html: str) -> tuple[str, str]:
    """Normalize heading IDs to avoid awkward suffixes like `_1`."""
    seen: dict[str, int] = {}
    id_map: dict[str, str] = {}

    def slugify(text: str) -> str:
        plain = re.sub(r"<[^>]+>", "", text)
        plain = plain.replace("¶", " ").strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
        return slug or "section"

    def replace_heading(match: re.Match[str]) -> str:
        level = match.group("level")
        old_id = match.group("id")
        body = match.group("body")
        base = slugify(body)
        count = seen.get(base, 0) + 1
        seen[base] = count
        new_id = base if count == 1 else f"{base}-{count}"
        id_map[old_id] = new_id
        body_with_link = re.sub(
            r'href="#[^"]+"',
            f'href="#{new_id}"',
            body,
            count=1,
        )
        return f'<h{level} id="{new_id}">{body_with_link}</h{level}>'

    heading_re = re.compile(
        r'<h(?P<level>[1-6])\s+id="(?P<id>[^"]+)">(?P<body>.*?)</h[1-6]>',
        re.DOTALL,
    )
    normalized_content = heading_re.sub(replace_heading, content)
    normalized_toc = toc_html
    for old_id, new_id in id_map.items():
        normalized_toc = normalized_toc.replace(f'href="#{old_id}"', f'href="#{new_id}"')
    return normalized_content, normalized_toc
