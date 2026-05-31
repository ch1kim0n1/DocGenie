"""HTML documentation generator for DocGenie."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import markdown

from .generator import ReadmeGenerator
from .html_sections import (
    build_impact_graph_data,
    impact_graph_block,
    normalize_heading_ids,
)
from .redaction import redact_text
from .sanitize import sanitize_html, sanitize_markdown_html


class HTMLGenerator:
    """Generate minimal, professional HTML docs from README or analysis data."""

    def __init__(self) -> None:
        self.markdown_processor = markdown.Markdown(
            extensions=["codehilite", "toc", "tables", "fenced_code", "attr_list"],
            extension_configs={
                "codehilite": {"css_class": "highlight", "linenums": False},
                "toc": {"permalink": True, "baselevel": 1},
            },
        )

    def generate_from_readme(  # noqa: PLR0913
        self,
        readme_content: str,
        output_path: str | None = None,
        project_name: str = "Project Documentation",
        redaction_mode: str = "strict",
        redact_patterns: list[str] | None = None,
        graph_data: dict[str, Any] | None = None,
    ) -> str:
        safe_readme = redact_text(readme_content, redaction_mode, redact_patterns or [])
        # Reset converter state so `toc` reflects only this document.
        self.markdown_processor.reset()
        raw_content = self.markdown_processor.convert(safe_readme)
        toc_html = getattr(self.markdown_processor, "toc", "")
        # Normalize heading IDs (and matching TOC anchors) before sanitizing.
        raw_content, toc_html = normalize_heading_ids(raw_content, toc_html)
        # SECURITY: sanitize the converted body to strip executable content
        # (<script>, event handlers, javascript:/data: URLs) that may originate
        # from analyzed source (docstrings, identifiers, dependency names).
        content = sanitize_markdown_html(raw_content)
        safe_toc = sanitize_markdown_html(toc_html)
        full_html = self._create_html_document(
            content, project_name, graph_data=graph_data, toc_html=safe_toc
        )
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_html)
        return full_html

    def generate_from_analysis(
        self, analysis_data: dict[str, Any], output_path: str | None = None
    ) -> str:
        readme_gen = ReadmeGenerator()
        readme_content = readme_gen.generate(analysis_data)
        config = analysis_data.get("config", {})
        safety = config.get("safety", {}) if isinstance(config, dict) else {}
        redaction_mode = str(safety.get("redaction_mode", "strict"))
        redact_patterns = safety.get("redact_patterns", []) if isinstance(safety, dict) else []
        if not isinstance(redact_patterns, list):
            redact_patterns = []

        project_name = self._extract_project_name(analysis_data)
        graph_data = build_impact_graph_data(analysis_data)
        return self.generate_from_readme(
            readme_content,
            output_path,
            project_name,
            redaction_mode=redaction_mode,
            redact_patterns=redact_patterns,
            graph_data=graph_data,
        )

    def _create_html_document(
        self,
        content: str,
        project_name: str,
        *,
        graph_data: dict[str, Any] | None = None,
        toc_html: str = "",
    ) -> str:
        safe_project_name = sanitize_html(project_name)
        generated_on = datetime.now().strftime("%B %d, %Y")
        impact_block = impact_graph_block(graph_data)

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{safe_project_name}</title>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap\" rel=\"stylesheet\">
  <!-- Offline fallback: system fonts used if Google Fonts unavailable -->
  <style>
  body {{ font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  code, pre {{ font-family: 'IBM Plex Mono', 'Consolas', 'Monaco', monospace; }}
  </style>
  <style>{self._get_css_styles()}</style>
</head>
<body>
  <a class=\"skip-link\" href=\"#main-content\">Skip to main content</a>
  <button type=\"button\" class=\"mobile-menu-btn\" aria-label=\"Toggle menu\"></button>
  <div class=\"layout\">
    <aside class=\"sidebar\" aria-label=\"Table of contents\">
      <div class=\"brand\">{safe_project_name}</div>
      <label class=\"sr-only\" for=\"toc-filter\">Filter sections</label>
      <input id=\"toc-filter\" class=\"toc-filter\" type=\"search\" placeholder=\"Filter sections\" autocomplete=\"off\" />
      <nav class=\"toc\">{toc_html}</nav>
    </aside>
    <main id=\"main-content\" class=\"content\">
      <header class=\"top\">
        <h1>{safe_project_name}</h1>
        <p>Generated by DocGenie on {generated_on}</p>
      </header>
      {impact_block}
      <article class=\"markdown-content\">{content}</article>
      <a href=\"#main-content\" class=\"back-to-top\" aria-label=\"Back to top\">Back to top</a>
    </main>
  </div>
  <script>{self._get_javascript()}</script>
</body>
</html>"""

    def _get_css_styles(self) -> str:
        return """
:root {
  --primary-color: #1f4f78;
  --accent-color: #0f766e;
  --bg: #f7f8fa;
  --surface: #ffffff;
  --text: #111827;
  --muted: #4b5563;
  --border: #d1d5db;
  --mono-bg: #f3f4f6;
  --sidebar-width: 280px;
  --space-1: 8px;
  --space-2: 12px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 32px;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  color: var(--text);
  background: var(--bg);
  font-family: 'IBM Plex Sans', sans-serif;
  line-height: 1.6;
}
.layout { display: flex; min-height: 100vh; }
.sidebar {
  width: var(--sidebar-width);
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: var(--space-4) var(--space-3);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
}
.brand { font-weight: 700; margin-bottom: var(--space-3); color: var(--primary-color); }
.toc-filter {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: var(--space-3);
}
.content {
  flex: 1;
  padding: var(--space-5);
  max-width: 900px;
  margin: 0 auto;
}
.top h1 { margin: 0 0 var(--space-1) 0; }
.top p { margin: 0 0 var(--space-4) 0; color: var(--muted); }
.impact-graph-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: var(--space-4);
  margin-bottom: var(--space-4);
}
.impact-graph-header h2 { margin: 0; font-size: 1.1rem; }
.impact-graph-hint {
  margin: var(--space-1) 0 var(--space-3) 0;
  color: var(--muted);
  font-size: 0.9rem;
}
#impact-graph {
  width: 100%;
  height: 260px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #f9fafb;
}
.impact-graph-legend {
  margin-top: var(--space-2);
  color: var(--muted);
  font-size: 0.86rem;
}
.markdown-content {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: var(--space-5);
}
.markdown-content code {
  font-family: 'IBM Plex Mono', monospace;
  background: var(--mono-bg);
  padding: 2px 5px;
  border-radius: 6px;
}
.markdown-content pre {
  background: #111827;
  color: #f9fafb;
  padding: var(--space-3);
  border-radius: 10px;
  overflow-x: auto;
}
.markdown-content a { color: var(--primary-color); }
.skip-link {
  position: absolute;
  left: 0;
  top: -100px;
  background: var(--primary-color);
  color: #fff;
  padding: var(--space-2) var(--space-3);
}
.skip-link:focus { top: 0; }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  border: 0;
}
@media (max-width: 960px) {
  .layout { display: block; }
  .sidebar {
    position: static;
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  .content { padding: var(--space-3); }
  .markdown-content { padding: var(--space-4); }
  #impact-graph { height: 220px; }
}
"""

    def _get_javascript(self) -> str:
        return """
// Smooth scrolling for hash links.
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', (e) => {
    const id = anchor.getAttribute('href');
    if (!id || id === '#') return;
    const target = document.querySelector(id);
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// TOC filter: filter table-of-contents by search term
const filter = document.getElementById('toc-filter');
if (filter) {
  filter.addEventListener('input', (event) => {
    const term = String(event.target.value || '').toLowerCase();
    document.querySelectorAll('.toc li').forEach((item) => {
      const text = String(item.textContent || '').toLowerCase();
      item.style.display = text.includes(term) ? '' : 'none';
    });
  });
}

const impactDataTag = document.getElementById('impact-graph-data');
if (impactDataTag) {
  let payload = { nodes: [], edges: [] };
  try {
    payload = JSON.parse(impactDataTag.textContent || '{}');
  } catch (_err) {}
  const svg = document.getElementById('impact-graph');
  if (svg) {
    renderImpactGraph(svg, payload);
  }
}

function renderImpactGraph(svg, payload) {
  const nodes = Array.isArray(payload.nodes) ? payload.nodes.slice(0, 80) : [];
  const edges = Array.isArray(payload.edges) ? payload.edges.slice(0, 160) : [];
  if (!nodes.length) {
    svg.innerHTML = '<text x="20" y="40" fill="#6b7280" font-size="14">No impact graph data available</text>';
    return;
  }

  const width = svg.clientWidth || 760;
  const height = svg.clientHeight || 260;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.36;

  const positions = new Map();
  nodes.forEach((node, idx) => {
    const angle = (2 * Math.PI * idx) / nodes.length;
    positions.set(node.id, {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      type: node.type,
      label: node.label,
    });
  });

  const colorByType = { file: '#1f4f78', module: '#0f766e', output: '#b45309' };
  const edgeSvg = edges
    .map((edge) => {
      const s = positions.get(edge.source);
      const t = positions.get(edge.target);
      if (!s || !t) return '';
      return '<line x1="' + s.x + '" y1="' + s.y + '" x2="' + t.x + '" y2="' + t.y + '" stroke="#cbd5e1" stroke-width="1" />';
    })
    .join('');

  const nodeSvg = nodes
    .map((node) => {
      const p = positions.get(node.id);
      if (!p) return '';
      const fill = colorByType[node.type] || '#334155';
      const safeLabel = String(p.label || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
      return '<g><circle cx="' + p.x + '" cy="' + p.y + '" r="5" fill="' + fill + '"></circle><title>' + safeLabel + '</title></g>';
    })
    .join('');

  svg.innerHTML = edgeSvg + nodeSvg;
}
"""

    def _extract_project_name(self, analysis_data: dict[str, Any]) -> str:
        project_name = analysis_data.get("project_name")
        if isinstance(project_name, str) and project_name.strip():
            return project_name
        git_info = analysis_data.get("git_info", {})
        repo_name = git_info.get("repo_name") if isinstance(git_info, dict) else None
        if isinstance(repo_name, str) and repo_name.strip():
            return repo_name
        root_path = analysis_data.get("root_path")
        if isinstance(root_path, str) and root_path.strip():
            return Path(root_path).name
        return "Project Documentation"
