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
            'typescript': self._parse_typescript,
            'java': self._parse_java,
            'cpp': self._parse_cpp,
            'c': self._parse_cpp,  # Similar syntax
            'go': self._parse_go,
            'rust': self._parse_rust,
            'csharp': self._parse_csharp,
            'php': self._parse_php,
            'ruby': self._parse_ruby,
            'swift': self._parse_swift,
            'kotlin': self._parse_kotlin,
            'scala': self._parse_scala,
            'shell': self._parse_shell,
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
        """Parse JavaScript code using enhanced regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        in_multiline_comment = False
        
        # Enhanced function patterns
        func_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)',  # function name()
            r'(\w+)\s*:\s*function\s*\([^)]*\)',  # name: function()
            r'(\w+)\s*=\s*function\s*\([^)]*\)',  # name = function()
            r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>', # const name = () =>
            r'(?:const|let|var)\s+(\w+)\s*=\s*async\s*\([^)]*\)\s*=>', # async arrow functions
            r'async\s+function\s+(\w+)\s*\([^)]*\)',  # async function name()
            r'(\w+)\s*\([^)]*\)\s*\{',  # method-like patterns
        ]
        
        # Class and method patterns
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        method_pattern = r'(\w+)\s*\([^)]*\)\s*\{'
        
        # Enhanced import patterns
        import_patterns = [
            r'import\s+\{[^}]*\}\s+from\s+["\']([^"\']+)["\']',  # import { ... } from 'module'
            r'import\s+(\w+)\s+from\s+["\']([^"\']+)["\']',  # import name from 'module'
            r'import\s+\*\s+as\s+\w+\s+from\s+["\']([^"\']+)["\']',  # import * as name from 'module'
            r'import\s+["\']([^"\']+)["\']',  # import 'module'
            r'const\s+\{[^}]*\}\s+=\s+require\s*\(\s*["\']([^"\']+)["\']\s*\)',  # const { ... } = require('module')
            r'const\s+\w+\s+=\s+require\s*\(\s*["\']([^"\']+)["\']\s*\)',  # const name = require('module')
        ]
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # Handle multiline comments
            if '/*' in line and '*/' not in line:
                in_multiline_comment = True
                continue
            elif '*/' in line and in_multiline_comment:
                in_multiline_comment = False
                continue
            elif in_multiline_comment or line.startswith('//'):
                continue
            
            # Check for classes
            class_match = re.search(class_pattern, line)
            if class_match:
                class_info = {
                    'name': class_match.group(1),
                    'line': i,
                    'docstring': self._extract_js_comment(lines, i-1),
                    'methods': [],
                    'extends': class_match.group(2) if class_match.group(2) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for functions
            function_found = False
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match and not line.startswith('//'):
                    func_name = match.group(1)
                    
                    # Skip if it looks like a method call rather than definition
                    if '=' not in line and '(' in line and '{' not in line:
                        continue
                    
                    func_info = {
                        'name': func_name,
                        'line': i,
                        'docstring': self._extract_js_comment(lines, i-1),
                        'args': self._extract_js_args(line),
                        'is_async': 'async' in line,
                    }
                    
                    # If we're inside a class, add as method
                    if current_class and self._is_indented(original_line):
                        current_class['methods'].append(func_info)
                    else:
                        functions.append(func_info)
                    
                    function_found = True
                    break
            
            # Check for imports
            for pattern in import_patterns:
                match = re.search(pattern, line)
                if match:
                    # Get the last group which should be the module name
                    module = match.group(match.lastindex)
                    if module not in imports:
                        imports.append(module)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_typescript(self, content: str) -> Dict[str, List[Any]]:
        """Parse TypeScript code using enhanced patterns."""
        # Start with JavaScript parsing
        result = self._parse_javascript(content)
        
        lines = content.split('\n')
        
        # TypeScript-specific patterns
        interface_pattern = r'interface\s+(\w+)'
        type_pattern = r'type\s+(\w+)\s*='
        enum_pattern = r'enum\s+(\w+)'
        namespace_pattern = r'namespace\s+(\w+)'
        
        # Add TypeScript-specific constructs to classes
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Interfaces
            match = re.search(interface_pattern, line)
            if match:
                result['classes'].append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_js_comment(lines, i-1),
                    'type': 'interface',
                    'methods': [],
                })
            
            # Type aliases
            match = re.search(type_pattern, line)
            if match:
                result['classes'].append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_js_comment(lines, i-1),
                    'type': 'type',
                    'methods': [],
                })
            
            # Enums
            match = re.search(enum_pattern, line)
            if match:
                result['classes'].append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_js_comment(lines, i-1),
                    'type': 'enum',
                    'methods': [],
                })
            
            # Namespaces
            match = re.search(namespace_pattern, line)
            if match:
                result['classes'].append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_js_comment(lines, i-1),
                    'type': 'namespace',
                    'methods': [],
                })
        
        return result
    
    def _extract_js_comment(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract JSDoc or comment from previous lines."""
        if line_index < 0:
            return None
        
        comment_lines = []
        i = line_index
        
        # Look for JSDoc comments
        while i >= 0:
            line = lines[i].strip()
            if line.endswith('*/'):
                # Found end of JSDoc, collect lines going backwards
                while i >= 0 and not lines[i].strip().startswith('/**'):
                    if lines[i].strip().startswith('*'):
                        comment_lines.insert(0, lines[i].strip()[1:].strip())
                    i -= 1
                if i >= 0 and lines[i].strip().startswith('/**'):
                    break
                return ' '.join(comment_lines) if comment_lines else None
            elif line.startswith('//'):
                comment_lines.insert(0, line[2:].strip())
            else:
                break
            i -= 1
        
        return ' '.join(comment_lines) if comment_lines else None
    
    def _extract_js_args(self, line: str) -> List[str]:
        """Extract function arguments from JavaScript function definition."""
        # Find the part between parentheses
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return []
        
        args_str = match.group(1).strip()
        if not args_str:
            return []
        
        # Split by comma and clean up
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Remove TypeScript type annotations
            if ':' in arg:
                arg = arg.split(':')[0].strip()
            # Remove default values
            if '=' in arg:
                arg = arg.split('=')[0].strip()
            # Remove destructuring and rest parameters
            if arg.startswith('...'):
                arg = arg[3:].strip()
            if arg.startswith('{') or arg.startswith('['):
                continue
            if arg:
                args.append(arg)
        
        return args
    
    def _is_indented(self, line: str) -> bool:
        """Check if a line is indented (likely a class method)."""
        return len(line) - len(line.lstrip()) > 0
    
    def _parse_java(self, content: str) -> Dict[str, List[Any]]:
        """Parse Java code using enhanced regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        in_multiline_comment = False
        
        # Enhanced patterns for Java
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:abstract)?\s*(?:synchronized)?\s*(?:\w+(?:<[^>]*>)?)\s+(\w+)\s*\([^)]*\)'
        class_pattern = r'(?:public|private|protected)?\s*(?:final|abstract)?\s*(?:class|interface|enum)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        import_pattern = r'import\s+(?:static\s+)?([^;]+);'
        package_pattern = r'package\s+([^;]+);'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # Handle multiline comments
            if '/*' in line and '*/' not in line:
                in_multiline_comment = True
                continue
            elif '*/' in line and in_multiline_comment:
                in_multiline_comment = False
                continue
            elif in_multiline_comment or line.startswith('//'):
                continue
            
            # Check for package
            match = re.search(package_pattern, line)
            if match:
                imports.append(f"package:{match.group(1).strip()}")
                continue
            
            # Check for classes/interfaces/enums
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_javadoc(lines, i-1),
                    'methods': [],
                    'type': 'interface' if 'interface' in line else 'enum' if 'enum' in line else 'class',
                    'extends': match.group(2) if match.group(2) else None,
                    'implements': match.group(3).strip() if match.group(3) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for methods
            match = re.search(method_pattern, line)
            if match and not line.startswith('//') and ('{' in line or ';' in line):
                method_name = match.group(1)
                
                # Skip constructors and common keywords
                if method_name not in ['if', 'for', 'while', 'switch', 'return', 'new']:
                    method_info = {
                        'name': method_name,
                        'line': i,
                        'docstring': self._extract_javadoc(lines, i-1),
                        'args': self._extract_java_args(line),
                        'visibility': self._extract_java_visibility(line),
                        'is_static': 'static' in line,
                        'is_abstract': 'abstract' in line,
                    }
                    
                    # If we're inside a class, add as method
                    if current_class and self._is_indented(original_line):
                        current_class['methods'].append(method_info)
                    else:
                        functions.append(method_info)
            
            # Check for imports
            match = re.search(import_pattern, line)
            if match:
                import_name = match.group(1).strip()
                if import_name not in imports:
                    imports.append(import_name)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _extract_javadoc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract Javadoc comments from previous lines."""
        if line_index < 0:
            return None
        
        comment_lines = []
        i = line_index
        
        # Look for Javadoc comments
        while i >= 0:
            line = lines[i].strip()
            if line.endswith('*/'):
                # Found end of Javadoc, collect lines going backwards
                while i >= 0 and not lines[i].strip().startswith('/**'):
                    if lines[i].strip().startswith('*'):
                        comment_lines.insert(0, lines[i].strip()[1:].strip())
                    i -= 1
                if i >= 0 and lines[i].strip().startswith('/**'):
                    break
                return ' '.join(comment_lines) if comment_lines else None
            elif line.startswith('//'):
                comment_lines.insert(0, line[2:].strip())
            else:
                break
            i -= 1
        
        return ' '.join(comment_lines) if comment_lines else None
    
    def _extract_java_args(self, line: str) -> List[str]:
        """Extract method arguments from Java method definition."""
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return []
        
        args_str = match.group(1).strip()
        if not args_str:
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Remove type and keep only parameter name
            parts = arg.split()
            if len(parts) >= 2:
                args.append(parts[-1])  # Last part is usually the parameter name
        
        return args
    
    def _extract_java_visibility(self, line: str) -> str:
        """Extract visibility modifier from Java method/class definition."""
        if 'public' in line:
            return 'public'
        elif 'private' in line:
            return 'private'
        elif 'protected' in line:
            return 'protected'
        else:
            return 'package'
    
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
    
    def _parse_csharp(self, content: str) -> Dict[str, List[Any]]:
        """Parse C# code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        in_multiline_comment = False
        
        # C# patterns
        method_pattern = r'(?:public|private|protected|internal)?\s*(?:static)?\s*(?:virtual|override|abstract)?\s*(?:\w+(?:<[^>]*>)?)\s+(\w+)\s*\([^)]*\)'
        class_pattern = r'(?:public|private|protected|internal)?\s*(?:static|sealed|abstract)?\s*(?:class|interface|struct|enum)\s+(\w+)(?:\s*:\s*([^{]+))?'
        using_pattern = r'using\s+([^;]+);'
        namespace_pattern = r'namespace\s+([^{]+)'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # Handle multiline comments
            if '/*' in line and '*/' not in line:
                in_multiline_comment = True
                continue
            elif '*/' in line and in_multiline_comment:
                in_multiline_comment = False
                continue
            elif in_multiline_comment or line.startswith('//'):
                continue
            
            # Check for using statements
            match = re.search(using_pattern, line)
            if match:
                imports.append(match.group(1).strip())
                continue
            
            # Check for namespace
            match = re.search(namespace_pattern, line)
            if match:
                imports.append(f"namespace:{match.group(1).strip()}")
                continue
            
            # Check for classes/interfaces/structs/enums
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_xml_doc(lines, i-1),
                    'methods': [],
                    'type': 'interface' if 'interface' in line else 'struct' if 'struct' in line else 'enum' if 'enum' in line else 'class',
                    'inherits': match.group(2).strip() if match.group(2) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for methods
            match = re.search(method_pattern, line)
            if match and not line.startswith('//') and ('{' in line or ';' in line):
                method_name = match.group(1)
                
                if method_name not in ['if', 'for', 'while', 'switch', 'return', 'new', 'get', 'set']:
                    method_info = {
                        'name': method_name,
                        'line': i,
                        'docstring': self._extract_xml_doc(lines, i-1),
                        'args': self._extract_csharp_args(line),
                        'visibility': self._extract_csharp_visibility(line),
                        'is_static': 'static' in line,
                        'is_abstract': 'abstract' in line,
                        'is_virtual': 'virtual' in line,
                        'is_override': 'override' in line,
                    }
                    
                    if current_class and self._is_indented(original_line):
                        current_class['methods'].append(method_info)
                    else:
                        functions.append(method_info)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_php(self, content: str) -> Dict[str, List[Any]]:
        """Parse PHP code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        
        # PHP patterns
        function_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*function\s+(\w+)\s*\('
        class_pattern = r'(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        use_pattern = r'use\s+([^;]+);'
        include_pattern = r'(?:include|require)(?:_once)?\s*\(\s*["\']([^"\']+)["\']\s*\)'
        namespace_pattern = r'namespace\s+([^;]+);'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            if line.startswith('//') or line.startswith('#'):
                continue
            
            # Check for namespace
            match = re.search(namespace_pattern, line)
            if match:
                imports.append(f"namespace:{match.group(1).strip()}")
                continue
            
            # Check for use statements
            match = re.search(use_pattern, line)
            if match:
                imports.append(match.group(1).strip())
                continue
            
            # Check for includes
            match = re.search(include_pattern, line)
            if match:
                imports.append(match.group(1))
                continue
            
            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_php_doc(lines, i-1),
                    'methods': [],
                    'extends': match.group(2) if match.group(2) else None,
                    'implements': match.group(3).strip() if match.group(3) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for functions
            match = re.search(function_pattern, line)
            if match:
                func_name = match.group(1)
                func_info = {
                    'name': func_name,
                    'line': i,
                    'docstring': self._extract_php_doc(lines, i-1),
                    'args': self._extract_php_args(line),
                    'visibility': self._extract_php_visibility(line),
                    'is_static': 'static' in line,
                }
                
                if current_class and self._is_indented(original_line):
                    current_class['methods'].append(func_info)
                else:
                    functions.append(func_info)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_ruby(self, content: str) -> Dict[str, List[Any]]:
        """Parse Ruby code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        
        # Ruby patterns
        method_pattern = r'def\s+(\w+)'
        class_pattern = r'class\s+(\w+)(?:\s*<\s*(\w+))?'
        module_pattern = r'module\s+(\w+)'
        require_pattern = r'require\s+["\']([^"\']+)["\']'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            if line.startswith('#'):
                continue
            
            # Check for requires
            match = re.search(require_pattern, line)
            if match:
                imports.append(match.group(1))
                continue
            
            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_ruby_doc(lines, i-1),
                    'methods': [],
                    'superclass': match.group(2) if match.group(2) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for modules
            match = re.search(module_pattern, line)
            if match:
                classes.append({
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_ruby_doc(lines, i-1),
                    'type': 'module',
                    'methods': [],
                })
                continue
            
            # Check for methods
            match = re.search(method_pattern, line)
            if match:
                method_name = match.group(1)
                method_info = {
                    'name': method_name,
                    'line': i,
                    'docstring': self._extract_ruby_doc(lines, i-1),
                    'args': self._extract_ruby_args(line),
                }
                
                if current_class and self._is_indented(original_line):
                    current_class['methods'].append(method_info)
                else:
                    functions.append(method_info)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_swift(self, content: str) -> Dict[str, List[Any]]:
        """Parse Swift code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        
        # Swift patterns
        func_pattern = r'(?:public|private|internal|fileprivate)?\s*(?:static|class)?\s*func\s+(\w+)\s*\('
        class_pattern = r'(?:public|private|internal|fileprivate)?\s*(?:final)?\s*(?:class|struct|enum|protocol)\s+(\w+)(?:\s*:\s*([^{]+))?'
        import_pattern = r'import\s+([^\s]+)'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            if line.startswith('//'):
                continue
            
            # Check for imports
            match = re.search(import_pattern, line)
            if match:
                imports.append(match.group(1))
                continue
            
            # Check for classes/structs/enums/protocols
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_swift_doc(lines, i-1),
                    'methods': [],
                    'type': 'struct' if 'struct' in line else 'enum' if 'enum' in line else 'protocol' if 'protocol' in line else 'class',
                    'inherits': match.group(2).strip() if match.group(2) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for functions
            match = re.search(func_pattern, line)
            if match:
                func_name = match.group(1)
                func_info = {
                    'name': func_name,
                    'line': i,
                    'docstring': self._extract_swift_doc(lines, i-1),
                    'args': self._extract_swift_args(line),
                    'visibility': self._extract_swift_visibility(line),
                    'is_static': 'static' in line or 'class' in line,
                }
                
                if current_class and self._is_indented(original_line):
                    current_class['methods'].append(func_info)
                else:
                    functions.append(func_info)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_kotlin(self, content: str) -> Dict[str, List[Any]]:
        """Parse Kotlin code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        
        # Kotlin patterns
        fun_pattern = r'(?:public|private|protected|internal)?\s*(?:suspend)?\s*fun\s+(\w+)\s*\('
        class_pattern = r'(?:public|private|protected|internal)?\s*(?:data|sealed|abstract|open)?\s*(?:class|interface|object)\s+(\w+)(?:\s*:\s*([^{]+))?'
        import_pattern = r'import\s+([^\s]+)'
        package_pattern = r'package\s+([^\s]+)'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            if line.startswith('//'):
                continue
            
            # Check for package
            match = re.search(package_pattern, line)
            if match:
                imports.append(f"package:{match.group(1)}")
                continue
            
            # Check for imports
            match = re.search(import_pattern, line)
            if match:
                imports.append(match.group(1))
                continue
            
            # Check for classes/interfaces/objects
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_kotlin_doc(lines, i-1),
                    'methods': [],
                    'type': 'interface' if 'interface' in line else 'object' if 'object' in line else 'class',
                    'inherits': match.group(2).strip() if match.group(2) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for functions
            match = re.search(fun_pattern, line)
            if match:
                func_name = match.group(1)
                func_info = {
                    'name': func_name,
                    'line': i,
                    'docstring': self._extract_kotlin_doc(lines, i-1),
                    'args': self._extract_kotlin_args(line),
                    'visibility': self._extract_kotlin_visibility(line),
                    'is_suspend': 'suspend' in line,
                }
                
                if current_class and self._is_indented(original_line):
                    current_class['methods'].append(func_info)
                else:
                    functions.append(func_info)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_scala(self, content: str) -> Dict[str, List[Any]]:
        """Parse Scala code using regex patterns."""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        current_class = None
        
        # Scala patterns
        def_pattern = r'def\s+(\w+)\s*\('
        class_pattern = r'(?:class|trait|object)\s+(\w+)(?:\s+extends\s+([^{]+))?'
        import_pattern = r'import\s+([^\s]+)'
        package_pattern = r'package\s+([^\s]+)'
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            if line.startswith('//'):
                continue
            
            # Check for package
            match = re.search(package_pattern, line)
            if match:
                imports.append(f"package:{match.group(1)}")
                continue
            
            # Check for imports
            match = re.search(import_pattern, line)
            if match:
                imports.append(match.group(1))
                continue
            
            # Check for classes/traits/objects
            match = re.search(class_pattern, line)
            if match:
                class_info = {
                    'name': match.group(1),
                    'line': i,
                    'docstring': self._extract_scala_doc(lines, i-1),
                    'methods': [],
                    'type': 'trait' if 'trait' in line else 'object' if 'object' in line else 'class',
                    'extends': match.group(2).strip() if match.group(2) else None,
                }
                classes.append(class_info)
                current_class = class_info
                continue
            
            # Check for methods/functions
            match = re.search(def_pattern, line)
            if match:
                func_name = match.group(1)
                func_info = {
                    'name': func_name,
                    'line': i,
                    'docstring': self._extract_scala_doc(lines, i-1),
                    'args': self._extract_scala_args(line),
                }
                
                if current_class and self._is_indented(original_line):
                    current_class['methods'].append(func_info)
                else:
                    functions.append(func_info)
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    def _parse_shell(self, content: str) -> Dict[str, List[Any]]:
        """Parse shell script using regex patterns."""
        functions = []
        classes = []  # Shell doesn't have classes
        imports = []
        
        lines = content.split('\n')
        
        # Shell function patterns
        func_patterns = [
            r'function\s+(\w+)\s*\(\)',  # function name()
            r'(\w+)\s*\(\)\s*\{',       # name() {
        ]
        
        # Source/import patterns
        source_patterns = [
            r'source\s+([^\s]+)',
            r'\.\s+([^\s]+)',
        ]
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if line.startswith('#'):
                continue
            
            # Check for functions
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match:
                    functions.append({
                        'name': match.group(1),
                        'line': i,
                        'docstring': self._extract_shell_doc(lines, i-1),
                        'args': [],
                    })
                    break
            
            # Check for source/imports
            for pattern in source_patterns:
                match = re.search(pattern, line)
                if match:
                    imports.append(match.group(1))
                    break
        
        return {'functions': functions, 'classes': classes, 'imports': imports}
    
    # Helper methods for different language documentation extraction
    def _extract_xml_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract XML documentation (C#)."""
        if line_index < 0:
            return None
        
        comment_lines = []
        i = line_index
        
        while i >= 0:
            line = lines[i].strip()
            if line.startswith('///'):
                comment_lines.insert(0, line[3:].strip())
            else:
                break
            i -= 1
        
        return ' '.join(comment_lines) if comment_lines else None
    
    def _extract_php_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract PHPDoc comments."""
        return self._extract_javadoc(lines, line_index)  # PHPDoc uses similar format
    
    def _extract_ruby_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract Ruby documentation comments."""
        if line_index < 0:
            return None
        
        comment_lines = []
        i = line_index
        
        while i >= 0:
            line = lines[i].strip()
            if line.startswith('#'):
                comment_lines.insert(0, line[1:].strip())
            else:
                break
            i -= 1
        
        return ' '.join(comment_lines) if comment_lines else None
    
    def _extract_swift_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract Swift documentation comments."""
        if line_index < 0:
            return None
        
        comment_lines = []
        i = line_index
        
        while i >= 0:
            line = lines[i].strip()
            if line.startswith('///'):
                comment_lines.insert(0, line[3:].strip())
            elif line.startswith('//'):
                comment_lines.insert(0, line[2:].strip())
            else:
                break
            i -= 1
        
        return ' '.join(comment_lines) if comment_lines else None
    
    def _extract_kotlin_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract Kotlin documentation comments."""
        return self._extract_javadoc(lines, line_index)  # KDoc uses similar format
    
    def _extract_scala_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract Scala documentation comments."""
        return self._extract_javadoc(lines, line_index)  # Scaladoc uses similar format
    
    def _extract_shell_doc(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract shell script comments."""
        return self._extract_ruby_doc(lines, line_index)  # Shell uses # comments like Ruby
    
    # Argument extraction helpers for different languages
    def _extract_csharp_args(self, line: str) -> List[str]:
        """Extract C# method arguments."""
        return self._extract_java_args(line)  # Similar format
    
    def _extract_php_args(self, line: str) -> List[str]:
        """Extract PHP function arguments."""
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return []
        
        args_str = match.group(1).strip()
        if not args_str:
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Remove type hints and default values
            if '=' in arg:
                arg = arg.split('=')[0].strip()
            # Remove $ from variable names
            if arg.startswith('$'):
                arg = arg[1:]
            if arg:
                args.append(arg)
        
        return args
    
    def _extract_ruby_args(self, line: str) -> List[str]:
        """Extract Ruby method arguments."""
        match = re.search(r'def\s+\w+\s*\(([^)]*)\)', line)
        if not match:
            # Check for arguments without parentheses
            match = re.search(r'def\s+\w+\s+(.+)', line)
            if match:
                args_str = match.group(1).strip()
            else:
                return []
        else:
            args_str = match.group(1).strip()
        
        if not args_str:
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Remove default values and block parameters
            if '=' in arg:
                arg = arg.split('=')[0].strip()
            if '&' in arg:
                arg = arg.replace('&', '').strip()
            if '*' in arg:
                arg = arg.replace('*', '').strip()
            if arg:
                args.append(arg)
        
        return args
    
    def _extract_swift_args(self, line: str) -> List[str]:
        """Extract Swift function arguments."""
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return []
        
        args_str = match.group(1).strip()
        if not args_str:
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Swift has external and internal parameter names
            parts = arg.split(':')
            if len(parts) >= 2:
                # Get the internal parameter name (before the colon)
                param_part = parts[0].strip()
                # Handle "_ paramName" or "externalName paramName"
                param_parts = param_part.split()
                if len(param_parts) >= 2:
                    args.append(param_parts[-1])  # Last part is internal name
                elif param_part != '_':
                    args.append(param_part)
        
        return args
    
    def _extract_kotlin_args(self, line: str) -> List[str]:
        """Extract Kotlin function arguments."""
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return []
        
        args_str = match.group(1).strip()
        if not args_str:
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Remove type annotations and default values
            if ':' in arg:
                arg = arg.split(':')[0].strip()
            if '=' in arg:
                arg = arg.split('=')[0].strip()
            if arg:
                args.append(arg)
        
        return args
    
    def _extract_scala_args(self, line: str) -> List[str]:
        """Extract Scala function arguments."""
        match = re.search(r'\(([^)]*)\)', line)
        if not match:
            return []
        
        args_str = match.group(1).strip()
        if not args_str:
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # Remove type annotations
            if ':' in arg:
                arg = arg.split(':')[0].strip()
            if arg:
                args.append(arg)
        
        return args
    
    # Visibility extraction helpers
    def _extract_csharp_visibility(self, line: str) -> str:
        """Extract C# visibility modifier."""
        if 'public' in line:
            return 'public'
        elif 'private' in line:
            return 'private'
        elif 'protected' in line:
            return 'protected'
        elif 'internal' in line:
            return 'internal'
        else:
            return 'private'  # Default in C#
    
    def _extract_php_visibility(self, line: str) -> str:
        """Extract PHP visibility modifier."""
        if 'public' in line:
            return 'public'
        elif 'private' in line:
            return 'private'
        elif 'protected' in line:
            return 'protected'
        else:
            return 'public'  # Default in PHP
    
    def _extract_swift_visibility(self, line: str) -> str:
        """Extract Swift access control modifier."""
        if 'public' in line:
            return 'public'
        elif 'private' in line:
            return 'private'
        elif 'fileprivate' in line:
            return 'fileprivate'
        elif 'internal' in line:
            return 'internal'
        else:
            return 'internal'  # Default in Swift
    
    def _extract_kotlin_visibility(self, line: str) -> str:
        """Extract Kotlin visibility modifier."""
        if 'public' in line:
            return 'public'
        elif 'private' in line:
            return 'private'
        elif 'protected' in line:
            return 'protected'
        elif 'internal' in line:
            return 'internal'
        else:
            return 'public'  # Default in Kotlin