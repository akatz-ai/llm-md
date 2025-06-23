import click
from pathlib import Path
from typing import Optional
from importlib.metadata import version, PackageNotFoundError
from .scanner import RepoScanner
from .parser import GitignoreParser, LlmMdParser
from .generator import MarkdownGenerator

try:
    __version__ = version('llmd')
except PackageNotFoundError:
    __version__ = 'dev'


@click.command()
@click.version_option(version=__version__, prog_name='llmd')
@click.argument('repo_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('-o', '--output', type=click.Path(path_type=Path), default='llm-context.md',
              help='Output markdown file path (default: llm-context.md)')
@click.option('-c', '--config', type=click.Path(exists=True, path_type=Path),
              help='Override path to llm.md configuration file (default: auto-detect in repo root)')
@click.option('-i', '--include', multiple=True, help='Include files matching these patterns (can be specified multiple times)')
@click.option('-e', '--exclude', multiple=True, help='Exclude files matching these patterns (can be specified multiple times)')
@click.option('-O', '--only', multiple=True, help='Only include files matching these patterns, ignoring all exclusions (can be specified multiple times)')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show which files would be included without generating output')
def main(repo_path: Path, output: Path, config: Optional[Path], include: tuple, exclude: tuple, only: tuple, verbose: bool, dry_run: bool):
    """Generate LLM context from a GitHub repository.
    
    This tool scans through files in a repository and creates a single markdown
    file containing all relevant code, with a table of contents for easy navigation.
    
    Files are filtered based on .gitignore rules and optional llm.md configuration.
    If an llm.md file exists in the repository root, it will be used automatically
    unless overridden with the -c option.
    """
    if not dry_run:
        click.echo(f"Scanning repository: {repo_path}")
    
    # Initialize parsers
    gitignore_parser = GitignoreParser(repo_path)
    
    # Determine which llm.md config to use
    if config:
        # User explicitly provided a config file
        llm_config_path = config
        if not dry_run:
            click.echo(f"Using specified llm.md config: {llm_config_path}")
    else:
        # Check if llm.md exists in the repo root
        default_llm_path = repo_path / 'llm.md'
        if default_llm_path.exists():
            llm_config_path = default_llm_path
            if not dry_run:
                click.echo(f"Found llm.md in repository root: {llm_config_path}")
        else:
            llm_config_path = None
            if verbose and not dry_run:
                click.echo("No llm.md file found in repository root")
    
    llm_parser = LlmMdParser(llm_config_path, cli_include=list(include), cli_exclude=list(exclude), cli_only=list(only))
    
    # Show CLI pattern usage
    if only and verbose and not dry_run:
        click.echo(f"Using CLI only patterns: {', '.join(only)}")
    if include and verbose and not dry_run:
        click.echo(f"Using CLI include patterns: {', '.join(include)}")
    if exclude and verbose and not dry_run:
        click.echo(f"Using CLI exclude patterns: {', '.join(exclude)}")
    
    # Create scanner with filtering rules
    # In dry-run mode, suppress verbose output from scanner since we'll print files ourselves
    scanner = RepoScanner(repo_path, gitignore_parser, llm_parser, verbose=verbose and not dry_run)
    
    # Scan files
    files = scanner.scan()
    
    if not files:
        click.echo("No files found matching the criteria.", err=True)
        return
    
    if dry_run:
        # In dry-run mode, just output the list of files that would be included
        for file in files:
            click.echo(f"+{file.relative_to(repo_path)}")
        return
    
    click.echo(f"Found {len(files)} files to process")
    
    # Generate markdown
    generator = MarkdownGenerator()
    content = generator.generate(files, repo_path)
    
    # Write output
    output.write_text(content, encoding='utf-8')
    click.echo(f"✓ Generated context file: {output}")
    
    if verbose:
        click.echo(f"  Total size: {len(content):,} characters")
        click.echo(f"  Files included: {len(files)}")


if __name__ == '__main__':
    main()