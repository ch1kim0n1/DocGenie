"""
Command-line interface for DocGenie.

Unified CLI with consistent commands and options.
"""

import sys
import json
import yaml
import click
from pathlib import Path
from typing import Optional

from .core import CodebaseAnalyzer
from .generator import ReadmeGenerator
from .html_generator import HTMLGenerator
from .config import load_config


# Global options that can be passed to any command
@click.group()
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.version_option(version='1.0.0', prog_name='DocGenie')
@click.pass_context
def cli(ctx, config: Optional[Path], verbose: bool):
    """DocGenie - Auto-documentation tool for codebases.
    
    Generate comprehensive documentation for any codebase by analyzing
    source code, dependencies, and project structure.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path), default='.')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output path for the generated documentation')
@click.option('--format', '--fmt', type=click.Choice(['markdown', 'html', 'both']), default='markdown',
              help='Output format: markdown (README.md), html (HTML documentation), or both')
@click.option('--theme', '-t', type=click.Choice(['default', 'dark', 'minimal']), default='default',
              help='HTML theme style (only applies to HTML output)')
@click.option('--title', type=str, 
              help='Custom title for the documentation')
@click.option('--ignore', '-i', multiple=True, 
              help='Additional patterns to ignore (can be used multiple times)')
@click.option('--force', '-f', is_flag=True, 
              help='Overwrite existing files without prompting')
@click.option('--open-browser', '--open', is_flag=True,
              help='Open generated HTML file in browser (HTML output only)')
@click.option('--preview', '-p', is_flag=True, 
              help='Preview the generated documentation without saving')
@click.pass_context
def generate(ctx, path: Path, output: Optional[Path], format: str, theme: str, title: Optional[str], 
            ignore: tuple, force: bool, open_browser: bool, preview: bool):
    """
    Generate documentation from codebase analysis (default command).
    
    Analyzes the codebase and generates comprehensive documentation
    in markdown, HTML, or both formats.
    
    PATH: Path to the codebase to analyze (default: current directory)
    """
    verbose = ctx.obj['verbose']
    config_path = ctx.obj['config']
    
    # Print banner
    if not preview:
        if format == 'html':
            click.echo("🌐 DocGenie - HTML Documentation Generator")
        elif format == 'both':
            click.echo("📚 DocGenie - Multi-format Documentation Generator")
        else:
            click.echo("🧞 DocGenie - Auto-documentation tool")
        click.echo("=" * 50)
    
    try:
        # Load configuration
        if config_path:
            config_obj = load_config(config_path.parent, config_path)
        else:
            config_obj = load_config(path)
        
        # Override config with command line arguments
        if output is not None:
            config_obj.set('output', 'directory', str(output.parent) if output.parent != Path('.') else 'docs')
            config_obj.set('output', 'filename', output.name if not output.is_dir() else None)
        if title is not None:
            config_obj.set('generation', 'title', title)
        if theme != 'default':
            config_obj.set('output', 'theme', theme)
        if force:
            config_obj.set('generation', 'force_overwrite', True)
        if open_browser:
            config_obj.set('generation', 'open_browser', True)
        if verbose:
            config_obj.set('generation', 'verbose', True)
        
        # Get final configuration values
        verbose = config_obj.get('generation', 'verbose', verbose)
        force = config_obj.get('generation', 'force_overwrite', force)
        open_browser = config_obj.get('generation', 'open_browser', open_browser)
        
        # Initialize analyzer
        if verbose:
            click.echo(f"📁 Analyzing codebase at: {path.resolve()}")
        
        analyzer = CodebaseAnalyzer(str(path), list(ignore), config=config_obj)
        
        # Perform analysis
        with click.progressbar(length=100, label='Analyzing codebase') as bar:
            analysis_data = analyzer.analyze()
            bar.update(100)
        
        if verbose:
            click.echo(f"✅ Analysis complete!")
            click.echo(f"   Files analyzed: {analysis_data['files_analyzed']}")
            click.echo(f"   Languages found: {', '.join(analysis_data['languages'].keys())}")
            click.echo(f"   Functions found: {len(analysis_data['functions'])}")
            click.echo(f"   Classes found: {len(analysis_data['classes'])}")
        
        # Determine output paths and formats
        outputs = []
        if format in ['markdown', 'both']:
            if not output:
                md_output = config_obj.get_output_path(path, 'markdown')
            elif output.is_dir():
                md_output = output / 'README.md'
            else:
                md_output = output if str(output).endswith('.md') else output.with_suffix('.md')
            outputs.append(('markdown', md_output))
        
        if format in ['html', 'both']:
            if not output:
                html_output = config_obj.get_output_path(path, 'html')
            elif output.is_dir():
                html_output = output / 'docs.html'
            else:
                html_output = output if str(output).endswith('.html') else output.with_suffix('.html')
            outputs.append(('html', html_output))
        
        # Check if files exist and prompt if not forced
        if not preview and not force:
            for output_format, output_path in outputs:
                if output_path.exists():
                    file_type = "README.md" if output_format == 'markdown' else "HTML documentation"
                    if not click.confirm(f"{file_type} already exists at {output_path}. Overwrite?"):
                        click.echo("❌ Operation cancelled.")
                        sys.exit(1)
        
        # Generate documentation
        if verbose:
            click.echo("📝 Generating documentation...")
        
        for output_format, output_path in outputs:
            if output_format == 'markdown':
                generator = ReadmeGenerator()
                content = generator.generate(analysis_data, None if preview else str(output_path))
                
                if preview:
                    click.echo("\n" + "=" * 60)
                    click.echo("PREVIEW - Generated README.md content:")
                    click.echo("=" * 60)
                    click.echo(content)
                    click.echo("=" * 60)
                else:
                    click.echo(f"✅ README generated: {output_path}")
            
            elif output_format == 'html':
                html_generator = HTMLGenerator()
                content = html_generator.generate_from_analysis(analysis_data, None if preview else str(output_path))
                
                if preview:
                    click.echo("\n" + "=" * 60)
                    click.echo("PREVIEW - Generated HTML documentation:")
                    click.echo("=" * 60)
                    click.echo("HTML document structure generated with:")
                    click.echo("- Modern responsive design")
                    click.echo("- Syntax highlighted code blocks")
                    click.echo("- Interactive table of contents")
                    click.echo("- Mobile-friendly layout")
                    click.echo("=" * 60)
                else:
                    click.echo(f"✅ HTML documentation generated: {output_path}")
                    click.echo(f"📊 File size: {_format_file_size(len(content))}")
                    
                    # Open in browser if requested and not previewing
                    if open_browser and format in ['html', 'both']:
                        import webbrowser
                        file_url = f"file://{output_path.resolve()}"
                        webbrowser.open(file_url)
                        click.echo(f"🌐 Opened in browser: {file_url}")
                    else:
                        click.echo(f"💡 Open {output_path} in your browser to view")
        
        # Show summary (only if not previewing)
        if not preview:
            click.echo("\n📊 Summary:")
            click.echo(f"   Project: {analysis_data.get('root_path', str(path)).split('/')[-1]}")
            click.echo(f"   Type: {analysis_data.get('main_language', 'Unknown').title()} project")
            click.echo(f"   Files: {analysis_data['files_analyzed']}")
            click.echo(f"   Languages: {len(analysis_data['languages'])}")
            click.echo(f"   Format(s): {format}")
            
            if analysis_data.get('git_info', {}).get('remote_url'):
                click.echo(f"   Repository: {analysis_data['git_info']['remote_url']}")
    
    except KeyboardInterrupt:
        click.echo("\n❌ Operation cancelled by user.")
        sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('readme_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output path for the HTML file (default: docs.html in the same directory)')
@click.option('--theme', '-t', type=click.Choice(['default', 'dark', 'minimal']), default='default',
              help='HTML theme style')
@click.option('--title', type=str, 
              help='Custom title for the HTML documentation')
@click.option('--force', '-f', is_flag=True, 
              help='Overwrite existing HTML file without prompting')
@click.option('--open-browser', '--open', is_flag=True,
              help='Open the generated HTML file in the default browser')
@click.option('--preview', '-p', is_flag=True, 
              help='Preview the generated HTML without saving')
@click.pass_context
def convert(ctx, readme_path: Path, output: Optional[Path], theme: str, title: Optional[str], 
           force: bool, open_browser: bool, preview: bool):
    """
    Convert a README.md file to HTML documentation.
    
    Takes an existing README.md file and converts it to beautiful HTML
    documentation with syntax highlighting and responsive design.
    
    README_PATH: Path to the README.md file to convert
    """
    verbose = ctx.obj['verbose']
    config_path = ctx.obj['config']
    
    click.echo("🌐 DocGenie HTML Documentation Converter")
    click.echo("=" * 45)
    
    try:
        # Validate input
        if not readme_path.name.endswith('.md'):
            click.echo("❌ Error: Input must be a markdown (.md) file")
            sys.exit(1)
        
        # Load configuration
        if config_path:
            config_obj = load_config(config_path.parent, config_path)
        else:
            config_obj = load_config(readme_path.parent)
        
        # Override config with command line arguments
        if output is not None:
            config_obj.set('output', 'directory', str(output.parent) if output.parent != Path('.') else 'docs')
            config_obj.set('output', 'filename', output.name)
        if title is not None:
            config_obj.set('generation', 'title', title)
        if theme != 'default':
            config_obj.set('output', 'theme', theme)
        if force:
            config_obj.set('generation', 'force_overwrite', True)
        if open_browser:
            config_obj.set('generation', 'open_browser', True)
        if verbose:
            config_obj.set('generation', 'verbose', True)
        
        # Get final configuration values
        verbose = config_obj.get('generation', 'verbose', verbose)
        force = config_obj.get('generation', 'force_overwrite', force)
        open_browser = config_obj.get('generation', 'open_browser', open_browser)
        
        # Determine output path
        if not output:
            output = config_obj.get_output_path(readme_path, 'readme')
        elif output.is_dir():
            filename = config_obj.get('output', 'filename', 'docs.html')
            output = output / filename
        
        # Check if output file exists (skip if previewing)
        if not preview and output.exists() and not force:
            if not click.confirm(f"HTML file already exists at {output}. Overwrite?"):
                click.echo("❌ Operation cancelled.")
                sys.exit(1)
        
        # Create output directory if it doesn't exist (skip if previewing)
        if not preview:
            output.parent.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            click.echo(f"📖 Reading README from: {readme_path}")
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # Extract project name from title or use custom title
        project_name = config_obj.get('generation', 'title') or title or _extract_title_from_markdown(readme_content) or readme_path.stem
        
        if verbose:
            click.echo(f"🔄 Converting markdown to HTML...")
        
        html_generator = HTMLGenerator()
        html_content = html_generator.generate_from_readme(
            readme_content, None if preview else str(output), project_name
        )
        
        if preview:
            click.echo("\n" + "=" * 60)
            click.echo("PREVIEW - Generated HTML documentation:")
            click.echo("=" * 60)
            click.echo("HTML document structure generated with:")
            click.echo("- Modern responsive design")
            click.echo("- Syntax highlighted code blocks")
            click.echo("- Interactive table of contents")
            click.echo("- Mobile-friendly layout")
            click.echo(f"- Theme: {theme}")
            click.echo("=" * 60)
        else:
            click.echo(f"✅ HTML documentation generated: {output}")
            click.echo(f"📊 File size: {_format_file_size(len(html_content))}")
            
            # Open in browser if requested
            if open_browser:
                import webbrowser
                file_url = f"file://{output.resolve()}"
                webbrowser.open(file_url)
                click.echo(f"🌐 Opened in browser: {file_url}")
            else:
                click.echo(f"💡 Open {output} in your browser to view the documentation")
    
    except KeyboardInterrupt:
        click.echo("\n❌ Operation cancelled by user.")
        sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path), default='.')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'text']), default='text',
              help='Output format for analysis results')
@click.pass_context
def analyze(ctx, path: Path, format: str):
    """
    Analyze a codebase and output detailed information.
    
    This command performs the same analysis as the generate command but outputs
    the raw analysis data instead of generating documentation.
    
    PATH: Path to the codebase to analyze (default: current directory)
    """
    verbose = ctx.obj['verbose']
    config_path = ctx.obj['config']
    
    try:
        # Load configuration
        if config_path:
            config_obj = load_config(config_path.parent, config_path)
        else:
            config_obj = load_config(path)
        
        analyzer = CodebaseAnalyzer(str(path), config=config_obj)
        analysis_data = analyzer.analyze()
        
        if format == 'json':
            click.echo(json.dumps(analysis_data, indent=2, default=str))
        elif format == 'yaml':
            click.echo(yaml.dump(analysis_data, default_flow_style=False))
        else:  # text format
            click.echo("🔍 Codebase Analysis Results")
            click.echo("=" * 30)
            click.echo(f"Path: {analysis_data['root_path']}")
            click.echo(f"Files analyzed: {analysis_data['files_analyzed']}")
            click.echo(f"Languages: {', '.join(analysis_data['languages'].keys())}")
            click.echo(f"Functions: {len(analysis_data['functions'])}")
            click.echo(f"Classes: {len(analysis_data['classes'])}")
            
            if analysis_data['dependencies']:
                click.echo("\nDependencies:")
                for dep_file, deps in analysis_data['dependencies'].items():
                    click.echo(f"  {dep_file}: {len(deps) if isinstance(deps, list) else sum(len(d) for d in deps.values()) if isinstance(deps, dict) else 0} dependencies")
            
            if analysis_data['git_info']:
                click.echo(f"\nGit info:")
                git_info = analysis_data['git_info']
                if 'repo_name' in git_info:
                    click.echo(f"  Repository: {git_info['repo_name']}")
                if 'current_branch' in git_info:
                    click.echo(f"  Branch: {git_info['current_branch']}")
                if 'contributor_count' in git_info:
                    click.echo(f"  Contributors: {git_info['contributor_count']}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output path for config file (default: .docgenie.yml in current directory)')
@click.pass_context
def config(ctx, output: Optional[Path]):
    """Create a sample configuration file."""
    verbose = ctx.obj['verbose']
    
    click.echo("📋 DocGenie Configuration Initializer")
    click.echo("=" * 40)
    
    if not output:
        output = Path.cwd() / '.docgenie.yml'
    
    if output.exists():
        if not click.confirm(f"Configuration file already exists at {output}. Overwrite?"):
            click.echo("❌ Operation cancelled.")
            return
    
    try:
        config_obj = load_config()
        created_path = config_obj.create_sample_config(output)
        click.echo(f"✅ Configuration file created: {created_path}")
        click.echo(f"💡 Edit the file to customize DocGenie's behavior")
        click.echo(f"📖 Use --config {created_path} to use this configuration")
    except Exception as e:
        click.echo(f"❌ Error creating configuration file: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()


@cli.command()
def init():
    """
    Initialize a new project with a basic README template.
    
    Creates a basic README.md file with standard sections that can be
    customized manually.
    """
    template_content = """# Project Name

Brief description of your project.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Add installation instructions here
```

## Usage

```bash
# Add usage examples here
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.
"""
    
    readme_path = Path('README.md')
    
    if readme_path.exists():
        if not click.confirm("README.md already exists. Overwrite?"):
            click.echo("❌ Operation cancelled.")
            return
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    click.echo("✅ Basic README.md template created!")
    click.echo("💡 Tip: Run 'docgenie generate' to create comprehensive documentation based on your code.")


def _extract_title_from_markdown(content: str) -> Optional[str]:
    """Extract the first heading from markdown content."""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return None


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# Make generate the default command when called directly
if __name__ == '__main__':
    cli()