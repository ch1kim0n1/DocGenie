"""
HTML documentation generator for DocGenie.
Converts README content to beautiful HTML documentation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import markdown

from .generator import ReadmeGenerator
from .logging import get_logger
from .sanitize import sanitize_html
from .utils import is_website_project


class HTMLGenerator:
    """
    Generates beautiful HTML documentation from README content or analysis data.
    """

    def __init__(self) -> None:
        self.markdown_processor = markdown.Markdown(
            extensions=[
                "codehilite",
                "toc",
                "tables",
                "fenced_code",
                "attr_list",
                "def_list",
                "abbr",
                "footnotes",
            ],
            extension_configs={
                "codehilite": {"css_class": "highlight", "linenums": False},
                "toc": {"permalink": True, "baselevel": 1},
            },
        )

    def generate_from_readme(
        self,
        readme_content: str,
        output_path: str | None = None,
        project_name: str = "Project Documentation",
    ) -> str:
        """
        Generate HTML documentation from README markdown content.

        Args:
            readme_content: Markdown content from README
            output_path: Optional path to save the HTML file
            project_name: Name of the project for the HTML title

        Returns:
            Generated HTML content as string
        """
        # Convert markdown to HTML
        html_content = self.markdown_processor.convert(readme_content)

        # Create full HTML document
        full_html = self._create_html_document(html_content, project_name)

        # Save to file if path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            get_logger(__name__).info("HTML documentation generated", output_path=output_path)

        return full_html

    def generate_from_analysis(
        self, analysis_data: dict[str, Any], output_path: str | None = None
    ) -> str:
        """
        Generate HTML documentation directly from analysis data.

        Args:
            analysis_data: Results from CodebaseAnalyzer
            output_path: Optional path to save the HTML file

        Returns:
            Generated HTML content as string
        """  # First generate README content, then convert to HTML
        readme_gen = ReadmeGenerator()
        readme_content = readme_gen.generate(analysis_data)

        project_name = self._extract_project_name(analysis_data)

        # Check if website and inform user
        if is_website_project(analysis_data):
            html_content = self.generate_from_readme(readme_content, output_path, project_name)
            if output_path:
                get_logger(__name__).info(
                    "Website detected; generated website-optimized HTML documentation",
                    output_path=output_path,
                )
            return html_content
        return self.generate_from_readme(readme_content, output_path, project_name)

    def _create_html_document(self, content: str, project_name: str) -> str:
        """Create a complete HTML document with styling."""

        # Sanitize project name to prevent XSS
        safe_project_name = sanitize_html(project_name)

        # Extract table of contents if available
        toc_html = getattr(self.markdown_processor, "toc", "")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_project_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h2><i class="fas fa-file-alt"></i> {safe_project_name}</h2>
                <p class="sidebar-subtitle">Documentation</p>
            </div>
            <div class="toc">
                {toc_html}
            </div>
        </nav>
        
        <main class="content">
            <div class="content-header">
                <h1 class="main-title">{safe_project_name}</h1>
                <p class="generation-info">
                    <i class="fas fa-robot"></i> Generated with DocGenie on {datetime.now().strftime("%B %d, %Y")}
                </p>
            </div>
            
            <div class="markdown-content">
                {content}
            </div>
            
            <footer class="content-footer">
                <p>
                    <i class="fas fa-magic"></i> 
                    Documentation automatically generated by 
                    <a href="https://github.com/ch1kim0n1/DocGenie" target="_blank">DocGenie</a>
                </p>
            </footer>
        </main>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""

    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML documentation."""
        return """
        :root {
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --accent-color: #0ea5e9;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --code-background: #f1f5f9;
            --sidebar-width: 280px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--background-color);
        }
        
        .container {
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: var(--sidebar-width);
            background: var(--card-background);
            border-right: 1px solid var(--border-color);
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 100;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
        }
        
        .sidebar-header {
            padding: 2rem 1.5rem 1rem;
            border-bottom: 1px solid var(--border-color);
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            color: white;
        }
        
        .sidebar-header h2 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .sidebar-subtitle {
            font-size: 0.875rem;
            opacity: 0.9;
        }
        
        .toc {
            padding: 1.5rem;
        }
        
        .toc ul {
            list-style: none;
            margin: 0;
            padding: 0;
        }
        
        .toc li {
            margin-bottom: 0.5rem;
        }
        
        .toc a {
            color: var(--text-secondary);
            text-decoration: none;
            padding: 0.5rem;
            border-radius: 0.375rem;
            display: block;
            transition: all 0.2s ease;
            font-size: 0.875rem;
        }
        
        .toc a:hover {
            background-color: var(--code-background);
            color: var(--primary-color);
        }
        
        .content {
            margin-left: var(--sidebar-width);
            flex: 1;
            padding: 2rem 3rem;
            max-width: calc(100vw - var(--sidebar-width));
        }
        
        .content-header {
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .generation-info {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .markdown-content {
            max-width: none;
        }
        
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3,
        .markdown-content h4,
        .markdown-content h5,
        .markdown-content h6 {
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            line-height: 1.25;
        }
        
        .markdown-content h1 {
            font-size: 2rem;
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
        }
        
        .markdown-content h2 {
            font-size: 1.5rem;
            color: var(--text-primary);
        }
        
        .markdown-content h3 {
            font-size: 1.25rem;
            color: var(--text-primary);
        }
        
        .markdown-content p {
            margin-bottom: 1rem;
        }
        
        .markdown-content ul,
        .markdown-content ol {
            margin-bottom: 1rem;
            padding-left: 2rem;
        }
        
        .markdown-content li {
            margin-bottom: 0.25rem;
        }
        
        .markdown-content pre {
            background-color: var(--code-background);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
            font-size: 0.875rem;
        }
        
        .markdown-content code {
            background-color: var(--code-background);
            color: var(--text-primary);
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-family: 'SF Mono', Monaco, 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
        }
        
        .markdown-content pre code {
            background: none;
            padding: 0;
            border-radius: 0;
        }
        
        .markdown-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            overflow: hidden;
        }
        
        .markdown-content th,
        .markdown-content td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        .markdown-content th {
            background-color: var(--code-background);
            font-weight: 600;
        }
        
        .markdown-content blockquote {
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin: 1rem 0;
            background-color: var(--code-background);
            padding: 1rem;
            border-radius: 0.375rem;
        }
        
        .markdown-content a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .markdown-content a:hover {
            text-decoration: underline;
        }
        
        .content-footer {
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .content-footer a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            
            .sidebar.active {
                transform: translateX(0);
            }
            
            .content {
                margin-left: 0;
                padding: 1rem 1.5rem;
                max-width: 100vw;
            }
            
            .main-title {
                font-size: 2rem;
            }
        }
        
        /* Emoji enhancement */
        .markdown-content h1:before,
        .markdown-content h2:before {
            margin-right: 0.5rem;
        }
        
        /* Code syntax highlighting improvements */
        .highlight {
            background: var(--code-background) !important;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        """

    def _get_javascript(self) -> str:
        """Get JavaScript for enhanced functionality."""
        return """
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Mobile menu toggle
        function toggleSidebar() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('active');
        }
        
        // Add mobile menu button if needed
        if (window.innerWidth <= 768) {
            const menuButton = document.createElement('button');
            menuButton.innerHTML = '<i class="fas fa-bars"></i>';
            menuButton.className = 'mobile-menu-btn';
            menuButton.onclick = toggleSidebar;
            document.body.appendChild(menuButton);
        }
        
        // Highlight current section in TOC
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.id;
                    if (id) {
                        // Remove active class from all TOC links
                        document.querySelectorAll('.toc a').forEach(link => {
                            link.classList.remove('active');
                        });
                        
                        // Add active class to current link
                        const currentLink = document.querySelector(`.toc a[href="#${id}"]`);
                        if (currentLink) {
                            currentLink.classList.add('active');
                        }
                    }
                }
            });
        }, { threshold: 0.1 });
        
        // Observe all headings
        document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
            observer.observe(heading);
        });
        """

    def _extract_project_name(self, analysis_data: dict[str, Any]) -> str:
        """Extract project name from analysis data."""
        # Try to get project name from various sources
        if "git_info" in analysis_data and analysis_data["git_info"].get("repo_name"):
            return analysis_data["git_info"]["repo_name"]

        if "root_path" in analysis_data:
            return Path(analysis_data["root_path"]).name

        return "Project Documentation"
