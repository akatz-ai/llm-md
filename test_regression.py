#!/usr/bin/env python3
"""
Simple test to confirm the regression behavior before fixing it.
This test should fail initially, then pass after the fix.
"""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from src.llmd.cli import main


def test_path_argument_regression():
    """Test that repository path arguments work correctly."""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        (repo_path / "test.py").write_text("print('hello')")
        
        # This should work but currently fails
        result = runner.invoke(main, [str(repo_path), '--dry-run'])
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
        
        # Should succeed (exit_code == 0) and show the file
        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}: {result.output}"
        assert "test.py" in result.output, "Expected file not found in output"


if __name__ == "__main__":
    test_path_argument_regression()
    print("Test passed!")