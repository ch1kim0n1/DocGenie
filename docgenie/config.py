"""
Configuration management for DocGenie.

This module handles loading and managing configuration settings from various sources:
- Configuration files (YAML, JSON, TOML)
- Environment variables
- Command line arguments
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import click

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # fallback for older Python versions
    except ImportError:
        tomllib = None


class DocGenieConfig:
    """
    Configuration manager for DocGenie HTML converter.
    
    Supports configuration files in YAML, JSON, and TOML formats.
    Configuration is loaded in this priority order:
    1. Command line arguments (highest priority)
    2. Environment variables
    3. Project-specific config file (.docgenie.yml, .docgenie.json, .docgenie.toml)
    4. User-specific config file (~/.docgenie/config.yml)
    5. Default values (lowest priority)
    """
    
    DEFAULT_CONFIG = {
        'output': {
            'directory': 'docs',
            'filename': 'docs.html',
            'theme': 'default',
        },
        'generation': {
            'title': None,
            'force_overwrite': False,
            'open_browser': False,
            'verbose': False,
        },
        'codebase': {
            'exclude_patterns': [
                '.git/**',
                '.svn/**',
                '__pycache__/**',
                'node_modules/**',
                '.venv/**',
                'venv/**',
                'build/**',
                'dist/**',
                'target/**',
                '.idea/**',
                '.vscode/**',
                '*.pyc',
                '*.pyo',
                '*.pyd',
                '*.log',
                '*.tmp',
                '*.temp',
                '*.min.js',
                '*.min.css',
                'coverage/**',
                '.pytest_cache/**',
                '.tox/**',
                '*.egg-info/**',
            ],
            'exclude_files': [],
            'exclude_directories': [],
            'include_patterns': [],
        },
        'html': {
            'custom_css': None,
            'custom_js': None,
            'favicon': None,
            'meta_description': None,
            'meta_keywords': None,
        }
    }
    
    CONFIG_FILENAMES = [
        '.docgenie.yml',
        '.docgenie.yaml', 
        '.docgenie.json',
        '.docgenie.toml'
    ]
    def __init__(self, project_path: Optional[Union[str, Path]] = None, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager.
        
        Args:
            project_path: Path to the project directory (for finding project-specific config)
            config_file: Path to a specific config file to load
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.config_file = Path(config_file) if config_file else None
        self.config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    def _load_config(self):
        """Load configuration from all available sources."""
        # Load user-specific config
        self._load_user_config()
        
        # Load specific config file or project-specific config
        if self.config_file:
            self._load_specific_config_file()
        else:
            self._load_project_config()
        
        # Load environment variables
        self._load_env_config()
    
    def _load_user_config(self):
        """Load user-specific configuration from ~/.docgenie/config.yml"""
        user_config_dir = Path.home() / '.docgenie'
        user_config_file = user_config_dir / 'config.yml'
        
        if user_config_file.exists():
            try:
                user_config = self._load_yaml_file(user_config_file)
                if user_config:
                    self._deep_merge_config(self.config, user_config)
            except Exception as e:
                click.echo(f"Warning: Failed to load user config from {user_config_file}: {e}", err=True)
    
    def _load_specific_config_file(self):
        """Load configuration from a specific config file."""
        if self.config_file and self.config_file.exists():
            try:
                config_data = self._load_config_file(self.config_file)
                if config_data:
                    self._deep_merge_config(self.config, config_data)
                    click.echo(f"📋 Loaded configuration from {self.config_file}", err=True)
            except Exception as e:
                click.echo(f"Warning: Failed to load config from {self.config_file}: {e}", err=True)

    def _load_project_config(self):
        """Load project-specific configuration."""
        for filename in self.CONFIG_FILENAMES:
            config_path = self.project_path / filename
            if config_path.exists():
                try:
                    config_data = self._load_config_file(config_path)
                    if config_data:
                        self._deep_merge_config(self.config, config_data)
                        click.echo(f"📋 Loaded configuration from {filename}", err=True)
                    break
                except Exception as e:
                    click.echo(f"Warning: Failed to load config from {config_path}: {e}", err=True)
    
    def _load_env_config(self):
        """Load configuration from environment variables."""
        env_mapping = {
            'DOCGENIE_OUTPUT_DIR': ('output', 'directory'),
            'DOCGENIE_OUTPUT_FILE': ('output', 'filename'),
            'DOCGENIE_THEME': ('output', 'theme'),
            'DOCGENIE_TITLE': ('generation', 'title'),
            'DOCGENIE_FORCE': ('generation', 'force_overwrite'),
            'DOCGENIE_VERBOSE': ('generation', 'verbose'),
            'DOCGENIE_OPEN_BROWSER': ('generation', 'open_browser'),
        }
        
        for env_var, (section, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if key in ['force_overwrite', 'verbose', 'open_browser']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value
    
    def _load_config_file(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from a file based on its extension."""
        suffix = config_path.suffix.lower()
        
        if suffix in ['.yml', '.yaml']:
            return self._load_yaml_file(config_path)
        elif suffix == '.json':
            return self._load_json_file(config_path)
        elif suffix == '.toml':
            return self._load_toml_file(config_path)
        else:
            raise ValueError(f"Unsupported config file format: {suffix}")
    
    def _load_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to read YAML file: {e}")
    
    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON configuration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to read JSON file: {e}")
    
    def _load_toml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load TOML configuration file."""
        if tomllib is None:
            raise RuntimeError("TOML support not available. Install tomli package for Python < 3.11")
        
        try:
            with open(file_path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to read TOML file: {e}")
    
    def _deep_merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Deeply merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name (optional)
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if key is None:
            return self.config.get(section, default)
        
        section_config = self.config.get(section, {})
        if isinstance(section_config, dict):
            return section_config.get(key, default)
        
        return default
    
    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        
        if isinstance(self.config[section], dict):
            self.config[section][key] = value
        else:
            self.config[section] = {key: value}
    
    def get_output_path(self, input_path: Optional[Path] = None, source_type: str = 'readme') -> Path:
        """
        Get the output path for generated HTML documentation.
        
        Args:
            input_path: Input path (file or directory)
            source_type: Type of source ('readme' or 'codebase')
            
        Returns:
            Path object for output HTML file
        """
        output_dir = self.get('output', 'directory', 'docs')
        output_filename = self.get('output', 'filename', 'docs.html')
        
        if input_path is None:
            return Path(output_dir) / output_filename
        
        input_path = Path(input_path)
        
        if source_type == 'readme':
            base_dir = input_path.parent
        else:
            base_dir = input_path
        
        # If output_dir is relative, make it relative to the input base directory
        if not Path(output_dir).is_absolute():
            output_path = base_dir / output_dir / output_filename
        else:
            output_path = Path(output_dir) / output_filename
        
        return output_path
    
    def get_exclude_patterns(self) -> List[str]:
        """Get list of patterns to exclude from codebase analysis."""
        patterns = self.get('codebase', 'exclude_patterns', [])
        files = self.get('codebase', 'exclude_files', [])
        directories = self.get('codebase', 'exclude_directories', [])
        
        # Combine all exclusion patterns
        all_patterns = patterns.copy()
        all_patterns.extend(files)
        all_patterns.extend([f"{d}/**" for d in directories])
        
        return all_patterns
    
    def get_include_patterns(self) -> List[str]:
        """Get list of patterns to explicitly include in codebase analysis."""
        return self.get('codebase', 'include_patterns', [])
    
    def create_sample_config(self, output_path: Optional[Path] = None) -> Path:
        """
        Create a sample configuration file with comments.
        
        Args:
            output_path: Path where to create the config file
            
        Returns:
            Path to the created config file
        """
        if output_path is None:
            output_path = self.project_path / '.docgenie.yml'
        
        sample_config = '''# DocGenie Configuration File
# This file allows you to customize the behavior of DocGenie HTML documentation generator

# Output configuration
output:
  directory: docs              # Output directory for HTML files
  filename: docs.html          # Output filename
  theme: default              # HTML theme: default, dark, minimal

# Generation settings
generation:
  title: null                 # Custom title for documentation (null = auto-detect)
  force_overwrite: false      # Always overwrite existing files without prompting
  open_browser: false         # Open generated HTML in browser automatically
  verbose: false              # Enable verbose output

# Codebase analysis configuration
codebase:
  # Patterns to exclude from analysis (supports glob patterns)
  exclude_patterns:
    - .git/**
    - __pycache__/**
    - node_modules/**
    - .venv/**
    - venv/**
    - build/**
    - dist/**
    - target/**
    - .idea/**
    - .vscode/**
    - "*.pyc"
    - "*.pyo"
    - "*.log"
    - "*.min.js"
    - "*.min.css"
    - coverage/**
    - .pytest_cache/**
    - "*.egg-info/**"
  
  # Specific files to exclude
  exclude_files:
    # - specific_file.py
    # - another_file.js
  
  # Specific directories to exclude
  exclude_directories:
    # - temp_dir
    # - backup_folder
  
  # Patterns to explicitly include (overrides exclude patterns)
  include_patterns:
    # - important_file.py
    # - "src/**/*.js"

# HTML customization
html:
  custom_css: null            # Path to custom CSS file
  custom_js: null             # Path to custom JavaScript file
  favicon: null               # Path to favicon file
  meta_description: null      # HTML meta description
  meta_keywords: null         # HTML meta keywords
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sample_config)
        
        return output_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the current configuration as a dictionary."""
        return self.config.copy()


def load_config(project_path: Optional[Union[str, Path]] = None, config_file: Optional[Union[str, Path]] = None) -> DocGenieConfig:
    """
    Load DocGenie configuration.
    
    Args:
        project_path: Path to the project directory
        config_file: Path to a specific config file to load
        
    Returns:
        DocGenieConfig instance
    """
    return DocGenieConfig(project_path, config_file)
