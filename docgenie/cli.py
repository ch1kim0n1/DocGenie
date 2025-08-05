"""
Command-line interface for DocGenie.
"""

import sys
import click
from pathlib import Path
from typing import Optional

from .core import CodebaseAnalyzer
from .generator import ReadmeGenerator
from .html_generator import HTMLGenerator


@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path), default='.')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output path for the generated documentation (default: README.md or docs.html in the analyzed directory)')
@click.option('--format', '--fmt', type=click.Choice(['markdown', 'html', 'both']), default='markdown',
              help='Output format: markdown (README.md), html (HTML documentation), or both')
@click.option('--ignore', '-i', multiple=True, 
              help='Additional patterns to ignore (can be used multiple times)')
@click.option('--force', '-f', is_flag=True, 
              help='Overwrite existing files without prompting')
@click.option('--preview', '-p', is_flag=True, 
              help='Preview the generated documentation without saving')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
@click.version_option(version='1.0.0', prog_name='DocGenie')
def main(path: Path, output: Optional[Path], format: str, ignore: tuple, force: bool, preview: bool, verbose: bool):
    """
    DocGenie - Auto-documentation tool for codebases.
    
    Generate comprehensive documentation for any codebase by analyzing
    source code, dependencies, and project structure. Output as README.md,
    HTML documentation, or both formats.
    
    PATH: Path to the codebase to analyze (default: current directory)
    """
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
        # Initialize analyzer
        if verbose:
            click.echo(f"📁 Analyzing codebase at: {path.resolve()}")
        
        analyzer = CodebaseAnalyzer(str(path), list(ignore))
        
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
                md_output = path / 'README.md'
            elif output.is_dir():
                md_output = output / 'README.md'
            else:
                md_output = output if str(output).endswith('.md') else output.with_suffix('.md')
            outputs.append(('markdown', md_output))
        
        if format in ['html', 'both']:
            if not output:
                html_output = path / 'docs.html'
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
                    # Show a snippet of HTML for preview
                    lines = content.split('\n')
                    preview_lines = []
                    in_body = False
                    for line in lines:
                        if '<body>' in line:
                            in_body = True
                        if in_body and ('</body>' in line or len(preview_lines) > 50):
                            break
                        if in_body:
                            preview_lines.append(line)
                    
                    click.echo("HTML document structure generated with:")
                    click.echo("- Modern responsive design")
                    click.echo("- Syntax highlighted code blocks")
                    click.echo("- Interactive table of contents")
                    click.echo("- Mobile-friendly layout")
                    click.echo("=" * 60)
                else:
                    click.echo(f"✅ HTML documentation generated: {output_path}")
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


@click.group()
def cli():
    """DocGenie - Auto-documentation tool for codebases."""
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path), default='.')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'text']), default='text',
              help='Output format for analysis results')
def analyze(path: Path, format: str):
    """
    Analyze a codebase and output detailed information.
    
    This command performs the same analysis as the main command but outputs
    the raw analysis data instead of generating a README.
    """
    import json
    import yaml
    
    try:
        analyzer = CodebaseAnalyzer(str(path))
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
        sys.exit(1)


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
    click.echo("💡 Tip: Run 'docgenie .' to generate a comprehensive README based on your code.")


# Add the subcommands to the main CLI
cli.add_command(analyze)
cli.add_command(init)

# Make main the default command when called directly
if __name__ == '__main__':
    main()