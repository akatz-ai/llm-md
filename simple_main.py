#!/usr/bin/env python3
"""
Simple test to see if I can get basic path arguments working with Click
"""

import click
from pathlib import Path
from typing import Optional


@click.command()
@click.argument('path', required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--dry-run', is_flag=True, help='Show which files would be included without generating output')
def simple_main(path: Optional[Path], dry_run: bool):
    """Simple test command."""
    if path:
        click.echo(f"Path: {path}")
    else:
        click.echo("No path provided, using current directory")
    
    if dry_run:
        click.echo("Dry run mode enabled")
    
    click.echo("Success!")


if __name__ == "__main__":
    simple_main()