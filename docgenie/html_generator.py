"""
HTML documentation generator for DocGenie.
Converts README content to beautiful HTML documentation.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import markdown
from markdown.extensions import codehilite, toc, tables, fenced_code
from .utils import is_website_project


class HTMLGenerator:
    """
    Generates beautiful HTML documentation from README content or analysis data.
    """
    
    def __init__(self):
        self.markdown_processor = markdown.Markdown(
            extensions=[
                'codehilite',
                'toc',
                'tables',
                'fenced_code',
                'attr_list',
                'def_list',
                'abbr',
                'footnotes'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False
                },
                'toc': {
                    'permalink': True,
                    'baselevel': 1
                }
            }
        )
    
    def generate_from_readme(self, readme_content: str, output_path: Optional[str] = None, 
                           project_name: str = "Project Documentation") -> str:
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
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"🌐 HTML documentation generated: {output_path}")
        
        return full_html
    
    def generate_from_analysis(self, analysis_data: Dict[str, Any], 
                             output_path: Optional[str] = None) -> str:
        """
        Generate HTML documentation directly from analysis data.
        
        Args:
            analysis_data: Results from CodebaseAnalyzer
            output_path: Optional path to save the HTML file
            
        Returns:
            Generated HTML content as string
        """
        # Generate enhanced detailed content instead of just README
        detailed_content = self._generate_detailed_documentation(analysis_data)
        project_name = self._extract_project_name(analysis_data)
        
        # Create full HTML document with enhanced content
        full_html = self._create_enhanced_html_document(detailed_content, project_name, analysis_data)
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"🌐 Enhanced HTML documentation generated: {output_path}")
        
        return full_html
    
    def _create_html_document(self, content: str, project_name: str) -> str:
        """Create a complete HTML document with styling."""
        
        # Extract table of contents if available
        toc_html = getattr(self.markdown_processor, 'toc', '')
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
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
                <h2><i class="fas fa-file-alt"></i> {project_name}</h2>
                <p class="sidebar-subtitle">Documentation</p>
            </div>
            <div class="toc">
                {toc_html}
            </div>
        </nav>
        
        <main class="content">
            <div class="content-header">
                <h1 class="main-title">{project_name}</h1>
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
                    <a href="https://github.com/your-repo/docgenie" target="_blank">DocGenie</a>
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
        
        return html_template
    
    # Helper methods for enhanced documentation generation
    def _analyze_project_type(self, analysis_data: Dict[str, Any]) -> str:
        """Analyze and determine the project type."""
        dependencies = analysis_data.get('dependencies', {})
        main_language = analysis_data.get('main_language', '').lower()
        
        # Check for web frameworks
        web_frameworks = ['react', 'vue', 'angular', 'express', 'django', 'flask', 'fastapi']
        for dep_file, deps in dependencies.items():
            if isinstance(deps, dict):
                all_deps = []
                for dep_list in deps.values():
                    if isinstance(dep_list, list):
                        all_deps.extend(dep_list)
            else:
                all_deps = deps if isinstance(deps, list) else []
            
            for framework in web_frameworks:
                if any(framework in str(dep).lower() for dep in all_deps):
                    return f"{framework.title()} Web Application"
        
        # Check by language
        language_types = {
            'python': "Python Application",
            'javascript': "Node.js Application", 
            'typescript': "TypeScript Application",
            'java': "Java Application",
            'go': "Go Service",
            'csharp': ".NET Application"
        }
        
        return language_types.get(main_language, "Software Application")
    
    def _assess_complexity_level(self, analysis_data: Dict[str, Any]) -> str:
        """Assess the complexity level of the project."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        languages = analysis_data.get('languages', {})
        
        complexity_score = 0
        complexity_score += min(len(languages) * 10, 30)
        complexity_score += min(len(functions), 30)
        complexity_score += min(len(classes) * 2, 40)
        
        if complexity_score < 30:
            return "basic"
        elif complexity_score < 60:
            return "intermediate"
        elif complexity_score < 90:
            return "advanced"
        else:
            return "expert"
    
    def _explain_language_purpose(self, language: str, analysis_data: Dict[str, Any]) -> str:
        """Explain the purpose of each language in the project."""
        purposes = {
            'python': "Core application logic and data processing",
            'javascript': "Frontend interactivity and user interface",
            'typescript': "Type-safe frontend development",
            'java': "Enterprise backend services and business logic",
            'go': "High-performance backend services",
            'csharp': ".NET framework applications"
        }
        return purposes.get(language.lower(), f"{language.title()} development")
    
    def _has_good_documentation(self, analysis_data: Dict[str, Any]) -> bool:
        """Check if project has good documentation."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        documented = sum(1 for f in functions if f.get('docstring')) + sum(1 for c in classes if c.get('docstring'))
        total = len(functions) + len(classes)
        
        return (documented / total) > 0.3 if total > 0 else False
    
    def _identify_architectural_patterns(self, analysis_data: Dict[str, Any]) -> list:
        """Identify architectural patterns."""
        patterns = []
        classes = analysis_data.get('classes', [])
        
        class_names = [cls.get('name', '').lower() for cls in classes]
        
        if any('service' in name for name in class_names):
            patterns.append({'name': 'Service Layer Pattern', 'description': 'Business logic in service classes'})
        
        if any('manager' in name for name in class_names):
            patterns.append({'name': 'Manager Pattern', 'description': 'Complex operations coordinated by managers'})
        
        if not patterns and len(classes) > 3:
            patterns.append({'name': 'Object-Oriented Design', 'description': 'Code organized with classes and objects'})
        
        return patterns
    
    def _assess_architectural_complexity(self, analysis_data: Dict[str, Any]) -> str:
        """Assess architectural complexity."""
        classes = analysis_data.get('classes', [])
        imports = analysis_data.get('imports', {})
        total_imports = sum(len(deps) for deps in imports.values())
        
        if len(classes) > 15 and total_imports > 20:
            return "High - Complex multi-layered architecture"
        elif len(classes) > 8 and total_imports > 10:
            return "Medium - Well-structured modular design"
        else:
            return "Low - Simple structure"
    
    def _analyze_file_structure(self, analysis_data: Dict[str, Any]) -> list:
        """Analyze file structure."""
        languages = analysis_data.get('languages', {})
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        file_analysis = []
        for lang, count in languages.items():
            file_analysis.append({
                'name': f"{lang.title()} Files",
                'purpose': self._explain_language_purpose(lang, analysis_data),
                'functions': len(functions) // len(languages) if languages else 0,
                'classes': len(classes) // len(languages) if languages else 0,
                'importance': "high" if count > 2 else "medium"
            })
        
        return file_analysis
    
    def _get_detailed_file_analysis(self, analysis_data: Dict[str, Any]) -> list:
        """Get detailed file analysis."""
        languages = analysis_data.get('languages', {})
        file_details = []
        
        for lang, count in languages.items():
            file_details.append({
                'name': f"{lang.title()} Files ({count} files)",
                'purpose': self._explain_language_purpose(lang, analysis_data),
                'complexity': "High" if count > 3 else "Medium" if count > 1 else "Low",
                'components': ['Functions', 'Classes', 'Imports'],
                'system_role': f"{lang.title()} implementation",
                'dependencies': f"{count} files with standard dependencies",
                'features': f"Standard {lang} features and patterns"
            })
        
        return file_details
    
    def _is_complex_function(self, function: dict) -> bool:
        """Check if function is complex."""
        args = function.get('args', [])
        name = function.get('name', '')
        docstring = function.get('docstring', '')
        
        return (len(args) > 4 or 
                'async' in name.lower() or 
                (docstring and len(docstring) > 100) or
                any(kw in name.lower() for kw in ['process', 'analyze', 'calculate']))
    
    def _generate_detailed_function_docs(self, function: dict, analysis_data: Dict[str, Any]) -> str:
        """Generate detailed function docs."""
        name = function.get('name', 'Unknown')
        args = function.get('args', [])
        docstring = function.get('docstring', '')
        line = function.get('line', 0)
        
        return f"""
#### `{name}()` - Complex Function

**Location**: Line {line}
**Arguments**: {len(args)} parameters
**Purpose**: {docstring if docstring else 'Complex function implementation'}

---
"""
    
    def _generate_detailed_class_docs(self, cls: dict, analysis_data: Dict[str, Any]) -> str:
        """Generate detailed class docs."""
        name = cls.get('name', 'Unknown')
        methods = cls.get('methods', [])
        docstring = cls.get('docstring', '')
        line = cls.get('line', 0)
        
        return f"""
#### `{name}` Class

**Location**: Line {line}
**Methods**: {len(methods)} methods
**Purpose**: {docstring if docstring else 'Class implementation'}

---
"""
    
    def _generate_standard_function_docs(self, function: dict) -> str:
        """Generate standard function docs."""
        name = function.get('name', 'Unknown')
        args = function.get('args', [])
        line = function.get('line', 0)
        
        return f"""#### `{name}({', '.join(args)})`
Line {line} - {self._infer_function_purpose(name)}
---
"""
    
    def _infer_function_purpose(self, name: str) -> str:
        """Infer function purpose from name."""
        name_lower = name.lower()
        if name_lower.startswith('get'):
            return "Retrieves data"
        elif name_lower.startswith('set'):
            return "Sets values"
        elif name_lower.startswith('create'):
            return "Creates objects"
        elif name_lower.startswith('process'):
            return "Processes data"
        else:
            return "Implements functionality"
    
    def _calculate_total_complexity_score(self, analysis_data: Dict[str, Any]) -> int:
        """Calculate total complexity score."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        languages = analysis_data.get('languages', {})
        
        score = min(len(functions) + len(classes) * 2 + len(languages) * 5, 100)
        return score
    
    def _calculate_average_arguments(self, functions: list) -> float:
        """Calculate average arguments per function."""
        if not functions:
            return 0.0
        
        total_args = sum(len(func.get('args', [])) for func in functions)
        return total_args / len(functions)
    
    def _calculate_maintainability_index(self, analysis_data: Dict[str, Any]) -> str:
        """Calculate maintainability index."""
        complexity = self._calculate_total_complexity_score(analysis_data)
        
        if complexity < 30:
            return "High - Easy to maintain"
        elif complexity < 60:
            return "Medium - Moderate maintenance effort"
        else:
            return "Low - Requires significant maintenance effort"
    
    def _analyze_complexity_by_file(self, analysis_data: Dict[str, Any]) -> list:
        """Analyze complexity by file."""
        languages = analysis_data.get('languages', {})
        complexity_analysis = []
        
        for lang, count in languages.items():
            score = min(count * 2, 10)
            explanation = f"{lang.title()} files with {'high' if score > 7 else 'medium' if score > 4 else 'low'} complexity"
            
            complexity_analysis.append({
                'file': f"{lang.title()} files",
                'score': score,
                'explanation': explanation
            })
        
        return complexity_analysis
    
    def _generate_complexity_recommendations(self, analysis_data: Dict[str, Any]) -> list:
        """Generate complexity recommendations."""
        recommendations = []
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        complex_functions = sum(1 for f in functions if self._is_complex_function(f))
        
        if complex_functions > len(functions) * 0.3:
            recommendations.append("Consider refactoring complex functions into smaller, more focused functions")
        
        if len(classes) > 20:
            recommendations.append("Large number of classes detected - consider organizing into packages or modules")
        
        if not recommendations:
            recommendations.append("Code complexity is well-managed - continue following current patterns")
        
        return recommendations
    
    def _explain_dependency_purpose(self, dependency: str) -> str:
        """Explain dependency purpose."""
        dep_lower = str(dependency).lower()
        
        purposes = {
            'express': "Web application framework",
            'react': "Frontend UI library",
            'vue': "Progressive web framework",
            'django': "Python web framework",
            'flask': "Lightweight web framework",
            'requests': "HTTP library",
            'numpy': "Numerical computing",
            'pandas': "Data analysis"
        }
        
        for key, purpose in purposes.items():
            if key in dep_lower:
                return purpose
        
        return "External library dependency"
    
    def _generate_code_examples(self, analysis_data: Dict[str, Any]) -> list:
        """Generate code examples."""
        main_language = analysis_data.get('main_language', '').lower()
        functions = analysis_data.get('functions', [])
        
        examples = []
        
        if main_language == 'python' and functions:
            examples.append({
                'title': 'Basic Usage',
                'description': 'Example of how to use the main functionality',
                'language': 'python',
                'code': f'# Import and use main functions\nfrom main import {functions[0].get("name", "main_function")}\n\nresult = {functions[0].get("name", "main_function")}()',
                'explanation': 'This demonstrates the basic usage pattern for the application'
            })
        
        if main_language in ['javascript', 'typescript']:
            examples.append({
                'title': 'Basic Usage',
                'description': 'Example JavaScript/TypeScript usage',
                'language': 'javascript',
                'code': '// Import and initialize\nconst app = require("./main");\n\n// Use the functionality\napp.start();',
                'explanation': 'Basic initialization and usage pattern'
            })
        
        return examples
    
    def _generate_enhanced_navigation(self, analysis_data: Dict[str, Any], toc_html: str) -> str:
        """Generate enhanced navigation."""
        return toc_html  # Use the generated TOC
    
    def _generate_statistics_sidebar(self, analysis_data: Dict[str, Any]) -> str:
        """Generate statistics sidebar."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        languages = analysis_data.get('languages', {})
        
        return f"""
            <div class="stats-sidebar">
                <h3><i class="fas fa-chart-bar"></i> Project Stats</h3>
                <div class="stat-item">
                    <span class="stat-number">{len(functions)}</span>
                    <span class="stat-label">Functions</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(classes)}</span>
                    <span class="stat-label">Classes</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(languages)}</span>
                    <span class="stat-label">Languages</span>
                </div>
            </div>
        """
    
    def _generate_project_badges(self, analysis_data: Dict[str, Any]) -> str:
        """Generate project badges."""
        main_language = analysis_data.get('main_language', 'Unknown')
        complexity = self._assess_complexity_level(analysis_data)
        
        return f"""
            <span class="badge badge-language">{main_language}</span>
            <span class="badge badge-complexity badge-{complexity}">{complexity.title()}</span>
        """
    
    def _get_enhanced_css_styles(self) -> str:
        """Get enhanced CSS styles."""
        base_styles = self._get_css_styles()
        
        enhanced_styles = """
        .stats-sidebar {
            padding: 1rem;
            background: var(--code-background);
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .stats-sidebar h3 {
            margin-bottom: 1rem;
            color: var(--primary-color);
            font-size: 1rem;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .stat-number {
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .project-badges {
            margin-bottom: 1rem;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }
        
        .badge-language {
            background-color: var(--primary-color);
            color: white;
        }
        
        .badge-complexity {
            color: white;
        }
        
        .badge-basic { background-color: #10b981; }
        .badge-intermediate { background-color: #f59e0b; }
        .badge-advanced { background-color: #ef4444; }
        .badge-expert { background-color: #7c3aed; }
        
        .analysis-summary {
            font-size: 0.75rem;
            opacity: 0.8;
        }
        """
        
        return base_styles + enhanced_styles
    
    def _get_enhanced_javascript(self) -> str:
        """Get enhanced JavaScript."""
        base_js = self._get_javascript()
        
        enhanced_js = """
        // Enhanced functionality
        document.addEventListener('DOMContentLoaded', function() {
            // Add copy buttons to code blocks
            document.querySelectorAll('pre code').forEach(function(codeBlock) {
                const button = document.createElement('button');
                button.className = 'copy-btn';
                button.textContent = 'Copy';
                button.onclick = function() {
                    navigator.clipboard.writeText(codeBlock.textContent);
                    button.textContent = 'Copied!';
                    setTimeout(() => button.textContent = 'Copy', 2000);
                };
                codeBlock.parentNode.appendChild(button);
            });
        });
        """
        
        return base_js + enhanced_js
    
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
    
    def _extract_project_name(self, analysis_data: Dict[str, Any]) -> str:
        """Extract project name from analysis data."""
        # Try to get project name from various sources
        if 'git_info' in analysis_data and analysis_data['git_info'].get('repo_name'):
            return analysis_data['git_info']['repo_name']
        
        if 'root_path' in analysis_data:
            return Path(analysis_data['root_path']).name
        
        return "Project Documentation"
    
    def _generate_detailed_documentation(self, analysis_data: Dict[str, Any]) -> str:
        """Generate comprehensive detailed documentation from analysis data."""
        sections = []
        
        # Project Overview Section
        sections.append(self._generate_project_overview(analysis_data))
        
        # Architecture Overview Section
        sections.append(self._generate_architecture_overview(analysis_data))
        
        # File-by-File Analysis Section
        sections.append(self._generate_file_analysis(analysis_data))
        
        # API Documentation Section
        sections.append(self._generate_api_documentation(analysis_data))
        
        # Complexity Analysis Section
        sections.append(self._generate_complexity_analysis(analysis_data))
        
        # Dependencies and Integration Section
        sections.append(self._generate_dependencies_section(analysis_data))
        
        # Usage Examples Section
        sections.append(self._generate_usage_examples(analysis_data))
        
        return '\n\n'.join(sections)
    
    def _generate_project_overview(self, analysis_data: Dict[str, Any]) -> str:
        """Generate comprehensive project overview section."""
        project_name = analysis_data.get('project_name', 'Unknown Project')
        main_language = analysis_data.get('main_language', 'Unknown')
        languages = analysis_data.get('languages', {})
        files_analyzed = analysis_data.get('files_analyzed', 0)
        
        # Determine project type and characteristics
        project_type = self._analyze_project_type(analysis_data)
        complexity_level = self._assess_complexity_level(analysis_data)
        
        overview = f"""# {project_name} - Comprehensive Documentation

## Project Overview

**{project_name}** is a {main_language.lower()} application that demonstrates {complexity_level} software architecture and design patterns. This project has been automatically analyzed to provide you with detailed insights into its structure, functionality, and implementation details.

### Project Characteristics

- **Primary Language**: {main_language}
- **Project Type**: {project_type}
- **Complexity Level**: {complexity_level}
- **Files Analyzed**: {files_analyzed} source files
- **Multi-language Support**: {'Yes' if len(languages) > 1 else 'No'} ({len(languages)} languages detected)

### Language Distribution Analysis

The codebase demonstrates a {"polyglot" if len(languages) > 2 else "focused"} approach to software development:

"""
        
        # Add detailed language analysis
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / files_analyzed) * 100 if files_analyzed > 0 else 0
            lang_purpose = self._explain_language_purpose(lang, analysis_data)
            overview += f"""
**{lang.title()}** ({count} files, {percentage:.1f}%)
: {lang_purpose}
"""
        
        overview += f"""
### Project Architecture Summary

This {main_language.lower()} project follows {"modern software engineering practices" if complexity_level in ["Advanced", "Expert"] else "standard development patterns"} and implements:

- **Modular Design**: Code is organized into logical modules and components
- **Separation of Concerns**: Different aspects of functionality are properly separated
- **Code Reusability**: Functions and classes are designed for reuse across the project
- **Documentation**: {"Comprehensive" if self._has_good_documentation(analysis_data) else "Basic"} code documentation practices

"""
        
        return overview
    
    def _generate_architecture_overview(self, analysis_data: Dict[str, Any]) -> str:
        """Generate detailed architecture overview."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        imports = analysis_data.get('imports', {})
        
        # Analyze architectural patterns
        patterns = self._identify_architectural_patterns(analysis_data)
        
        architecture = f"""## Architecture Deep Dive

### System Architecture

This project implements a {"multi-layered" if len(classes) > 5 else "simple"} architecture with the following characteristics:

#### Component Overview
- **Total Functions**: {len(functions)} (including methods)
- **Total Classes/Modules**: {len(classes)}
- **Import Dependencies**: {sum(len(deps) for deps in imports.values())} total imports
- **Architectural Complexity**: {self._assess_architectural_complexity(analysis_data)}

#### Identified Design Patterns

"""
        
        for pattern in patterns:
            architecture += f"- **{pattern['name']}**: {pattern['description']}\n"
        
        architecture += f"""
### Code Organization Strategy

The project follows a {"sophisticated" if len(classes) > 10 else "straightforward"} organizational approach:

#### Module Structure Analysis
"""
        
        # Group functions and classes by file/module
        file_analysis = self._analyze_file_structure(analysis_data)
        for file_info in file_analysis[:5]:  # Show top 5 most important files
            architecture += f"""
**{file_info['name']}**
: {file_info['purpose']} - Contains {file_info['functions']} functions and {file_info['classes']} classes. This module is {"critical" if file_info['importance'] == "high" else "supporting"} to the overall system architecture.
"""
        
        return architecture
    
    def _generate_file_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Generate detailed file-by-file analysis."""
        project_structure = analysis_data.get('project_structure', {})
        languages = analysis_data.get('languages', {})
        
        file_analysis = """## File-by-File Analysis

### Source Code Structure

Each file in this project serves a specific purpose in the overall system. Below is a detailed analysis of the most important files:

"""
        
        # Analyze each file type and its role
        file_details = self._get_detailed_file_analysis(analysis_data)
        
        for file_detail in file_details:
            file_analysis += f"""
#### {file_detail['name']}

**Purpose**: {file_detail['purpose']}

**Complexity Level**: {file_detail['complexity']}

**Key Components**:
"""
            for component in file_detail['components']:
                file_analysis += f"- {component}\n"
            
            file_analysis += f"""
**Role in System**: {file_detail['system_role']}

**Dependencies**: {file_detail['dependencies']}

**Notable Features**: {file_detail['features']}

---
"""
        
        return file_analysis
    
    def _generate_api_documentation(self, analysis_data: Dict[str, Any]) -> str:
        """Generate comprehensive API documentation."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        api_docs = """## API Documentation

### Functions and Methods Reference

This section provides detailed documentation for all functions and methods in the codebase, including complexity analysis and usage patterns.

"""
        
        # Group functions by complexity and importance
        complex_functions = []
        standard_functions = []
        
        for func in functions:
            if self._is_complex_function(func):
                complex_functions.append(func)
            else:
                standard_functions.append(func)
        
        # Document complex functions first with detailed explanations
        if complex_functions:
            api_docs += """### Complex Functions (Detailed Analysis)

These functions implement sophisticated logic and require detailed explanation:

"""
            for func in complex_functions[:10]:  # Limit to top 10 complex functions
                api_docs += self._generate_detailed_function_docs(func, analysis_data)
        
        # Document classes with their methods
        if classes:
            api_docs += """### Classes and Objects

"""
            for cls in classes[:10]:  # Limit to top 10 classes
                api_docs += self._generate_detailed_class_docs(cls, analysis_data)
        
        # Document remaining functions
        if standard_functions:
            api_docs += """### Standard Functions

"""
            for func in standard_functions[:20]:  # Limit to top 20 standard functions
                api_docs += self._generate_standard_function_docs(func)
        
        return api_docs
    
    def _generate_complexity_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Generate complexity analysis section."""
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        complexity_analysis = """## Complexity Analysis

### Code Complexity Metrics

This section analyzes the computational and cognitive complexity of the codebase to help understand maintenance requirements and potential optimization opportunities.

"""
        
        # Calculate various complexity metrics
        total_functions = len(functions)
        total_classes = len(classes)
        
        # Analyze function complexity
        complex_function_count = sum(1 for func in functions if self._is_complex_function(func))
        avg_args_per_function = self._calculate_average_arguments(functions)
        
        complexity_analysis += f"""### Overall Complexity Metrics

- **Total Complexity Score**: {self._calculate_total_complexity_score(analysis_data)}/100
- **Complex Functions**: {complex_function_count}/{total_functions} ({(complex_function_count/total_functions*100):.1f}% if total_functions > 0 else 0)
- **Average Arguments per Function**: {avg_args_per_function:.1f}
- **Maintainability Index**: {self._calculate_maintainability_index(analysis_data)}

### Complexity Distribution

"""
        
        # Analyze complexity by file/module
        complexity_by_file = self._analyze_complexity_by_file(analysis_data)
        for file_complexity in complexity_by_file[:5]:
            complexity_analysis += f"""
**{file_complexity['file']}**
: Complexity Score: {file_complexity['score']}/10 - {file_complexity['explanation']}
"""
        
        # Recommendations
        complexity_analysis += f"""
### Optimization Recommendations

Based on the complexity analysis, here are recommendations for improving code maintainability:

"""
        
        recommendations = self._generate_complexity_recommendations(analysis_data)
        for rec in recommendations:
            complexity_analysis += f"- {rec}\n"
        
        return complexity_analysis
    
    def _generate_dependencies_section(self, analysis_data: Dict[str, Any]) -> str:
        """Generate dependencies and integration analysis."""
        dependencies = analysis_data.get('dependencies', {})
        imports = analysis_data.get('imports', {})
        
        deps_section = """## Dependencies and Integration

### External Dependencies Analysis

This section analyzes the project's external dependencies and integration patterns.

"""
        
        if dependencies:
            deps_section += """### Package Dependencies

"""
            for dep_file, deps in dependencies.items():
                deps_section += f"""
#### {dep_file}

This configuration file manages {"critical" if len(deps) > 10 else "essential"} project dependencies:

"""
                if isinstance(deps, dict):
                    for category, dep_list in deps.items():
                        deps_section += f"""
**{category.title()}** ({len(dep_list)} packages):
"""
                        for dep in dep_list[:10]:  # Limit to first 10
                            purpose = self._explain_dependency_purpose(dep)
                            deps_section += f"- `{dep}`: {purpose}\n"
                else:
                    for dep in deps[:10]:  # Limit to first 10
                        purpose = self._explain_dependency_purpose(dep)
                        deps_section += f"- `{dep}`: {purpose}\n"
        
        # Analyze import patterns
        if imports:
            deps_section += """
### Import Pattern Analysis

The project demonstrates the following import patterns:

"""
            for lang, lang_imports in imports.items():
                if lang_imports:
                    deps_section += f"""
**{lang.title()} Imports** ({len(lang_imports)} modules):
: This indicates a {"well-structured" if len(lang_imports) > 5 else "focused"} approach to code organization in {lang}.
"""
        
        return deps_section
    
    def _generate_usage_examples(self, analysis_data: Dict[str, Any]) -> str:
        """Generate usage examples and patterns."""
        main_language = analysis_data.get('main_language', 'Unknown')
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        usage_examples = f"""## Usage Examples and Patterns

### Getting Started

Based on the analysis of this {main_language.lower()} project, here are common usage patterns and examples:

"""
        
        # Generate examples based on detected patterns
        examples = self._generate_code_examples(analysis_data)
        
        for example in examples:
            usage_examples += f"""
### {example['title']}

{example['description']}

```{example['language']}
{example['code']}
```

**Explanation**: {example['explanation']}

"""
        
        return usage_examples
    
    def _create_enhanced_html_document(self, content: str, project_name: str, analysis_data: Dict[str, Any]) -> str:
        """Create enhanced HTML document with detailed styling and navigation."""
        
        # Convert markdown content to HTML
        html_content = self.markdown_processor.convert(content)
        
        # Extract table of contents
        toc_html = getattr(self.markdown_processor, 'toc', '')
        
        # Generate enhanced navigation
        enhanced_nav = self._generate_enhanced_navigation(analysis_data, toc_html)
        
        # Generate project statistics sidebar
        stats_sidebar = self._generate_statistics_sidebar(analysis_data)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Comprehensive Documentation</title>
    <meta name="description" content="Detailed technical documentation for {project_name} with comprehensive API reference, complexity analysis, and architectural insights.">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        {self._get_enhanced_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h2><i class="fas fa-code-branch"></i> {project_name}</h2>
                <p class="sidebar-subtitle">Technical Documentation</p>
            </div>
            
            {stats_sidebar}
            
            <div class="toc">
                <h3><i class="fas fa-list"></i> Table of Contents</h3>
                {enhanced_nav}
            </div>
        </nav>
        
        <main class="content">
            <div class="content-header">
                <h1 class="main-title">{project_name}</h1>
                <div class="project-badges">
                    {self._generate_project_badges(analysis_data)}
                </div>
                <p class="generation-info">
                    <i class="fas fa-robot"></i> Comprehensive analysis generated by DocGenie on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                </p>
            </div>
            
            <div class="markdown-content">
                {html_content}
            </div>
            
            <footer class="content-footer">
                <div class="footer-content">
                    <p>
                        <i class="fas fa-magic"></i> 
                        Documentation automatically generated by 
                        <a href="https://github.com/your-repo/docgenie" target="_blank">DocGenie</a>
                    </p>
                    <p class="analysis-summary">
                        Analysis completed: {analysis_data.get('files_analyzed', 0)} files, 
                        {len(analysis_data.get('functions', []))} functions, 
                        {len(analysis_data.get('classes', []))} classes
                    </p>
                </div>
            </footer>
        </main>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script>
        {self._get_enhanced_javascript()}
    </script>
</body>
</html>"""
        
        return html_template
