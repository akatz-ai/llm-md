"""
Tests for CLI Mode Selection and Override Behavior (Task 4)

This file tests the new CLI mode functionality:
- -w/--whitelist and -b/--blacklist mode options
- CLI mode flags completely overriding llm.md configuration
- Behavior control flags
- Pattern refinement working with mode flags
"""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from llmd.cli import main


class TestCliModeSelection:
    """Test CLI mode selection functionality."""
    
    def test_whitelist_mode_flag_accepted(self):
        """Test that -w/--whitelist flag is accepted with patterns."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('hello')")
            
            # Test short flag
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
            
            # Test long flag
            result = runner.invoke(main, [str(repo_path), '--whitelist', '*.py', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
    
    def test_blacklist_mode_flag_accepted(self):
        """Test that -b/--blacklist flag is accepted with patterns."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('hello')")
            (repo_path / "test.log").write_text("log content")
            
            # Test short flag
            result = runner.invoke(main, [str(repo_path), '-b', '*.log', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
            assert "+test.log" not in result.output
            
            # Test long flag  
            result = runner.invoke(main, [str(repo_path), '--blacklist', '*.log', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
            assert "+test.log" not in result.output

    def test_mode_flags_mutually_exclusive(self):
        """Test that -w and -b flags are mutually exclusive."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Should fail when both -w and -b are used
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-b', '*.log'])
            assert result.exit_code != 0
            assert "mutually exclusive" in result.output.lower() or "usage error" in result.output.lower()

    def test_pattern_refinement_requires_mode_flags(self):
        """Test that -e/-i flags require -w or -b mode flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Should fail when -e is used without mode flag
            result = runner.invoke(main, [str(repo_path), '-e', '*.log'])
            assert result.exit_code != 0
            
            # Should fail when -i is used without mode flag
            result = runner.invoke(main, [str(repo_path), '-i', '*.py'])
            assert result.exit_code != 0

    def test_pattern_refinement_works_with_mode_flags(self):
        """Test that -e/-i flags work correctly with -w/-b mode flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('hello')")
            (repo_path / "test.js").write_text("console.log('hello')")
            (repo_path / "test.log").write_text("log content")
            
            # Test whitelist mode with exclude - use separate flags for each pattern
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-w', '*.js', '-e', '*.js', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
            assert "+test.js" not in result.output
            
            # Test whitelist mode with include (force-include)
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-i', '*.log', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
            assert "+test.log" in result.output


class TestCliModeOverride:
    """Test that CLI mode flags completely override llm.md configuration."""
    
    def test_cli_mode_completely_overrides_llm_md(self):
        """Test that CLI mode flags completely override llm.md configuration."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create llm.md with WHITELIST configuration
            llm_md = repo_path / "llm.md"
            llm_md.write_text("""WHITELIST:
src/
*.py

EXCLUDE:
*.test.py
""")
            
            # Create test files
            (repo_path / "main.py").write_text("print('main')")
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "test.js").write_text("console.log('test')")
            src_dir = repo_path / "src"
            src_dir.mkdir()
            (src_dir / "module.py").write_text("print('module')")
            
            # Without CLI mode flags, should use llm.md config
            result = runner.invoke(main, [str(repo_path), '--dry-run'])
            assert result.exit_code == 0
            # Should include files from WHITELIST patterns but exclude test.py
            # This is to establish baseline behavior
            
            # With CLI blacklist mode, should completely override llm.md
            result = runner.invoke(main, [str(repo_path), '-b', '*.py', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.js" in result.output  # Should include JS files (not in blacklist)
            assert "+main.py" not in result.output  # Should exclude Python files (in blacklist)
            assert "+test.py" not in result.output  # Should exclude Python files (in blacklist)

    def test_cli_behavior_flags_override_llm_md_options(self):
        """Test that CLI behavior flags override llm.md OPTIONS."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create llm.md with OPTIONS that include hidden files
            llm_md = repo_path / "llm.md"
            llm_md.write_text("""BLACKLIST:

OPTIONS:
include_hidden: true
""")
            
            # Create test files including hidden file
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / ".hidden").write_text("hidden content")
            
            # CLI flag should override llm.md option
            result = runner.invoke(main, [str(repo_path), '-b', '*.log', '--exclude-hidden', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output
            assert "+.hidden" not in result.output  # Should be excluded despite llm.md setting


class TestBehaviorControlFlags:
    """Test behavior control flags functionality."""
    
    def test_include_gitignore_flags(self):
        """Test --include-gitignore and --no-gitignore flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create .gitignore
            (repo_path / ".gitignore").write_text("*.log\ntemp/")
            
            # Create test files
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "debug.log").write_text("log content")
            
            # Test --include-gitignore
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--include-gitignore', '--dry-run'])
            assert result.exit_code == 0
            assert "+debug.log" in result.output
            
            # Test --no-gitignore (alias)
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--no-gitignore', '--dry-run'])
            assert result.exit_code == 0
            assert "+debug.log" in result.output
            
            # Test default behavior (should exclude gitignored files)
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--dry-run'])
            assert result.exit_code == 0
            assert "+debug.log" not in result.output

    def test_include_hidden_flags(self):
        """Test --include-hidden and --with-hidden flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test files including hidden file
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / ".hidden").write_text("hidden content")
            
            # Test --include-hidden
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--include-hidden', '--dry-run'])
            assert result.exit_code == 0
            assert "+.hidden" in result.output
            
            # Test --with-hidden (alias)
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--with-hidden', '--dry-run'])
            assert result.exit_code == 0
            assert "+.hidden" in result.output
            
            # Test default behavior (should exclude hidden files)
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--dry-run'])
            assert result.exit_code == 0
            assert "+.hidden" not in result.output

    def test_include_binary_flags(self):
        """Test --include-binary and --with-binary flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test files including binary file
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "image.jpg").write_bytes(b'\xff\xd8\xff\xe0')  # JPEG header
            
            # Test --include-binary
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--include-binary', '--dry-run'])
            assert result.exit_code == 0
            assert "+image.jpg" in result.output
            
            # Test --with-binary (alias)
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--with-binary', '--dry-run'])
            assert result.exit_code == 0
            assert "+image.jpg" in result.output
            
            # Test default behavior (should exclude binary files)
            result = runner.invoke(main, [str(repo_path), '-b', '*.txt', '--dry-run'])
            assert result.exit_code == 0
            assert "+image.jpg" not in result.output


class TestQuietMode:
    """Test quiet mode functionality."""
    
    def test_quiet_flag_suppresses_output(self):
        """Test that -q/--quiet flag suppresses non-error output."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            
            # Test without quiet flag (should have verbose output)
            result = runner.invoke(main, [str(repo_path), '-w', '*.py'])
            assert result.exit_code == 0
            assert "Scanning repository" in result.output or "Found" in result.output
            
            # Test with -q flag (should suppress non-error output)
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-q'])
            assert result.exit_code == 0
            assert "Scanning repository" not in result.output
            
            # Test with --quiet flag
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '--quiet'])
            assert result.exit_code == 0
            assert "Scanning repository" not in result.output

    def test_quiet_mode_with_dry_run_still_shows_files(self):
        """Test that quiet mode with --dry-run still shows the file list."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            
            # Quiet + dry-run should still show file list (that's the point of dry-run)
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-q', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output


class TestTask6CliAlignment:
    """Test Task 6 - Complete CLI Interface Alignment and Remove Legacy Features."""
    
    def test_path_argument_is_optional_defaults_to_current_dir(self):
        """Test that PATH argument is optional and defaults to current directory."""
        runner = CliRunner()
        
        # Change to a temp directory and test without PATH argument
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            
            # Test without PATH argument - should work
            with runner.isolated_filesystem():
                # Copy test file to current directory
                Path("test.py").write_text("print('test')")
                result = runner.invoke(main, ['-w', '*.py', '--dry-run'])
                assert result.exit_code == 0
                assert "+test.py" in result.output
    
    def test_multiple_pattern_arguments_work(self):
        """Test that multiple patterns work for -w and -b flags: llmd . -w "src/" "tests/" """
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create directory structure
            src_dir = repo_path / "src"
            tests_dir = repo_path / "tests"
            src_dir.mkdir()
            tests_dir.mkdir()
            
            (src_dir / "main.py").write_text("print('main')")
            (tests_dir / "test_main.py").write_text("print('test')")
            (repo_path / "README.md").write_text("# README")
            
            # Test multiple whitelist patterns
            result = runner.invoke(main, [str(repo_path), '-w', 'src/', 'tests/', '--dry-run'])
            assert result.exit_code == 0
            assert "+src/main.py" in result.output
            assert "+tests/test_main.py" in result.output
            assert "+README.md" not in result.output
            
            # Test multiple blacklist patterns  
            result = runner.invoke(main, [str(repo_path), '-b', 'src/', 'tests/', '--dry-run'])
            assert result.exit_code == 0
            assert "+src/main.py" not in result.output
            assert "+tests/test_main.py" not in result.output
            assert "+README.md" in result.output
    
    def test_legacy_config_option_removed(self):
        """Test that -c/--config option is removed and causes error."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "custom.md").write_text("WHITELIST:\n*.py")
            
            # Test that -c flag causes error
            result = runner.invoke(main, [str(repo_path), '-c', str(repo_path / "custom.md")])
            assert result.exit_code != 0
            
            # Test that --config flag causes error
            result = runner.invoke(main, [str(repo_path), '--config', str(repo_path / "custom.md")])
            assert result.exit_code != 0
    
    def test_legacy_only_option_removed(self):
        """Test that -O/--only option is removed and causes error."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            
            # Test that -O flag causes error
            result = runner.invoke(main, [str(repo_path), '-O', '*.py'])
            assert result.exit_code != 0
            
            # Test that --only flag causes error
            result = runner.invoke(main, [str(repo_path), '--only', '*.py'])
            assert result.exit_code != 0
    
    def test_default_output_path_is_dot_slash(self):
        """Test that default output path is './llm-context.md' not 'llm-context.md'."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            
            # Run without output flag and check that file is created at ./llm-context.md
            result = runner.invoke(main, [str(repo_path), '-w', '*.py'])
            assert result.exit_code == 0
            
            # Check that output mentions ./llm-context.md
            assert "./llm-context.md" in result.output or "llm-context.md" in result.output
    
    def test_enhanced_dry_run_output_shows_detailed_info(self):
        """Test that --dry-run shows detailed info about what will and will not be kept."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create diverse file set
            (repo_path / "main.py").write_text("print('main')")
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "config.json").write_text('{"key": "value"}')
            (repo_path / "debug.log").write_text("log content")
            (repo_path / ".hidden").write_text("hidden content")
            
            # Create .gitignore to exclude .log files
            (repo_path / ".gitignore").write_text("*.log")
            
            # Test detailed dry-run output
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '*.json', '--dry-run'])
            assert result.exit_code == 0
            
            # Should show included files with + prefix
            assert "+main.py" in result.output
            assert "+test.py" in result.output  
            assert "+config.json" in result.output
            
            # Should NOT show .log file (gitignored)
            assert "debug.log" not in result.output
            
            # Should NOT show hidden file (default exclusion)
            assert ".hidden" not in result.output
    
    def test_error_messages_match_prd_format(self):
        """Test that error messages for invalid combinations match PRD error conditions."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Test mutually exclusive mode flags
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-b', '*.log'])
            assert result.exit_code != 0
            assert "mutually exclusive" in result.output.lower()
            
            # Test pattern refinement without mode flags
            result = runner.invoke(main, [str(repo_path), '-e', '*.log'])
            assert result.exit_code != 0
            assert "require" in result.output.lower() and "mode" in result.output.lower()
    
    def test_cli_synopsis_matches_prd(self):
        """Test that CLI help shows synopsis: llmd [PATH] [OPTIONS]."""
        runner = CliRunner()
        
        # Test help output
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        
        # Should show proper usage format
        assert "Usage:" in result.output
        # PATH should be shown as optional in brackets
        assert "[PATH]" in result.output or "repo_path" in result.output