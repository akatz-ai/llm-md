"""
Tests for GitHub Remote Repository Context Extraction (Task 7)

This file tests the new GitHub remote repository functionality:
- --github flag for cloning remote repositories
- Integration with existing llmd arguments
- Temporary directory management and cleanup
- Error handling for invalid URLs and clone failures
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from llmd.cli import main
import pytest


class TestGitHubUrlValidation:
    """Test GitHub URL validation functionality."""
    
    def test_valid_github_https_urls_accepted(self):
        """Test that valid GitHub HTTPS URLs are accepted."""
        runner = CliRunner()
        
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user/repo.git",
            "https://github.com/organization/repository-name",
            "https://github.com/user123/repo-with-dashes",
        ]
        
        for url in valid_urls:
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = "/tmp/cloned_repo"
                with patch('llmd.cli.cleanup_temp_repo'):
                    # Should not fail due to URL validation
                    result = runner.invoke(main, ['--github', url, '--dry-run'])
                    # We expect this to fail for other reasons (like git not being available)
                    # but NOT because of URL validation
                    assert "Invalid GitHub URL" not in result.output
    
    def test_invalid_github_urls_rejected(self):
        """Test that invalid GitHub URLs are rejected."""
        runner = CliRunner()
        
        invalid_urls = [
            "https://gitlab.com/user/repo",
            "https://bitbucket.org/user/repo", 
            "https://github.com",
            "not-a-url",
            "http://github.com/user/repo",  # HTTP not HTTPS
            "",
        ]
        
        for url in invalid_urls:
            result = runner.invoke(main, ['--github', url])
            assert result.exit_code != 0
            assert "Invalid GitHub URL" in result.output or "Usage Error" in result.output

    def test_github_ssh_urls_accepted(self):
        """Test that GitHub SSH URLs are accepted."""
        runner = CliRunner()
        
        ssh_urls = [
            "git@github.com:user/repo.git",
            "git@github.com:organization/repository-name.git",
        ]
        
        for url in ssh_urls:
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = "/tmp/cloned_repo"
                with patch('llmd.cli.cleanup_temp_repo'):
                    result = runner.invoke(main, ['--github', url, '--dry-run'])
                    assert "Invalid GitHub URL" not in result.output


class TestGitHubCloneIntegration:
    """Test GitHub cloning integration with existing llmd workflow."""
    
    def test_github_flag_prevents_path_argument(self):
        """Test that --github flag makes PATH argument unnecessary/ignored."""
        runner = CliRunner()
        
        with patch('llmd.cli.clone_github_repo') as mock_clone:
            mock_clone.return_value = "/tmp/cloned_repo"
            with patch('llmd.cli.cleanup_temp_repo'):
                # Should work without PATH when using --github
                result = runner.invoke(main, ['--github', 'https://github.com/user/repo', '--dry-run'])
                # Should not complain about missing PATH
                assert "Repository path" not in result.output or result.exit_code == 0

    def test_github_integrates_with_whitelist_mode(self):
        """Test that --github works with -w/--whitelist flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the clone to return our temp directory
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = temp_dir
                with patch('llmd.cli.cleanup_temp_repo'):
                    
                    # Create test files in temp directory
                    Path(temp_dir, "test.py").write_text("print('hello')")
                    Path(temp_dir, "test.js").write_text("console.log('hello')")
                    
                    result = runner.invoke(main, [
                        '--github', 'https://github.com/user/repo',
                        '-w', '*.py',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert "+test.py" in result.output
                    assert "+test.js" not in result.output

    def test_github_integrates_with_blacklist_mode(self):
        """Test that --github works with -b/--blacklist flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = temp_dir
                with patch('llmd.cli.cleanup_temp_repo'):
                    
                    # Create test files in temp directory
                    Path(temp_dir, "test.py").write_text("print('hello')")
                    Path(temp_dir, "test.log").write_text("log content")
                    
                    result = runner.invoke(main, [
                        '--github', 'https://github.com/user/repo',
                        '-b', '*.log',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert "+test.py" in result.output
                    assert "+test.log" not in result.output

    def test_github_integrates_with_output_flag(self):
        """Test that --github works with -o/--output flag."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir, "custom-output.md")
            
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = temp_dir
                with patch('llmd.cli.cleanup_temp_repo'):
                    
                    # Create test file in temp directory
                    Path(temp_dir, "test.py").write_text("print('hello')")
                    
                    result = runner.invoke(main, [
                        '--github', 'https://github.com/user/repo',
                        '-w', '*.py',
                        '-o', str(output_file)
                    ])
                    
                    assert result.exit_code == 0
                    assert output_file.exists()
                    assert "print('hello')" in output_file.read_text()

    def test_github_integrates_with_include_exclude_flags(self):
        """Test that --github works with -i/--include and -e/--exclude flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = temp_dir
                with patch('llmd.cli.cleanup_temp_repo'):
                    
                    # Create test files
                    Path(temp_dir, "main.py").write_text("print('main')")
                    Path(temp_dir, "test.py").write_text("print('test')")
                    Path(temp_dir, "config.json").write_text("{'key': 'value'}")
                    
                    result = runner.invoke(main, [
                        '--github', 'https://github.com/user/repo',
                        '-w', '*.py',
                        '-e', 'test.py',
                        '-i', 'config.json',
                        '--dry-run'
                    ])
                    
                    assert result.exit_code == 0
                    assert "+main.py" in result.output
                    assert "+test.py" not in result.output  # excluded
                    assert "+config.json" in result.output  # force included


class TestGitOperations:
    """Test git operations and temporary directory management."""
    
    def test_git_clone_with_temporary_directory(self):
        """Test that git clone creates and uses temporary directory."""
        # This test will be implementation-specific
        # For now, test that the function exists and can be called
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            from llmd.cli import clone_github_repo
            
            temp_dir = clone_github_repo("https://github.com/user/repo")
            assert temp_dir is not None
            assert isinstance(temp_dir, str)
            
            # Should have called git clone
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "git" in call_args
            assert "clone" in call_args
            assert "https://github.com/user/repo" in call_args

    def test_git_clone_error_handling(self):
        """Test that git clone errors are handled properly."""
        with patch('subprocess.run') as mock_run:
            # Simulate git clone failure
            mock_run.return_value = MagicMock(returncode=1, stderr="Repository not found")
            
            from llmd.cli import clone_github_repo
            
            with pytest.raises(Exception) as exc_info:
                clone_github_repo("https://github.com/nonexistent/repo")
            
            assert "git clone failed" in str(exc_info.value).lower() or "repository not found" in str(exc_info.value).lower()

    def test_temporary_directory_cleanup(self):
        """Test that temporary directories are cleaned up."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test directory structure
            test_repo = Path(temp_dir, "test_repo")
            test_repo.mkdir()
            (test_repo / "test.py").write_text("print('test')")
            
            from llmd.cli import cleanup_temp_repo
            
            # Directory should exist before cleanup
            assert test_repo.exists()
            
            cleanup_temp_repo(str(test_repo))
            
            # Directory should be gone after cleanup
            assert not test_repo.exists()


class TestGitHubErrorHandling:
    """Test error handling for GitHub operations."""
    
    def test_git_not_available_error(self):
        """Test error when git command is not available."""
        runner = CliRunner()
        
        with patch('subprocess.run') as mock_run:
            # Simulate git command not found
            mock_run.side_effect = FileNotFoundError("git command not found")
            
            result = runner.invoke(main, ['--github', 'https://github.com/user/repo'])
            assert result.exit_code != 0
            assert "git" in result.output.lower()

    def test_network_error_handling(self):
        """Test handling of network connectivity issues."""
        runner = CliRunner()
        
        with patch('subprocess.run') as mock_run:
            # Simulate network error
            mock_run.return_value = MagicMock(
                returncode=128, 
                stderr="fatal: unable to access 'https://github.com/user/repo': Could not resolve host"
            )
            
            result = runner.invoke(main, ['--github', 'https://github.com/user/repo'])
            assert result.exit_code != 0
            assert "network" in result.output.lower() or "connection" in result.output.lower()

    def test_cleanup_happens_on_error(self):
        """Test that temporary directories are cleaned up even when errors occur."""
        runner = CliRunner()
        
        cleanup_called = False
        
        def mock_cleanup(path):
            nonlocal cleanup_called
            cleanup_called = True
        
        with patch('llmd.cli.clone_github_repo') as mock_clone:
            mock_clone.return_value = "/tmp/test_repo"
            with patch('llmd.cli.cleanup_temp_repo', side_effect=mock_cleanup):
                
                # Force an error after cloning (e.g., scanner error)
                with patch('llmd.cli.RepoScanner') as mock_scanner:
                    mock_scanner.side_effect = Exception("Scanner error")
                    
                    runner.invoke(main, ['--github', 'https://github.com/user/repo'])
                    
                    # Should still call cleanup even on error
                    assert cleanup_called


class TestGitHubCompleteWorkflow:
    """Test complete end-to-end GitHub workflow."""
    
    def test_complete_github_workflow_success(self):
        """Test complete successful workflow from clone to output generation."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir, "github-context.md")
            
            # Create a mock repository structure
            repo_dir = Path(temp_dir, "cloned_repo")
            repo_dir.mkdir()
            (repo_dir / "main.py").write_text("def main():\n    print('Hello from GitHub!')")
            (repo_dir / "README.md").write_text("# Test Repository")
            
            with patch('llmd.cli.clone_github_repo') as mock_clone:
                mock_clone.return_value = str(repo_dir)
                with patch('llmd.cli.cleanup_temp_repo') as mock_cleanup:
                    
                    result = runner.invoke(main, [
                        '--github', 'https://github.com/user/test-repo',
                        '-w', '*.py', '-w', '*.md',
                        '-o', str(output_file)
                    ])
                    
                    assert result.exit_code == 0
                    assert output_file.exists()
                    
                    content = output_file.read_text()
                    assert "main.py" in content
                    assert "README.md" in content
                    assert "Hello from GitHub!" in content
                    
                    # Verify cleanup was called
                    mock_cleanup.assert_called_once_with(str(repo_dir))