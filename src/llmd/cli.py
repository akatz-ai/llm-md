import click
from pathlib import Path
from typing import Optional
import re
import subprocess
import tempfile
import shutil
from importlib.metadata import version, PackageNotFoundError
from .scanner import RepoScanner
from .parser import GitignoreParser, LlmMdParser, PatternSequence
from .generator import MarkdownGenerator

# Global variable for test support - this is a hack but necessary for Click testing
_test_args_override = None

try:
    __version__ = version('llmd')
except PackageNotFoundError:
    __version__ = 'dev'


def build_pattern_sequence_from_raw_args():
    """Extract pattern sequence by parsing raw arguments to preserve order."""
    import sys
    global _test_args_override
    
    pattern_sequence = PatternSequence()
    
    # Use test override if available (for testing)
    if _test_args_override is not None:
        argv = _test_args_override
    else:
        # Parse from sys.argv to preserve order
        argv = sys.argv[1:]  # Skip script name
    
    # Special handling for test environments where sys.argv might not contain test args
    if not argv or ('pytest' in sys.modules and _test_args_override is None):
        # In test environment, we can't rely on sys.argv
        # For now, return None to indicate we should use legacy processing
        return None
    
    i = 0
    while i < len(argv):
        arg = argv[i]
        
        # Check for include patterns
        if arg in ['-i', '--include']:
            if i + 1 < len(argv):
                pattern_sequence.add_pattern('include', argv[i + 1])
                i += 2
            else:
                i += 1
        # Check for exclude patterns  
        elif arg in ['-e', '--exclude']:
            if i + 1 < len(argv):
                pattern_sequence.add_pattern('exclude', argv[i + 1])
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return pattern_sequence if pattern_sequence.has_patterns() else None


def set_test_args(args):
    """Set test arguments override for testing purposes."""
    global _test_args_override
    _test_args_override = args


def clear_test_args():
    """Clear test arguments override."""
    global _test_args_override
    _test_args_override = None


# Template content for init command
DEFAULT_BLACKLIST_TEMPLATE = """BLACKLIST:
tests/
node_modules/
__pycache__/
.git/
dist/
build/
coverage/
*.log
*.tmp

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

INCLUDE:
README.md
"""

WHITELIST_TEMPLATE = """WHITELIST:
src/
lib/
*.py
*.js
*.ts
*.md
package.json
pyproject.toml

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

EXCLUDE:
**/__pycache__/
**/*.test.js
**/*.test.py

INCLUDE:
tests/fixtures/
"""

BLACKLIST_TEMPLATE = """BLACKLIST:
tests/
node_modules/
__pycache__/
.git/
dist/
build/
coverage/
*.log
*.tmp
.env
.venv/
venv/

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

INCLUDE:
tests/fixtures/
debug.log
"""

MINIMAL_TEMPLATE = """WHITELIST:
src/

OPTIONS:
output: llm-context.md
"""


def validate_github_url(url: str) -> bool:
    """Validate if the URL is a valid GitHub repository URL."""
    if not url:
        return False
    
    # GitHub HTTPS patterns
    https_patterns = [
        r'^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+(\.git)?/?$',
    ]
    
    # GitHub SSH pattern
    ssh_pattern = r'^git@github\.com:[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+(\.git)?$'
    
    # Check HTTPS patterns
    for pattern in https_patterns:
        if re.match(pattern, url):
            return True
    
    # Check SSH pattern
    if re.match(ssh_pattern, url):
        return True
    
    return False


def clone_github_repo(github_url: str) -> str:
    """Clone a GitHub repository to a temporary directory.
    
    Args:
        github_url: The GitHub repository URL
        
    Returns:
        str: Path to the temporary directory containing the cloned repo
        
    Raises:
        click.ClickException: If cloning fails
    """
    # Check if git is available
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise click.ClickException("Git is not available. Please install Git and ensure it's in your PATH.")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix='llmd_github_')
    
    try:
        # Clone the repository (shallow clone for performance)
        result = subprocess.run([
            'git', 'clone', '--depth', '1', github_url, temp_dir
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                raise click.ClickException(f"Repository not found: {github_url}")
            elif "could not resolve host" in error_msg.lower() or "network" in error_msg.lower():
                raise click.ClickException(f"Network error while cloning repository: {error_msg}")
            else:
                raise click.ClickException(f"Git clone failed: {error_msg}")
        
        return temp_dir
        
    except Exception as e:
        # Clean up on error
        cleanup_temp_repo(temp_dir)
        if isinstance(e, click.ClickException):
            raise
        else:
            raise click.ClickException(f"Failed to clone repository: {str(e)}")


def cleanup_temp_repo(temp_dir: str) -> None:
    """Clean up a temporary repository directory.
    
    Args:
        temp_dir: Path to the temporary directory to clean up
    """
    try:
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
    except Exception:
        # Silently ignore cleanup errors - they're not critical
        pass


class FlexibleGroup(click.Group):
    def resolve_command(self, ctx, args):
        # Check if first argument is a directory path
        if args and Path(args[0]).exists() and Path(args[0]).is_dir():
            # Create a dummy command that will invoke the main callback with the path
            dummy_cmd = PathCommand(name=args[0], callback=self.callback, parent=self)
            return args[0], dummy_cmd, args[1:]
        
        # Otherwise use normal command resolution
        return super().resolve_command(ctx, args)


class PathCommand(click.Command):
    """A dummy command that handles directory path arguments"""
    
    def __init__(self, name, callback, parent):
        # Initialize as a command with the same parameters as the parent
        super().__init__(name=name, callback=callback, params=parent.params.copy())
        self.parent_group = parent
    
    def make_context(self, info_name, args, parent=None, **extra):
        # Create context but pass the path as an extra arg
        ctx = super().make_context(info_name, args, parent, **extra)
        # Put the path (command name) in args so main() can access it
        ctx.args = [info_name] + ctx.args
        return ctx

@click.group(cls=FlexibleGroup, invoke_without_command=True, context_settings={'allow_extra_args': True, 'allow_interspersed_args': False})
@click.version_option(version=__version__, prog_name='llmd')
@click.pass_context
@click.option('-o', '--output', type=click.Path(path_type=Path), default='./llm-context.md',
              help='Output file or directory path (default: ./llm-context.md)')
# GitHub remote repository option
@click.option('--github', 'github_url', help='Clone and process GitHub repository from URL')
# Mode selection options (mutually exclusive)
@click.option('-w', '--whitelist', 'whitelist_patterns', multiple=True, help='Use whitelist mode with specified patterns')
@click.option('-b', '--blacklist', 'blacklist_patterns', multiple=True, help='Use blacklist mode with specified patterns')
# Pattern refinement options (only valid with mode flags)
@click.option('-i', '--include', multiple=True, help='Include files matching these patterns (can be specified multiple times)')
@click.option('-e', '--exclude', multiple=True, help='Exclude files matching these patterns (can be specified multiple times)')
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
def main(ctx, output: Path, github_url: Optional[str], whitelist_patterns: tuple, blacklist_patterns: tuple, 
         include: tuple, exclude: tuple,
         include_gitignore: Optional[bool], include_gitignore_alias: bool,
         include_hidden: Optional[bool], include_hidden_alias: bool,
         include_binary: Optional[bool], include_binary_alias: bool,
         quiet: bool, verbose: bool, dry_run: bool):
    """Generate LLM context from a repository.
    
    PATH: Repository path (default: current directory)
    
    This tool generates consolidated markdown files containing code repository 
    contents for use with Large Language Models (LLMs). It provides flexible 
    file filtering through whitelist/blacklist patterns, respecting gitignore 
    rules and binary file detection by default.
    """
    # If a subcommand is invoked, don't run the main generation logic
    if ctx.invoked_subcommand is not None:
        return
    
    # Handle GitHub repository URL
    temp_repo_dir = None
    try:
        if github_url is not None:
            # GitHub URL was provided, validate it
            if not validate_github_url(github_url):
                raise click.UsageError(f"Invalid GitHub URL: {github_url}")
            
            # Clone the repository
            if not dry_run and not quiet:
                click.echo(f"Cloning GitHub repository: {github_url}")
            
            temp_repo_dir = clone_github_repo(github_url)
            repo_path = Path(temp_repo_dir)
            
            if verbose and not dry_run and not quiet:
                click.echo(f"Repository cloned to: {temp_repo_dir}")
        
        else:
            # Handle repository path from extra args
            extra_args = ctx.args
            if len(extra_args) > 1:
                raise click.UsageError("Too many arguments. Expected at most one repository path.")
            elif len(extra_args) == 1:
                repo_path = Path(extra_args[0])
                if not repo_path.exists():
                    raise click.UsageError(f"Repository path '{repo_path}' does not exist.")
                if not repo_path.is_dir():
                    raise click.UsageError(f"Repository path '{repo_path}' is not a directory.")
            else:
                repo_path = Path('.')
        
        # Validation: mode flags are mutually exclusive
        if whitelist_patterns and blacklist_patterns:
            raise click.UsageError("Options -w/--whitelist and -b/--blacklist are mutually exclusive.")
        
        # Validation: pattern refinement flags require mode flags
        if (include or exclude) and not (whitelist_patterns or blacklist_patterns):
            raise click.UsageError("Pattern refinement options (-e/--exclude and -i/--include) require mode flags (-w/--whitelist or -b/--blacklist).")
        
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
        if whitelist_patterns:
            cli_mode = "WHITELIST"
            cli_patterns = list(whitelist_patterns)
        elif blacklist_patterns:
            cli_mode = "BLACKLIST"
            cli_patterns = list(blacklist_patterns)
        
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
    
        # Extract pattern sequence by parsing raw arguments to preserve order
        pattern_sequence = build_pattern_sequence_from_raw_args()
        
        # Debug: Print pattern sequence if it exists
        if pattern_sequence and pattern_sequence.has_patterns():
            if verbose and not quiet:
                click.echo(f"DEBUG: Using sequential pattern processing with {len(pattern_sequence.patterns)} patterns:")
                for i, p in enumerate(pattern_sequence.patterns):
                    click.echo(f"  [{i}] {p.pattern_type}: {p.pattern}")
        elif verbose and not quiet:
            click.echo("DEBUG: No sequential patterns found, using legacy processing")
        
        # Create LlmMdParser with CLI override support
        if cli_mode:
            # CLI mode override - pass CLI mode and behavior overrides
            llm_parser = LlmMdParser(
                config_path=None,  # Ignore config file completely
                cli_include=list(include), 
                cli_exclude=list(exclude), 
                cli_mode=cli_mode,
                cli_patterns=cli_patterns,
                cli_behavior_overrides=cli_behavior_overrides,
                cli_pattern_sequence=pattern_sequence
            )
        else:
            # Legacy behavior - use existing constructor
            llm_parser = LlmMdParser(
                llm_config_path, 
                cli_include=list(include), 
                cli_exclude=list(exclude), 
                default_mode=default_mode,
                cli_pattern_sequence=pattern_sequence
            )
    
        # Show CLI pattern usage
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
            # Enhanced dry-run output with detailed information
            click.echo("=== DRY RUN - Files that would be included ===")
        
            # Show mode being used
            if cli_mode:
                click.echo(f"Mode: CLI {cli_mode.lower()}")
                if cli_patterns:
                    click.echo(f"Patterns: {', '.join(cli_patterns)}")
            elif llm_config_path:
                click.echo(f"Mode: Configuration from {llm_config_path}")
            else:
                click.echo("Mode: Default (implicit blacklist)")
        
            # Show behavior settings
            settings = []
            if final_include_gitignore is True:
                settings.append("including gitignored files")
            elif final_include_gitignore is False or final_include_gitignore is None:
                settings.append("excluding gitignored files")
            
            if final_include_hidden is True:
                settings.append("including hidden files")
            elif final_include_hidden is False or final_include_hidden is None:
                settings.append("excluding hidden files")
            
            if final_include_binary is True:
                settings.append("including binary files")
            elif final_include_binary is False or final_include_binary is None:
                settings.append("excluding binary files")
            
            if settings:
                click.echo(f"Settings: {', '.join(settings)}")
        
            click.echo(f"\nFiles to include ({len(files)} total):")
            for file in files:
                click.echo(f"  +{file.relative_to(repo_path)}")
        
            return
    
        if not quiet:
            click.echo(f"Found {len(files)} files to process")
    
        # Resolve final output path with precedence: CLI explicit > llm.md output > CLI default
        final_output = output
        
        # Detect if CLI --output was explicitly provided (not the default)
        # Check if output is the default value (can be './llm-context.md' or 'llm-context.md')
        cli_output_explicit = str(output) not in ('./llm-context.md', 'llm-context.md')
        
        if not cli_output_explicit and not cli_mode:
            # CLI output not explicitly provided and not in CLI mode
            # Try to use llm.md output option
            llm_output_path = llm_parser.resolve_output_path()
            if llm_output_path:
                final_output = llm_output_path
                if verbose and not dry_run and not quiet:
                    click.echo(f"Using output path from llm.md: {final_output}")
            elif verbose and not dry_run and not quiet:
                click.echo(f"Using default output path: {final_output}")
        elif verbose and not dry_run and not quiet:
            if cli_output_explicit:
                click.echo(f"Using CLI output path: {final_output}")
            else:
                click.echo(f"CLI mode active, using default output path: {final_output}")
        
        # Generate markdown
        generator = MarkdownGenerator()
        content = generator.generate(files, repo_path)
        
        # Write output
        final_output.write_text(content, encoding='utf-8')
        if not quiet:
            click.echo(f"✓ Generated context file: {final_output}")
        
        if verbose and not quiet:
            click.echo(f"  Total size: {len(content):,} characters")
            click.echo(f"  Files included: {len(files)}")

    finally:
        # Clean up temporary repository if it was created
        if temp_repo_dir:
            cleanup_temp_repo(temp_repo_dir)
            if verbose and not dry_run and not quiet:
                click.echo(f"Cleaned up temporary repository: {temp_repo_dir}")


@main.command()
@click.option('-w', '--whitelist', 'template_whitelist', is_flag=True, 
              help='Create whitelist mode template')
@click.option('-b', '--blacklist', 'template_blacklist', is_flag=True,
              help='Create blacklist mode template')
@click.option('--minimal', is_flag=True,
              help='Create minimal template')
def init(template_whitelist: bool, template_blacklist: bool, minimal: bool):
    """Create llm.md template in current directory.
    
    Generate a template llm.md configuration file in the current directory
    to help get started with llmd configuration. Choose from different
    template types based on your needs.
    """
    # Validation: template flags are mutually exclusive
    flag_count = sum([template_whitelist, template_blacklist, minimal])
    if flag_count > 1:
        raise click.UsageError("Template options -w/--whitelist, -b/--blacklist, and --minimal are mutually exclusive.")
    
    # Check if llm.md already exists
    llm_md_path = Path('llm.md')
    if llm_md_path.exists():
        raise click.ClickException("llm.md already exists in current directory. Remove it first or choose a different directory.")
    
    # Determine which template to use
    if template_whitelist:
        template_content = WHITELIST_TEMPLATE
        template_type = "whitelist"
    elif template_blacklist:
        template_content = BLACKLIST_TEMPLATE
        template_type = "blacklist"
    elif minimal:
        template_content = MINIMAL_TEMPLATE
        template_type = "minimal"
    else:
        # Default template (blacklist mode)
        template_content = DEFAULT_BLACKLIST_TEMPLATE
        template_type = "default"
    
    # Write template file
    try:
        llm_md_path.write_text(template_content, encoding='utf-8')
        click.echo(f"✓ Created {template_type} template: llm.md")
        click.echo("Edit the file to customize patterns and options for your project.")
    except Exception as e:
        raise click.ClickException(f"Failed to create llm.md: {e}")


if __name__ == '__main__':
    main()