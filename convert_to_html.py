#!/usr/bin/env python3
"""
Standalone HTML Documentation Converter for DocGenie.

This script can convert existing README.md files to beautiful HTML documentation
or generate HTML documentation directly from codebase analysis.
"""

import sys
import click
from pathlib import Path
from typing import Optional

# Add the parent directory to the Python path to import from docgenie
sys.path.insert(0, str(Path(__file__).parent))

from docgenie.core import CodebaseAnalyzer
from docgenie.html_generator import HTMLGenerator
from docgenie.generator import ReadmeGenerator
from docgenie.config import load_config


@click.command()
@click.argument('input_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output path for the HTML file (default: docs.html in the same directory)')
@click.option('--source', '-s', type=click.Choice(['readme', 'codebase']), default='readme',
              help='Source type: "readme" to convert existing README.md, "codebase" to analyze code')
@click.option('--title', '-t', type=str, 
              help='Custom title for the HTML documentation')
@click.option('--force', '-f', is_flag=True, 
              help='Overwrite existing HTML file without prompting')
@click.option('--open-browser', '--open', is_flag=True,
              help='Open the generated HTML file in the default browser')
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
def convert_to_html(input_path: Path, output: Optional[Path], source: str, title: Optional[str], 
                   force: bool, open_browser: bool, verbose: bool, config: Optional[Path]):
    """
    Convert README.md to HTML documentation or generate HTML from codebase analysis.
    
    INPUT_PATH: Path to README.md file or codebase directory
    """
    
    click.echo("🌐 DocGenie HTML Documentation Converter")
    click.echo("=" * 45)
    
    try:        # Load configuration
        if config:
            # Load config from specified file
            config_obj = load_config(config.parent, config)
        else:
            # Load config from input path directory
            if source == 'readme':
                config_obj = load_config(input_path.parent)
            else:
                config_obj = load_config(input_path)
        
        # Override config with command line arguments
        if output is not None:
            config_obj.set('output', 'directory', str(output.parent) if output.parent != Path('.') else 'docs')
            config_obj.set('output', 'filename', output.name)
        if title is not None:
            config_obj.set('generation', 'title', title)
        if force:
            config_obj.set('generation', 'force_overwrite', True)
        if open_browser:
            config_obj.set('generation', 'open_browser', True)
        if verbose:
            config_obj.set('generation', 'verbose', True)
        
        # Get final configuration values
        verbose = config_obj.get('generation', 'verbose', False)
        force = config_obj.get('generation', 'force_overwrite', False)
        open_browser = config_obj.get('generation', 'open_browser', False)
        
        html_generator = HTMLGenerator()
        
        # Determine output path using config
        if not output:
            output = config_obj.get_output_path(input_path, source)
        elif output.is_dir():
            filename = config_obj.get('output', 'filename', 'docs.html')
            output = output / filename
          # Check if output file exists
        if output.exists() and not force:
            if not click.confirm(f"HTML file already exists at {output}. Overwrite?"):
                click.echo("❌ Operation cancelled.")
                sys.exit(1)
        
        # Create output directory if it doesn't exist
        output.parent.mkdir(parents=True, exist_ok=True)
        
        if source == 'readme':
            # Convert existing README.md to HTML
            if not input_path.is_file() or not input_path.name.endswith('.md'):
                click.echo("❌ Error: Input must be a markdown (.md) file when using --source readme")
                sys.exit(1)
            
            if verbose:
                click.echo(f"📖 Reading README from: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
              # Extract project name from title or use custom title
            project_name = config_obj.get('generation', 'title') or title or _extract_title_from_markdown(readme_content) or input_path.stem
            
            if verbose:
                click.echo(f"🔄 Converting markdown to HTML...")
            
            html_content = html_generator.generate_from_readme(
                readme_content, str(output), project_name
            )
            
        else:
            # Generate HTML from codebase analysis
            if not input_path.is_dir():
                click.echo("❌ Error: Input must be a directory when using --source codebase")
                sys.exit(1)
            
            if verbose:
                click.echo(f"🔍 Analyzing codebase at: {input_path}")
            
            analyzer = CodebaseAnalyzer(str(input_path), config=config_obj)
            
            with click.progressbar(length=100, label='Analyzing codebase') as bar:
                analysis_data = analyzer.analyze()
                bar.update(100)
            
            if verbose:
                click.echo(f"📝 Generating HTML documentation...")
            
            html_content = html_generator.generate_from_analysis(analysis_data, str(output))
        
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


@click.group()
def cli():
    """DocGenie HTML Documentation Tools."""
    pass


@cli.command()
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output path for config file (default: .docgenie.yml in current directory)')
def init_config(output: Optional[Path]):
    """Create a sample configuration file."""
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


@cli.command()
@click.argument('readme_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path))
@click.option('--title', '-t', type=str)
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to configuration file')
@click.option('--theme', type=click.Choice(['default', 'dark', 'minimal']), default='default',
              help='HTML theme style')
def readme_to_html(readme_path: Path, output: Optional[Path], title: Optional[str], theme: str, config: Optional[Path]):
    """Convert a README.md file to HTML documentation."""    # Load configuration
    if config:
        config_obj = load_config(config.parent, config)
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
    
    # This is a simplified version of the main convert command
    # focused specifically on README conversion
    
    if not readme_path.name.endswith('.md'):
        click.echo("❌ Error: Input must be a markdown (.md) file")
        sys.exit(1)
    
    if not output:
        output = config_obj.get_output_path(readme_path, 'readme')
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    project_name = config_obj.get('generation', 'title') or title or _extract_title_from_markdown(content) or readme_path.stem
    
    html_generator = HTMLGenerator()
    html_generator.generate_from_readme(content, str(output), project_name)
    
    click.echo(f"✅ Converted {readme_path} → {output}")


@cli.command()
@click.argument('codebase_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path))
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to configuration file')
def codebase_to_html(codebase_path: Path, output: Optional[Path], config: Optional[Path]):
    """Generate HTML documentation from codebase analysis."""
      # Load configuration
    if config:
        config_obj = load_config(config.parent, config)
    else:
        config_obj = load_config(codebase_path)
    
    if not codebase_path.is_dir():
        click.echo("❌ Error: Input must be a directory")
        sys.exit(1)
    
    if not output:
        output = config_obj.get_output_path(codebase_path, 'codebase')
    
    analyzer = CodebaseAnalyzer(str(codebase_path), config=config_obj)
    analysis_data = analyzer.analyze()
    
    html_generator = HTMLGenerator()
    html_generator.generate_from_analysis(analysis_data, str(output))
    
    click.echo(f"✅ Generated documentation for {codebase_path} → {output}")


# Add subcommands to the CLI group
cli.add_command(init_config)
cli.add_command(readme_to_html)
cli.add_command(codebase_to_html)

# Make convert_to_html the default command when called directly
if __name__ == '__main__':
    convert_to_html()
