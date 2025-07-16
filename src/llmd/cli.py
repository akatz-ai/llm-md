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
# Mode selection options (mutually exclusive)
@click.option('-w', '--whitelist', multiple=True, help='Use whitelist mode with specified patterns')
@click.option('-b', '--blacklist', multiple=True, help='Use blacklist mode with specified patterns')
# Pattern refinement options (only valid with mode flags)
@click.option('-i', '--include', multiple=True, help='Include files matching these patterns (can be specified multiple times)')
@click.option('-e', '--exclude', multiple=True, help='Exclude files matching these patterns (can be specified multiple times)')
@click.option('-O', '--only', multiple=True, help='Only include files matching these patterns, ignoring all exclusions (can be specified multiple times)')
# Behavior control options
@click.option('--include-gitignore/--exclude-gitignore', default=None, 
              help='Include or exclude files matched by .gitignore (default: exclude)')
@click.option('--no-gitignore', 'include_gitignore_alias', is_flag=True, 
              help='Same as --include-gitignore')
@click.option('--include-hidden/--exclude-hidden', default=None,
              help='Include or exclude hidden files starting with . (default: exclude)')
@click.option('--with-hidden', 'include_hidden_alias', is_flag=True,
              help='Same as --include-hidden')
@click.option('--include-binary/--exclude-binary', default=None,
              help='Include or exclude binary files (default: exclude)')
@click.option('--with-binary', 'include_binary_alias', is_flag=True,
              help='Same as --include-binary')
# Utility options
@click.option('-q', '--quiet', is_flag=True, help='Suppress non-error output')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show which files would be included without generating output')
def main(repo_path: Path, output: Path, config: Optional[Path], whitelist: tuple, blacklist: tuple, 
         include: tuple, exclude: tuple, only: tuple, 
         include_gitignore: Optional[bool], include_gitignore_alias: bool,
         include_hidden: Optional[bool], include_hidden_alias: bool,
         include_binary: Optional[bool], include_binary_alias: bool,
         quiet: bool, verbose: bool, dry_run: bool):
    """Generate LLM context from a GitHub repository.
    
    This tool scans through files in a repository and creates a single markdown
    file containing all relevant code, with a table of contents for easy navigation.
    
    Files are filtered based on .gitignore rules and optional llm.md configuration.
    If an llm.md file exists in the repository root, it will be used automatically
    unless overridden with the -c option.
    """
    # Validation: mode flags are mutually exclusive
    if whitelist and blacklist:
        raise click.UsageError("Options -w/--whitelist and -b/--blacklist are mutually exclusive.")
    
    # Validation: pattern refinement flags require mode flags
    if (include or exclude) and not (whitelist or blacklist):
        raise click.UsageError("Pattern refinement flags (-i/--include and -e/--exclude) require mode flags (-w/--whitelist or -b/--blacklist).")
    
    # Handle aliases for behavior flags
    final_include_gitignore = include_gitignore
    if include_gitignore_alias:
        final_include_gitignore = True
        
    final_include_hidden = include_hidden 
    if include_hidden_alias:
        final_include_hidden = True
        
    final_include_binary = include_binary
    if include_binary_alias:
        final_include_binary = True
    
    # Determine if CLI mode is being used (overrides llm.md)
    cli_mode = None
    cli_patterns = []
    if whitelist:
        cli_mode = "WHITELIST"
        cli_patterns = list(whitelist)
    elif blacklist:
        cli_mode = "BLACKLIST"
        cli_patterns = list(blacklist)
    
    # Create behavior overrides dict for CLI flags
    cli_behavior_overrides = {}
    if final_include_gitignore is not None:
        cli_behavior_overrides['respect_gitignore'] = not final_include_gitignore
    if final_include_hidden is not None:
        cli_behavior_overrides['include_hidden'] = final_include_hidden
    if final_include_binary is not None:
        cli_behavior_overrides['include_binary'] = final_include_binary
    
    if not dry_run and not quiet:
        click.echo(f"Scanning repository: {repo_path}")
    
    # Initialize parsers
    gitignore_parser = GitignoreParser(repo_path)
    
    # Determine which llm.md config to use (only if not using CLI mode override)
    llm_config_path = None
    if cli_mode:
        # CLI mode completely overrides llm.md
        llm_config_path = None
        if verbose and not dry_run and not quiet:
            click.echo(f"Using CLI {cli_mode.lower()} mode, ignoring llm.md configuration")
    else:
        # Use existing config file logic
        if config:
            # User explicitly provided a config file
            llm_config_path = config
            if not dry_run and not quiet:
                click.echo(f"Using specified llm.md config: {llm_config_path}")
        else:
            # Check if llm.md exists in the repo root
            default_llm_path = repo_path / 'llm.md'
            if default_llm_path.exists():
                llm_config_path = default_llm_path
                if not dry_run and not quiet:
                    click.echo(f"Found llm.md in repository root: {llm_config_path}")
            else:
                llm_config_path = None
                if verbose and not dry_run and not quiet:
                    click.echo("No llm.md file found in repository root")
    
    # Determine default_mode for when no llm.md exists and no CLI mode
    default_mode = "BLACKLIST" if llm_config_path is None and cli_mode is None else None
    
    # Create LlmMdParser with CLI override support
    if cli_mode:
        # CLI mode override - pass CLI mode and behavior overrides
        llm_parser = LlmMdParser(
            config_path=None,  # Ignore config file completely
            cli_include=list(include), 
            cli_exclude=list(exclude), 
            cli_only=list(only),
            cli_mode=cli_mode,
            cli_patterns=cli_patterns,
            cli_behavior_overrides=cli_behavior_overrides
        )
    else:
        # Legacy behavior - use existing constructor
        llm_parser = LlmMdParser(
            llm_config_path, 
            cli_include=list(include), 
            cli_exclude=list(exclude), 
            cli_only=list(only), 
            default_mode=default_mode
        )
    
    # Show CLI pattern usage
    if only and verbose and not dry_run and not quiet:
        click.echo(f"Using CLI only patterns: {', '.join(only)}")
    if include and verbose and not dry_run and not quiet:
        click.echo(f"Using CLI include patterns: {', '.join(include)}")
    if exclude and verbose and not dry_run and not quiet:
        click.echo(f"Using CLI exclude patterns: {', '.join(exclude)}")
    
    # Create scanner with filtering rules
    # In dry-run mode or quiet mode, suppress verbose output from scanner
    scanner = RepoScanner(repo_path, gitignore_parser, llm_parser, verbose=verbose and not dry_run and not quiet)
    
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
    
    if not quiet:
        click.echo(f"Found {len(files)} files to process")
    
    # Generate markdown
    generator = MarkdownGenerator()
    content = generator.generate(files, repo_path)
    
    # Write output
    output.write_text(content, encoding='utf-8')
    if not quiet:
        click.echo(f"✓ Generated context file: {output}")
    
    if verbose and not quiet:
        click.echo(f"  Total size: {len(content):,} characters")
        click.echo(f"  Files included: {len(files)}")


if __name__ == '__main__':
    main()