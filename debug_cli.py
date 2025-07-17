#!/usr/bin/env python3
"""
Debug script to test FlexibleGroup behavior
"""

import click
from pathlib import Path

class FlexibleGroup(click.Group):
    def invoke(self, ctx):
        print("FlexibleGroup.invoke called")
        print(f"ctx.protected_args: {ctx.protected_args}")
        print(f"ctx.args: {ctx.args}")
        
        # Check if we have any protected_args and the first one is a directory
        if ctx.protected_args and Path(ctx.protected_args[0]).exists() and Path(ctx.protected_args[0]).is_dir():
            print(f"Found directory in protected_args: {ctx.protected_args[0]}")
            # Move the path from protected_args to args so main() can access it
            ctx.args = list(ctx.protected_args)
            # Don't try to resolve as a command, just call the callback directly
            ctx.invoked_subcommand = None
            return ctx.invoke(self.callback)
        
        # Otherwise use normal group behavior
        return super().invoke(ctx)

@click.group(cls=FlexibleGroup, invoke_without_command=True, context_settings={'allow_extra_args': True, 'allow_interspersed_args': False})
@click.pass_context
def main(ctx):
    """Test CLI"""
    print(f"main() called, invoked_subcommand: {ctx.invoked_subcommand}")
    print(f"ctx.args: {ctx.args}")
    
    if ctx.invoked_subcommand is not None:
        print("Subcommand detected, returning")
        return
    
    # Handle repository path from extra args
    extra_args = ctx.args
    print(f"extra_args: {extra_args}")
    if len(extra_args) > 1:
        raise click.UsageError("Too many arguments. Expected at most one repository path.")
    elif len(extra_args) == 1:
        repo_path = Path(extra_args[0])
        print(f"Got repo path: {repo_path}")
        if not repo_path.exists():
            raise click.UsageError(f"Repository path '{repo_path}' does not exist.")
        if not repo_path.is_dir():
            raise click.UsageError(f"Repository path '{repo_path}' is not a directory.")
    else:
        repo_path = Path('.')
        print("Using current directory")
    
    print(f"Final repo_path: {repo_path}")

@main.command()
def init():
    """Test subcommand"""
    print("init subcommand called")

if __name__ == '__main__':
    main()