from __future__ import annotations

from docgenie.html_sections import (
    build_impact_graph_data,
    impact_graph_block,
    normalize_heading_ids,
)


def test_normalize_heading_ids_snapshot() -> None:
    content = (
        '<h2 id="toc_1"><a class="headerlink" href="#toc_1">¶</a>Installation</h2>'
        '<h2 id="toc_2"><a class="headerlink" href="#toc_2">¶</a>Installation</h2>'
    )
    toc = '<a href="#toc_1">Installation</a><a href="#toc_2">Installation</a>'
    normalized_content, normalized_toc = normalize_heading_ids(content, toc)
    assert 'id="installation"' in normalized_content
    assert 'id="installation-2"' in normalized_content
    assert 'href="#installation"' in normalized_toc
    assert 'href="#installation-2"' in normalized_toc


def test_build_impact_graph_data_snapshot() -> None:
    analysis_data = {
        "file_imports": {"src/a.py": ["os", "json"]},
        "output_links": [{"source_file": "src/a.py", "target_file": "dist/a.txt"}],
        "diff_summary": {"files": [{"path": "src/b.py"}]},
    }
    graph = build_impact_graph_data(analysis_data)
    assert graph["total_nodes"] == 5
    assert graph["total_edges"] == 3
    assert graph["truncated"] is False


def test_impact_graph_block_snapshot() -> None:
    graph_data = {"nodes": [{"id": "file:a", "label": "a", "type": "file"}], "edges": []}
    block = impact_graph_block(graph_data)
    assert "<section class=\"impact-graph-card\">" in block
    assert "1 nodes and 0 edges" in block
    assert "\"id\": \"file:a\"" in block
