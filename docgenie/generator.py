"""
README generation functionality for DocGenie.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template

from .utils import get_project_type, create_directory_tree, format_file_size


class ReadmeGenerator:
    """
    Generates comprehensive README.md files based on codebase analysis.
    """
    
    def __init__(self):
        self.template = self._get_template()
    
    def generate(self, analysis_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate README content based on analysis data.
        
        Args:
            analysis_data: Results from CodebaseAnalyzer
            output_path: Optional path to save the README file
            
        Returns:
            Generated README content as string
        """
        # Prepare template context
        context = self._prepare_context(analysis_data)
        
        # Render template
        readme_content = self.template.render(**context)
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"📝 README generated: {output_path}")
        
        return readme_content
    
    def _prepare_context(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare template context from analysis data."""
        
        # Basic project info
        project_name = self._get_project_name(analysis_data)
        project_type = get_project_type(analysis_data)
        
        # Language statistics
        languages = analysis_data.get('languages', {})
        main_language = analysis_data.get('main_language', 'unknown')
        
        # Dependencies
        dependencies = analysis_data.get('dependencies', {})
        
        # Git information
        git_info = analysis_data.get('git_info', {})
        
        # Project structure
        structure = analysis_data.get('project_structure', {})
        directory_tree = create_directory_tree(structure)
        
        # Code statistics
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        # Installation commands
        install_commands = self._generate_install_commands(analysis_data)
        
        # Usage examples
        usage_examples = self._generate_usage_examples(analysis_data)
        
        # API documentation
        api_docs = self._generate_api_docs(functions, classes)
        
        return {
            'project_name': project_name,
            'project_type': project_type,
            'description': self._generate_description(analysis_data),
            'languages': languages,
            'main_language': main_language,
            'total_files': analysis_data.get('files_analyzed', 0),
            'dependencies': dependencies,
            'git_info': git_info,
            'directory_tree': directory_tree,
            'functions_count': len(functions),
            'classes_count': len(classes),
            'install_commands': install_commands,
            'usage_examples': usage_examples,
            'api_docs': api_docs,
            'features': self._extract_features(analysis_data),
            'requirements': self._extract_requirements(dependencies),
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'has_tests': self._has_tests(analysis_data),
            'has_docs': len(analysis_data.get('documentation_files', [])) > 0,
            'config_files': analysis_data.get('config_files', []),
        }
    
    def _get_project_name(self, analysis_data: Dict[str, Any]) -> str:
        """Extract project name from various sources."""
        # Try git repository name first
        git_info = analysis_data.get('git_info', {})
        if 'repo_name' in git_info:
            repo_name = git_info['repo_name']
            if '/' in repo_name:
                return repo_name.split('/')[-1]
            return repo_name
        
        # Fall back to directory name
        root_path = analysis_data.get('root_path', '')
        if root_path:
            return Path(root_path).name
        
        return "Project"
    
    def _generate_description(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a project description based on analysis."""
        project_type = get_project_type(analysis_data)
        main_language = analysis_data.get('main_language', 'unknown')
        
        # Try to infer purpose from structure and dependencies
        dependencies = analysis_data.get('dependencies', {})
        dep_strings = [str(deps).lower() for deps in dependencies.values()]
        
        if any('web' in deps or 'http' in deps or 'server' in deps for deps in dep_strings):
            purpose = "web application"
        elif any('api' in deps or 'rest' in deps for deps in dep_strings):
            purpose = "API service"
        elif any('cli' in deps or 'command' in deps for deps in dep_strings):
            purpose = "command-line tool"
        elif any('data' in deps or 'analysis' in deps or 'ml' in deps for deps in dep_strings):
            purpose = "data analysis tool"
        elif any('game' in deps for deps in dep_strings):
            purpose = "game"
        else:
            purpose = "application"
        
        return f"A {main_language.lower()} {purpose} with comprehensive functionality and modern architecture."
    
    def _generate_install_commands(self, analysis_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate installation commands based on project type."""
        commands = []
        dependencies = analysis_data.get('dependencies', {})
        structure = analysis_data.get('project_structure', {})
        root_files = structure.get('root', {}).get('files', [])
        
        # Python projects
        if 'requirements.txt' in root_files:
            commands.append({
                'title': 'Install Python dependencies',
                'command': 'pip install -r requirements.txt'
            })
        elif 'pyproject.toml' in root_files:
            commands.append({
                'title': 'Install with Poetry',
                'command': 'poetry install'
            })
        elif 'setup.py' in root_files:
            commands.append({
                'title': 'Install package',
                'command': 'pip install -e .'
            })
        
        # Node.js projects
        if 'package.json' in root_files:
            commands.append({
                'title': 'Install Node.js dependencies',
                'command': 'npm install'
            })
        
        # Rust projects
        if 'Cargo.toml' in root_files:
            commands.append({
                'title': 'Build Rust project',
                'command': 'cargo build'
            })
        
        # Go projects
        if 'go.mod' in root_files:
            commands.append({
                'title': 'Download Go dependencies',
                'command': 'go mod download'
            })
        
        # Java projects
        if 'pom.xml' in root_files:
            commands.append({
                'title': 'Build with Maven',
                'command': 'mvn clean install'
            })
        elif 'build.gradle' in root_files:
            commands.append({
                'title': 'Build with Gradle',
                'command': './gradlew build'
            })
        
        return commands
    
    def _generate_usage_examples(self, analysis_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate usage examples based on project analysis."""
        examples = []
        main_language = analysis_data.get('main_language', 'unknown')
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        # Find main entry points
        main_functions = [f for f in functions if f['name'] in ['main', 'run', 'start', 'execute']]
        
        if main_language == 'python':
            if main_functions:
                examples.append({
                    'title': 'Run the application',
                    'command': 'python main.py'
                })
            elif classes:
                class_name = classes[0]['name']
                examples.append({
                    'title': f'Use the {class_name} class',
                    'command': f'from {self._get_project_name(analysis_data).lower()} import {class_name}\n\ninstance = {class_name}()\nresult = instance.method()'
                })
        
        elif main_language == 'javascript':
            examples.append({
                'title': 'Run with Node.js',
                'command': 'node index.js'
            })
            examples.append({
                'title': 'Start development server',
                'command': 'npm start'
            })
        
        elif main_language == 'java':
            examples.append({
                'title': 'Run the application',
                'command': 'java -jar target/app.jar'
            })
        
        elif main_language == 'rust':
            examples.append({
                'title': 'Run the application',
                'command': 'cargo run'
            })
        
        elif main_language == 'go':
            examples.append({
                'title': 'Run the application',
                'command': 'go run main.go'
            })
        
        # Add generic examples if no specific ones found
        if not examples:
            examples.append({
                'title': 'Basic usage',
                'command': '# Add your usage examples here'
            })
        
        return examples
    
    def _generate_api_docs(self, functions: List[Dict], classes: List[Dict]) -> Dict[str, Any]:
        """Generate API documentation from functions and classes."""
        api_docs = {
            'functions': [],
            'classes': []
        }
        
        # Document main functions (limit to avoid overwhelming)
        main_functions = [f for f in functions if not f['name'].startswith('_')][:10]
        for func in main_functions:
            doc = {
                'name': func['name'],
                'file': func.get('file', ''),
                'line': func.get('line', 0),
                'docstring': func.get('docstring', ''),
                'args': func.get('args', []),
                'decorators': func.get('decorators', []),
            }
            api_docs['functions'].append(doc)
        
        # Document main classes (limit to avoid overwhelming)
        main_classes = [c for c in classes if not c['name'].startswith('_')][:10]
        for cls in main_classes:
            doc = {
                'name': cls['name'],
                'file': cls.get('file', ''),
                'line': cls.get('line', 0),
                'docstring': cls.get('docstring', ''),
                'methods': cls.get('methods', [])[:5],  # Limit methods shown
                'bases': cls.get('bases', []),
            }
            api_docs['classes'].append(doc)
        
        return api_docs
    
    def _extract_features(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract key features from the codebase analysis."""
        features = []
        dependencies = analysis_data.get('dependencies', {})
        functions = analysis_data.get('functions', [])
        classes = analysis_data.get('classes', [])
        
        # Analyze dependencies for features
        dep_strings = [str(deps).lower() for deps in dependencies.values()]
        
        if any('web' in deps or 'http' in deps for deps in dep_strings):
            features.append("🌐 Web interface")
        
        if any('api' in deps or 'rest' in deps for deps in dep_strings):
            features.append("🔌 REST API")
        
        if any('database' in deps or 'db' in deps or 'sql' in deps for deps in dep_strings):
            features.append("🗄️ Database integration")
        
        if any('test' in deps for deps in dep_strings):
            features.append("🧪 Comprehensive testing")
        
        if any('auth' in deps or 'login' in deps for deps in dep_strings):
            features.append("🔐 Authentication system")
        
        if any('cache' in deps or 'redis' in deps for deps in dep_strings):
            features.append("⚡ Caching system")
        
        if any('async' in f['name'] or f.get('is_async') for f in functions):
            features.append("🔄 Asynchronous processing")
        
        if len(classes) > 5:
            features.append("🏗️ Object-oriented architecture")
        
        if analysis_data.get('git_info', {}).get('contributor_count', 0) > 1:
            features.append("👥 Collaborative development")
        
        # Add generic features if none found
        if not features:
            features = [
                "⚡ High performance",
                "🛠️ Easy to use",
                "📦 Modular design",
                "🔧 Configurable"
            ]
        
        return features
    
    def _extract_requirements(self, dependencies: Dict[str, Any]) -> List[str]:
        """Extract system requirements."""
        requirements = []
        
        if 'package.json' in dependencies:
            requirements.append("Node.js 14.0 or higher")
            requirements.append("npm or yarn")
        
        if any(key in dependencies for key in ['requirements.txt', 'pyproject.toml', 'setup.py']):
            requirements.append("Python 3.8 or higher")
            requirements.append("pip")
        
        if 'Cargo.toml' in dependencies:
            requirements.append("Rust 1.60 or higher")
            requirements.append("Cargo")
        
        if 'go.mod' in dependencies:
            requirements.append("Go 1.18 or higher")
        
        if 'pom.xml' in dependencies:
            requirements.append("Java 11 or higher")
            requirements.append("Maven 3.6 or higher")
        
        if not requirements:
            requirements.append("See installation instructions below")
        
        return requirements
    
    def _has_tests(self, analysis_data: Dict[str, Any]) -> bool:
        """Check if the project has tests."""
        structure = analysis_data.get('project_structure', {})
        
        # Check for test directories
        for path in structure.keys():
            if 'test' in path.lower() or 'spec' in path.lower():
                return True
        
        # Check for test files in root
        root_files = structure.get('root', {}).get('files', [])
        for file in root_files:
            if 'test' in file.lower() or file.startswith('test_') or file.endswith('_test.py'):
                return True
        
        return False
    
    def _get_template(self) -> Template:
        """Get the README template."""
        template_content = """# {{ project_name }}

{{ description }}

## 🚀 Features

{% for feature in features %}
- {{ feature }}
{% endfor %}

## 📋 Requirements

{% for req in requirements %}
- {{ req }}
{% endfor %}

## 🛠️ Installation

{% for cmd in install_commands %}
### {{ cmd.title }}

```bash
{{ cmd.command }}
```

{% endfor %}

## 📖 Usage

{% for example in usage_examples %}
### {{ example.title }}

```{% if main_language != 'unknown' %}{{ main_language }}{% endif %}
{{ example.command }}
```

{% endfor %}

## 📁 Project Structure

```
{{ directory_tree }}
```

## 🏗️ Architecture

This {{ project_type.lower() }} is built with {{ main_language }} and consists of:

- **{{ functions_count }}** functions across the codebase
- **{{ classes_count }}** classes/components
- **{{ total_files }}** source files analyzed
- **{{ languages|length }}** programming languages used

### Language Distribution

{% for lang, count in languages.items() %}
- **{{ lang.title() }}**: {{ count }} files
{% endfor %}

{% if api_docs.functions %}
## 🔧 API Reference

### Functions

{% for func in api_docs.functions %}
#### `{{ func.name }}({{ func.args|join(', ') }})`

{% if func.docstring %}
{{ func.docstring }}
{% else %}
Function defined in `{{ func.file }}` at line {{ func.line }}.
{% endif %}

{% endfor %}
{% endif %}

{% if api_docs.classes %}
### Classes

{% for cls in api_docs.classes %}
#### `{{ cls.name }}`

{% if cls.docstring %}
{{ cls.docstring }}
{% else %}
Class defined in `{{ cls.file }}` at line {{ cls.line }}.
{% endif %}

{% if cls.methods %}
**Methods:**
{% for method in cls.methods %}
- `{{ method.name }}({{ method.args|join(', ') }})`
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

{% if dependencies %}
## 📦 Dependencies

{% for dep_file, deps in dependencies.items() %}
### {{ dep_file }}

{% if deps is mapping %}
{% for category, dep_list in deps.items() %}
**{{ category.title() }}:**
{% for dep in dep_list %}
- {{ dep }}
{% endfor %}
{% endfor %}
{% else %}
{% for dep in deps %}
- {{ dep }}
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

{% if has_tests %}
## 🧪 Testing

This project includes comprehensive tests. Run them with:

```bash
{% if main_language == 'python' %}
pytest
{% elif main_language == 'javascript' %}
npm test
{% elif main_language == 'rust' %}
cargo test
{% elif main_language == 'go' %}
go test ./...
{% elif main_language == 'java' %}
mvn test
{% else %}
# Run your tests here
{% endif %}
```
{% endif %}

{% if config_files %}
## ⚙️ Configuration

Configuration files:
{% for config in config_files %}
- `{{ config }}`
{% endfor %}
{% endif %}

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

{% if git_info.contributor_count %}
## 👥 Contributors

This project has {{ git_info.contributor_count }} contributor{{ 's' if git_info.contributor_count != 1 else '' }}.
{% endif %}

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

{% if git_info.remote_url %}
- Repository: [{{ git_info.repo_name }}]({{ git_info.remote_url }})
{% endif %}
{% if git_info.latest_commit %}
- Latest commit: {{ git_info.latest_commit.message }}
{% endif %}

---

*This README was automatically generated by [DocGenie](https://github.com/docgenie/docgenie) on {{ generated_date }}*
"""
        
        return Template(template_content)