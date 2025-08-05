"""
Language-specific parsers for extracting code structure information.
"""

import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class LanguageParser:
    """
    Multi-language parser that extracts functions, classes, and imports from source code.
    """
    
    def __init__(self):
        self.parsers = {
            'python': self._parse_python,
            'javascript': self._parse_javascript,
            'typescript': self._parse_javascript,  # Similar syntax
            'java': self._parse_java,
            'cpp': self._parse_cpp,
            'c': self._parse_cpp,  # Similar syntax
            'go': self._parse_go,
            'rust': self._parse_rust,
        }
    
    def parse_file(self, content: str, language: str) -> Dict[str, List[Any]]:
        """
        Parse a file and extract functions, classes, and imports.
        
        Args:
            content: File content as string
            language: Programming language
            
        Returns:
            Dictionary with 'functions', 'classes', and 'imports' keys
        """
        parser = self.parsers.get(language.lower())
        if parser:
            return parser(content)
        else:
            return {'functions': [], 'classes': [], 'imports': []}
    
    def _parse_python(self, content: str) -> Dict[str, List[Any]]:
        """Parse Python code using AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {'functions': [], 'classes': [], 'imports': []}
        
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node),
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                }
                functions.append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node),
                    'bases': [self._get_base_name(base) for base in node.bases],
                    'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
                    'methods': [],
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'docstring': ast.get_docstring(item),
                            'args': [arg.arg for arg in item.args.args],
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                        }
                        class_info['methods'].append(method_info)
                
                classes.append(class_info)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                else:  # ImportFrom
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _get_decorator_name(self, decorator):
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        else:
            return str(decorator)
    
    def _get_base_name(self, base):
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}"
        else:
            return str(base)
    
    def _parse_javascript(self, content: str) -> Dict[str, List[Any]]:
        """Parse JavaScript/TypeScript code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        
        # Function patterns
        func_patterns = [
            r'function\s+(\w+)\s*\(',  # function name()
            r'(\w+)\s*:\s*function\s*\(',  # name: function()
            r'(\w+)\s*=\s*function\s*\(',  # name = function()
            r'(\w+)\s*=\s*\([^)]*\)\s*=>', # name = () =>
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>', # const name = () =>
            r'let\s+(\w+)\s*=\s*\([^)]*\)\s*=>', # let name = () =>
        ]
        
        # Class pattern
        class_pattern = r'class\s+(\w+)'
        
        # Import patterns
        import_patterns = [
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',  # import ... from 'module'
            r'import\s+["\']([^"\']+)["\']',  # import 'module'
            r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',  # require('module')
        ]
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for functions
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match:
                    functions.append({
                        'name': match.group(1),
                        'line': i,
                        'docstring': None,
                        'args': [],
                    })
            
            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                classes.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'methods': [],
                })
            
            # Check for imports
            for pattern in import_patterns:
                match = re.search(pattern, line)
                if match:
                    imports.append(match.group(1))
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_java(self, content: str) -> Dict[str, List[Any]]:
        """Parse Java code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        
        # Method pattern (simplified)
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\('
        
        # Class pattern
        class_pattern = r'(?:public|private)?\s*class\s+(\w+)'
        
        # Import pattern
        import_pattern = r'import\s+([^;]+);'
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for methods
            match = re.search(method_pattern, line)
            if match and not line.startswith('//'):
                functions.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'args': [],
                })
            
            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                classes.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'methods': [],
                })
            
            # Check for imports
            match = re.search(import_pattern, line)
            if match:
                imports.append(match.group(1).strip())
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_cpp(self, content: str) -> Dict[str, List[Any]]:
        """Parse C/C++ code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        
        # Function pattern (simplified)
        func_pattern = r'^\s*(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:{|;)'
        
        # Class pattern
        class_pattern = r'class\s+(\w+)'
        
        # Include pattern
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and preprocessor directives (except includes)
            if line.startswith('//') or (line.startswith('#') and not line.startswith('#include')):
                continue
            
            # Check for functions
            match = re.search(func_pattern, line)
            if match:
                name = match.group(1)
                # Skip common keywords
                if name not in ['if', 'for', 'while', 'switch', 'return', 'sizeof']:
                    functions.append({
                        'name': name,
                        'line': i,
                        'docstring': None,
                        'args': [],
                    })
            
            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                classes.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'methods': [],
                })
            
            # Check for includes
            match = re.search(include_pattern, line)
            if match:
                imports.append(match.group(1))
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_go(self, content: str) -> Dict[str, List[Any]]:
        """Parse Go code using regex patterns."""
        functions = []
        classes = []  # Go doesn't have classes, but has structs
        imports = []
        
        lines = content.split('\n')
        
        # Function pattern
        func_pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\('
        
        # Struct pattern (closest to classes in Go)
        struct_pattern = r'type\s+(\w+)\s+struct'
        
        # Import pattern
        import_pattern = r'import\s+(?:\(\s*)?["]([^"]+)["]'
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for functions
            match = re.search(func_pattern, line)
            if match:
                functions.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'args': [],
                })
            
            # Check for structs
            match = re.search(struct_pattern, line)
            if match:
                classes.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'methods': [],
                })
            
            # Check for imports
            match = re.search(import_pattern, line)
            if match:
                imports.append(match.group(1))
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_rust(self, content: str) -> Dict[str, List[Any]]:
        """Parse Rust code using regex patterns."""
        functions = []
        classes = []  # Rust has structs and enums
        imports = []
        
        lines = content.split('\n')
        
        # Function pattern
        func_pattern = r'fn\s+(\w+)\s*\('
        
        # Struct/enum pattern
        struct_pattern = r'(?:struct|enum)\s+(\w+)'
        
        # Use pattern
        use_pattern = r'use\s+([^;]+);'
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for functions
            match = re.search(func_pattern, line)
            if match:
                functions.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'args': [],
                })
            
            # Check for structs/enums
            match = re.search(struct_pattern, line)
            if match:
                classes.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': None,
                    'methods': [],
                })
            
            # Check for use statements
            match = re.search(use_pattern, line)
            if match:
                imports.append(match.group(1).strip())
        
        return {'functions': functions, 'classes': classes, 'imports': imports}