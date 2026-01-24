"""
Utility functions for DocGenie.
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

# Default ignore patterns
DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "node_modules",
    "bower_components",
    ".venv",
    "venv",
    "env",
    ".env",
    "build",
    "dist",
    "target",
    "out",
    ".idea",
    ".vscode",
    "*.swp",
    "*.swo",
    "*.log",
    "*.tmp",
    "*.temp",
    ".DS_Store",
    "Thumbs.db",
    "*.min.js",
    "*.min.css",
    "coverage",
    ".coverage",
    ".nyc_output",
    ".pytest_cache",
    ".tox",
    "*.egg-info",
    ".eggs",
]

# File extension to language mapping
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".cs": "csharp",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".fish": "shell",
    ".r": "r",
    ".R": "r",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".txt": "text",
}


def get_file_language(file_path: Path) -> Optional[str]:
    """
    Determine the programming language of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Language name or None if not recognized
    """
    suffix = file_path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(suffix)


def should_ignore_file(file_path: str, additional_patterns: Optional[List[str]] = None) -> bool:
    """
    Check if a file or directory should be ignored based on ignore patterns.

    Args:
        file_path: Path to check
        additional_patterns: Additional patterns to check

    Returns:
        True if the file should be ignored
    """
    patterns = DEFAULT_IGNORE_PATTERNS.copy()
    if additional_patterns:
        patterns.extend(additional_patterns)

    file_path = str(file_path)

    # Check against all patterns
    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(
            os.path.basename(file_path), pattern
        ):
            return True

        # Check if any part of the path matches the pattern
        path_parts = file_path.split(os.sep)
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False


def extract_git_info(repo_path: Path) -> Dict[str, Any]:
    """
    Extract git repository information.

    Args:
        repo_path: Path to the repository

    Returns:
        Dictionary containing git information
    """
    git_info: Dict[str, Any] = {}
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return git_info

    # Remote URL / repo name
    try:
        origin = repo.remotes.origin
        remote_url = origin.url
        git_info["remote_url"] = remote_url
        git_info["repo_name"] = extract_repo_name_from_url(remote_url)
    except (AttributeError, IndexError, GitCommandError):
        pass

    # Current branch
    try:
        if not repo.head.is_detached:
            git_info["current_branch"] = repo.active_branch.name
    except (TypeError, GitCommandError):
        pass

    # Latest commit info
    try:
        commit = repo.head.commit
        git_info["latest_commit"] = {
            "hash": commit.hexsha,
            "author_name": commit.author.name,
            "author_email": commit.author.email,
            "date": str(commit.committed_datetime),
            "message": commit.message.strip(),
        }
    except (ValueError, GitCommandError, AttributeError):
        pass

    # Contributor count (best-effort)
    try:
        shortlog = repo.git.shortlog("-sn")
        contributors = [line for line in shortlog.split("\n") if line.strip()]
        git_info["contributor_count"] = len(contributors)
    except GitCommandError:
        pass

    return git_info


def extract_repo_name_from_url(url: str) -> str:
    """
    Extract repository name from git URL.

    Args:
        url: Git repository URL

    Returns:
        Repository name
    """
    # Handle different URL formats
    if url.startswith("git@"):
        # SSH format: git@github.com:user/repo.git
        match = re.search(r":([^/]+/[^/]+?)(?:\.git)?$", url)
    else:
        # HTTPS format: https://github.com/user/repo.git
        match = re.search(r"/([^/]+/[^/]+?)(?:\.git)?/?$", url)

    if match:
        return match.group(1)

    return url


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    i = 0
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def is_website_project(analysis_data: Dict[str, Any]) -> bool:
    """
    Detect if the project is a website/web application.

    Args:
        analysis_data: Analysis results

    Returns:
        True if website detected, False otherwise
    """
    files = analysis_data.get("project_structure", {}).get("root", {}).get("files", [])
    dependencies = analysis_data.get("dependencies", {})
    languages = analysis_data.get("languages", {})

    # Check for common website files
    website_files = ["index.html", "index.htm", "home.html", "main.html", "default.html"]
    has_html_entry = any(f in files for f in website_files)

    # Check for CSS files
    has_css = any(f.endswith(".css") for f in files)

    # Check for static website generators
    static_generators = [
        "_config.yml",
        "gatsby-config.js",
        "next.config.js",
        "nuxt.config.js",
        "hugo.toml",
        "hugo.yaml",
        "_config.toml",
        "mkdocs.yml",
        "docusaurus.config.js",
    ]
    has_static_generator = any(f in files for f in static_generators)

    # Check for web framework dependencies
    web_frameworks = [
        "react",
        "vue",
        "angular",
        "svelte",
        "gatsby",
        "next",
        "nuxt",
        "hugo",
        "jekyll",
        "express",
        "koa",
        "fastify",
        "django",
        "flask",
        "fastapi",
        "rails",
        "sinatra",
        "laravel",
        "symfony",
    ]
    has_web_framework = any(
        framework in str(deps).lower()
        for deps in dependencies.values()
        for framework in web_frameworks
    )

    # Check for typical website directory structure
    structure = analysis_data.get("project_structure", {})
    web_dirs = [
        "public",
        "static",
        "assets",
        "dist",
        "build",
        "www",
        "html",
        "css",
        "js",
        "images",
        "img",
    ]
    has_web_dirs = any(any(web_dir in path.lower() for web_dir in web_dirs) for path in structure)

    # Check for high HTML/CSS/JS content
    web_languages = (
        languages.get("html", 0) + languages.get("css", 0) + languages.get("javascript", 0)
    )
    total_files = sum(languages.values()) if languages else 1
    web_ratio = web_languages / total_files if total_files > 0 else 0

    # Website detection criteria
    return (
        has_html_entry
        or has_static_generator
        or has_web_framework
        or (has_css and web_ratio > 0.3)
        or (has_web_dirs and web_ratio > 0.2)
    )


def get_project_type(analysis_data: Dict[str, Any]) -> str:
    """
    Determine the type of project based on analysis data.

    Args:
        analysis_data: Analysis results

    Returns:
        Project type description
    """
    dependencies = analysis_data.get("dependencies", {})
    files = analysis_data.get("project_structure", {}).get("root", {}).get("files", [])

    # First check if it's a website
    if is_website_project(analysis_data):
        # Determine specific website type
        if "package.json" in files:
            if any("react" in str(deps).lower() for deps in dependencies.values()):
                return "React Website"
            if any("vue" in str(deps).lower() for deps in dependencies.values()):
                return "Vue.js Website"
            if any("angular" in str(deps).lower() for deps in dependencies.values()):
                return "Angular Website"
            if any("gatsby" in str(deps).lower() for deps in dependencies.values()):
                return "Gatsby Static Website"
            if any("next" in str(deps).lower() for deps in dependencies.values()):
                return "Next.js Website"
            return "JavaScript Website"
        if any(f in files for f in ["_config.yml", "hugo.toml", "hugo.yaml"]):
            return "Static Website (Hugo/Jekyll)"
        if any("django" in str(deps).lower() for deps in dependencies.values()):
            return "Django Website"
        if any("flask" in str(deps).lower() for deps in dependencies.values()):
            return "Flask Website"
        return "Website"

    # Check for specific project types
    if "package.json" in files:
        if any("react" in str(deps).lower() for deps in dependencies.values()):
            return "React Application"
        if any("vue" in str(deps).lower() for deps in dependencies.values()):
            return "Vue.js Application"
        if any("angular" in str(deps).lower() for deps in dependencies.values()):
            return "Angular Application"
        if any("express" in str(deps).lower() for deps in dependencies.values()):
            return "Node.js/Express Application"
        return "Node.js Application"

    if "requirements.txt" in files or "pyproject.toml" in files or "setup.py" in files:
        if any("django" in str(deps).lower() for deps in dependencies.values()):
            return "Django Application"
        if any("flask" in str(deps).lower() for deps in dependencies.values()):
            return "Flask Application"
        if any("fastapi" in str(deps).lower() for deps in dependencies.values()):
            return "FastAPI Application"
        return "Python Application"

    if "Cargo.toml" in files:
        return "Rust Application"

    if "go.mod" in files:
        return "Go Application"

    if "pom.xml" in files or "build.gradle" in files:
        return "Java Application"

    if "Gemfile" in files:
        return "Ruby Application"

    # Fallback to main language
    main_language = analysis_data.get("main_language", "unknown")
    if main_language != "unknown":
        return f"{main_language.title()} Project"

    return "Software Project"


def create_directory_tree(structure: Dict[str, Any], max_depth: int = 3) -> str:
    """
    Create a visual directory tree representation.

    Args:
        structure: Project structure dictionary
        max_depth: Maximum depth to display

    Returns:
        Directory tree as string
    """
    tree_lines = []

    def add_items(items: List[str], prefix: str, is_last: bool = True) -> None:
        for i, item in enumerate(items):
            is_item_last = i == len(items) - 1
            connector = "└── " if is_item_last else "├── "
            tree_lines.append(f"{prefix}{connector}{item}")

    # Add root files
    root_info = structure.get("root", {})
    if root_info.get("files"):
        add_items(root_info["files"][:10], "")  # Limit to first 10 files
        if len(root_info["files"]) > 10:
            tree_lines.append(f"... and {len(root_info['files']) - 10} more files")

    # Add directories (limited depth)
    dirs_added = 0
    for path, info in structure.items():
        if path == "root" or dirs_added >= 10:  # Limit directories shown
            continue

        depth = path.count(os.sep)
        if depth >= max_depth:
            continue

        indent = "│   " * depth
        tree_lines.append(f"{indent}├── {os.path.basename(path)}/")

        # Add some files from this directory
        files = info.get("files", [])[:5]  # Limit to 5 files per directory
        if files:
            for i, file in enumerate(files):
                is_last = i == len(files) - 1 and not info.get("dirs")
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{indent}│   {connector}{file}")

        dirs_added += 1

    return "\n".join(tree_lines) if tree_lines else "No files found"
