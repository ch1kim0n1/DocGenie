"""
Core codebase analysis functionality for DocGenie.
"""

import os
import re
import json
import yaml
import toml
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict, Counter
import ast
import subprocess

from .parsers import LanguageParser
from .utils import get_file_language, should_ignore_file, extract_git_info


class CodebaseAnalyzer:
    """
    Analyzes a codebase to extract comprehensive information for documentation generation.
    """
    
    def __init__(self, root_path: str, ignore_patterns: Optional[List[str]] = None):
        """
        Initialize the analyzer with a root path and optional ignore patterns.
        
        Args:
            root_path: Path to the root of the codebase
            ignore_patterns: Additional patterns to ignore beyond standard ones
        """
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = ignore_patterns or []
        self.parser = LanguageParser()
        
        # Analysis results
        self.files_analyzed = 0
        self.languages = Counter()
        self.dependencies = {}
        self.project_structure = {}
        self.functions = []
        self.classes = []
        self.imports = defaultdict(set)
        self.documentation_files = []
        self.config_files = []
        self.git_info = {}
        
    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of the codebase.
        
        Returns:
            Dictionary containing all analysis results
        """
        print(f"🔍 Analyzing codebase at: {self.root_path}")
        
        # Extract git information
        self.git_info = extract_git_info(self.root_path)
        
        # Walk through all files
        for root, dirs, files in os.walk(self.root_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not should_ignore_file(d, self.ignore_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                
                if should_ignore_file(str(file_path), self.ignore_patterns):
                    continue
                
                self._analyze_file(file_path)
        
        # Analyze project structure
        self._analyze_project_structure()
        
        # Detect dependencies
        self._detect_dependencies()
        
        print(f"✅ Analysis complete! Processed {self.files_analyzed} files")
        print(f"📊 Languages detected: {dict(self.languages.most_common())}")
        
        return self._compile_results()
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single file."""
        try:
            language = get_file_language(file_path)
            if not language:
                return
            
            self.files_analyzed += 1
            self.languages[language] += 1
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (UnicodeDecodeError, PermissionError):
                return
            
            # Parse based on file type
            if language in ['python', 'javascript', 'typescript', 'java', 'cpp', 'go', 'rust']:
                self._parse_source_file(file_path, content, language)
            elif file_path.name.lower() in ['readme.md', 'readme.rst', 'readme.txt', 'changelog.md', 'contributing.md']:
                self.documentation_files.append(str(file_path.relative_to(self.root_path)))
            elif file_path.suffix.lower() in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                self.config_files.append(str(file_path.relative_to(self.root_path)))
                
        except Exception as e:
            print(f"⚠️  Warning: Could not analyze {file_path}: {e}")
    
    def _parse_source_file(self, file_path: Path, content: str, language: str):
        """Parse a source code file to extract functions, classes, and imports."""
        try:
            parsed_data = self.parser.parse_file(content, language)
            
            # Store functions and classes with file context
            for func in parsed_data.get('functions', []):
                func['file'] = str(file_path.relative_to(self.root_path))
                func['language'] = language
                self.functions.append(func)
            
            for cls in parsed_data.get('classes', []):
                cls['file'] = str(file_path.relative_to(self.root_path))
                cls['language'] = language
                self.classes.append(cls)
            
            # Store imports
            for imp in parsed_data.get('imports', []):
                self.imports[language].add(imp)
                
        except Exception as e:
            print(f"⚠️  Warning: Could not parse {file_path}: {e}")
    
    def _analyze_project_structure(self):
        """Analyze the overall project structure."""
        structure = {}
        
        for root, dirs, files in os.walk(self.root_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if not should_ignore_file(d, self.ignore_patterns)]
            
            level = root.replace(str(self.root_path), '').count(os.sep)
            indent = ' ' * 2 * level
            rel_path = os.path.relpath(root, self.root_path)
            
            if rel_path == '.':
                structure['root'] = {
                    'files': [f for f in files if not should_ignore_file(f, self.ignore_patterns)],
                    'dirs': dirs
                }
            else:
                structure[rel_path] = {
                    'files': [f for f in files if not should_ignore_file(f, self.ignore_patterns)],
                    'dirs': dirs
                }
        
        self.project_structure = structure
    
    def _detect_dependencies(self):
        """Detect project dependencies from various package files."""
        dependency_files = {
            'requirements.txt': self._parse_requirements_txt,
            'pyproject.toml': self._parse_pyproject_toml,
            'setup.py': self._parse_setup_py,
            'package.json': self._parse_package_json,
            'Cargo.toml': self._parse_cargo_toml,
            'go.mod': self._parse_go_mod,
            'pom.xml': self._parse_pom_xml,
            'Gemfile': self._parse_gemfile,
        }
        
        for filename, parser in dependency_files.items():
            file_path = self.root_path / filename
            if file_path.exists():
                try:
                    deps = parser(file_path)
                    if deps:
                        self.dependencies[filename] = deps
                except Exception as e:
                    print(f"⚠️  Warning: Could not parse {filename}: {e}")
    
    def _parse_requirements_txt(self, file_path: Path) -> List[str]:
        """Parse requirements.txt file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        deps = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # Extract package name (before ==, >=, etc.)
                dep = re.split(r'[<>=!]', line)[0].strip()
                if dep:
                    deps.append(dep)
        return deps
    
    def _parse_package_json(self, file_path: Path) -> Dict[str, List[str]]:
        """Parse package.json file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        deps = {}
        if 'dependencies' in data:
            deps['dependencies'] = list(data['dependencies'].keys())
        if 'devDependencies' in data:
            deps['devDependencies'] = list(data['devDependencies'].keys())
        
        return deps
    
    def _parse_pyproject_toml(self, file_path: Path) -> Dict[str, Any]:
        """Parse pyproject.toml file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        deps = {}
        if 'tool' in data and 'poetry' in data['tool']:
            poetry = data['tool']['poetry']
            if 'dependencies' in poetry:
                deps['dependencies'] = list(poetry['dependencies'].keys())
            if 'dev-dependencies' in poetry:
                deps['dev-dependencies'] = list(poetry['dev-dependencies'].keys())
        
        return deps
    
    def _parse_setup_py(self, file_path: Path) -> List[str]:
        """Parse setup.py file to extract install_requires."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex to find install_requires
            install_requires_match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if install_requires_match:
                deps_str = install_requires_match.group(1)
                deps = re.findall(r'["\']([^"\'>=<]+)', deps_str)
                return deps
        except Exception:
            pass
        return []
    
    def _parse_cargo_toml(self, file_path: Path) -> Dict[str, List[str]]:
        """Parse Cargo.toml file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        deps = {}
        if 'dependencies' in data:
            deps['dependencies'] = list(data['dependencies'].keys())
        if 'dev-dependencies' in data:
            deps['dev-dependencies'] = list(data['dev-dependencies'].keys())
        
        return deps
    
    def _parse_go_mod(self, file_path: Path) -> List[str]:
        """Parse go.mod file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        deps = []
        in_require = False
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('require ('):
                in_require = True
                continue
            elif line == ')' and in_require:
                in_require = False
                continue
            elif in_require and line:
                dep = line.split()[0]
                deps.append(dep)
            elif line.startswith('require ') and not in_require:
                dep = line.split()[1]
                deps.append(dep)
        
        return deps
    
    def _parse_pom_xml(self, file_path: Path) -> List[str]:
        """Parse pom.xml file (basic parsing)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex to find artifactId in dependencies
            deps = re.findall(r'<artifactId>(.*?)</artifactId>', content)
            return deps
        except Exception:
            return []
    
    def _parse_gemfile(self, file_path: Path) -> List[str]:
        """Parse Gemfile."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        deps = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('gem '):
                # Extract gem name
                match = re.search(r'gem\s+["\']([^"\']+)', line)
                if match:
                    deps.append(match.group(1))
        
        return deps
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile all analysis results into a single dictionary."""
        return {
            'root_path': str(self.root_path),
            'files_analyzed': self.files_analyzed,
            'languages': dict(self.languages),
            'dependencies': self.dependencies,
            'project_structure': self.project_structure,
            'functions': self.functions,
            'classes': self.classes,
            'imports': {lang: list(imps) for lang, imps in self.imports.items()},
            'documentation_files': self.documentation_files,
            'config_files': self.config_files,
            'git_info': self.git_info,
            'main_language': self.languages.most_common(1)[0][0] if self.languages else 'unknown',
            'total_languages': len(self.languages),
        }