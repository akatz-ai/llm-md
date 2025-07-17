#!/usr/bin/env python3
"""
Simple test to see what's happening with CLI arguments
"""

import os
import tempfile
import unittest.mock
from click.testing import CliRunner
from src.llmd.cli import main

# Create a test directory
test_dir = tempfile.mkdtemp()
print(f"Created test directory: {test_dir}")

# Test current directory (should work)
runner = CliRunner()
result = runner.invoke(main, ['--dry-run'])
print("Current directory test:")
print(f"Exit code: {result.exit_code}")
print(f"Output: {result.output}")
print()

# Test with path argument (the issue)
result = runner.invoke(main, [test_dir, '--dry-run'])
print("Path argument test:")
print(f"Exit code: {result.exit_code}")
print(f"Output: {result.output}")
print()

# Test with GitHub option (should work)
with unittest.mock.patch('src.llmd.cli.clone_github_repo') as mock_clone:
    mock_clone.return_value = test_dir
    with unittest.mock.patch('src.llmd.cli.cleanup_temp_repo'):
        result = runner.invoke(main, ['--github', 'https://github.com/user/repo', '--dry-run'])
        print("GitHub option test:")
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

# Cleanup
os.rmdir(test_dir)