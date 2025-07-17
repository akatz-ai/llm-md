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
from llmd.cli import main, set_test_args, clear_test_args


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
        """Test that multiple patterns work for -w and -b flags with multiple flag usage."""
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
            
            # Test multiple whitelist patterns using multiple -w flags
            result = runner.invoke(main, [str(repo_path), '-w', 'src/', '-w', 'tests/', '--dry-run'])
            assert result.exit_code == 0
            assert "+src/main.py" in result.output
            assert "+tests/test_main.py" in result.output
            assert "+README.md" not in result.output
            
            # Test multiple blacklist patterns using multiple -b flags
            result = runner.invoke(main, [str(repo_path), '-b', 'src/', '-b', 'tests/', '--dry-run'])
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
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-w', '*.json', '--dry-run'])
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
        assert "[REPO_PATH]" in result.output or "[PATH]" in result.output


class TestSequentialPatternProcessing:
    """Test sequential pattern processing for CLI flags (Task 13)."""
    
    def test_sequential_whitelist_exclude_example(self):
        """Test: llmd -w src/ -e src/*.pyc (start with src/, remove .pyc files)."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test file structure
            src_dir = repo_path / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("print('main')")
            (src_dir / "utils.py").write_text("print('utils')")
            (src_dir / "cache.pyc").write_text("compiled")
            (repo_path / "README.md").write_text("# README")
            
            # Test sequential processing: whitelist src/, then exclude .pyc files
            result = runner.invoke(main, [str(repo_path), '-w', 'src/', '-e', 'src/*.pyc', '--dry-run'])
            assert result.exit_code == 0
            
            # Should include Python files from src/
            assert "+src/main.py" in result.output
            assert "+src/utils.py" in result.output
            
            # Should exclude .pyc files despite being in src/
            assert "+src/cache.pyc" not in result.output
            
            # Should not include files outside src/
            assert "+README.md" not in result.output
    
    def test_sequential_exclude_include_rescue_example(self):
        """Test: llmd -w src/ -e src/random/ -i src/random/important-file.txt."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test file structure
            src_dir = repo_path / "src"
            random_dir = src_dir / "random"
            src_dir.mkdir()
            random_dir.mkdir()
            
            (src_dir / "main.py").write_text("print('main')")
            (random_dir / "junk.txt").write_text("junk")
            (random_dir / "important-file.txt").write_text("important")
            (repo_path / "README.md").write_text("# README")
            
            # Test sequential processing: whitelist src/, exclude random/, rescue important file
            result = runner.invoke(main, [
                str(repo_path), 
                '-w', 'src/', 
                '-e', 'src/random/', 
                '-i', 'src/random/important-file.txt',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Should include main.py from src/
            assert "+src/main.py" in result.output
            
            # Should exclude junk.txt from random/ directory
            assert "+src/random/junk.txt" not in result.output
            
            # Should include important-file.txt (rescued by include)
            assert "+src/random/important-file.txt" in result.output
            
            # Should not include files outside src/
            assert "+README.md" not in result.output
    
    def test_sequential_blacklist_include_exclude_example(self):
        """Test: llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test file structure
            tests_dir = repo_path / "tests"
            integration_dir = tests_dir / "integration"
            tests_dir.mkdir()
            integration_dir.mkdir()
            
            (repo_path / "main.py").write_text("print('main')")
            (tests_dir / "test_main.py").write_text("test main")
            (integration_dir / "test_integration.py").write_text("integration test")
            (integration_dir / "cache.pyc").write_text("compiled")
            
            # Test sequential processing: blacklist tests/, rescue integration/, exclude .pyc
            result = runner.invoke(main, [
                str(repo_path),
                '-b', 'tests/',
                '-i', 'tests/integration/', 
                '-e', 'tests/integration/*.pyc',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Should include main.py (not in tests/)
            assert "+main.py" in result.output
            
            # Should exclude test_main.py (in tests/, not rescued)
            assert "+tests/test_main.py" not in result.output
            
            # Should include integration test (rescued by include)
            assert "+tests/integration/test_integration.py" in result.output
            
            # Should exclude .pyc file despite being rescued (exclude comes after include)
            assert "+tests/integration/cache.pyc" not in result.output
    
    def test_sequential_processing_order_matters(self):
        """Test that the order of -e and -i flags matters for processing."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test file structure
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "main.py").write_text("print('main')")
            
            # Test order 1: exclude then include test.py
            test_args1 = [str(repo_path), '-w', '*.py', '-e', 'test.py', '-i', 'test.py', '--dry-run']
            set_test_args(test_args1)
            try:
                result1 = runner.invoke(main, [
                    str(repo_path),
                    '-w', '*.py',
                    '-e', 'test.py',
                    '-i', 'test.py',
                    '--dry-run'
                ])
                assert result1.exit_code == 0
                
                # test.py should be included (include comes after exclude)
                assert "+test.py" in result1.output
                assert "+main.py" in result1.output
            finally:
                clear_test_args()
            
            # Test order 2: include then exclude test.py  
            test_args2 = [str(repo_path), '-w', '*.py', '-i', 'test.py', '-e', 'test.py', '--dry-run']
            set_test_args(test_args2)
            try:
                result2 = runner.invoke(main, [
                    str(repo_path),
                    '-w', '*.py',
                    '-i', 'test.py',
                    '-e', 'test.py', 
                    '--dry-run'
                ])
                assert result2.exit_code == 0
                
                # test.py should be excluded (exclude comes after include)
                assert "+test.py" not in result2.output
                assert "+main.py" in result2.output
            finally:
                clear_test_args()
    
    def test_sequential_processing_ad_infinitum(self):
        """Test that sequential processing can continue indefinitely."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test file structure
            (repo_path / "file1.py").write_text("print('1')")
            (repo_path / "file2.py").write_text("print('2')")
            (repo_path / "file3.py").write_text("print('3')")
            (repo_path / "file4.py").write_text("print('4')")
            
            # Set up test args for sequential processing
            test_args = [
                str(repo_path),
                '-w', '*.py',          # Start with all Python files
                '-e', 'file1.py',      # Exclude file1
                '-e', 'file2.py',      # Exclude file2
                '-i', 'file1.py',      # Rescue file1
                '-e', 'file3.py',      # Exclude file3
                '-i', 'file2.py',      # Rescue file2
                '-i', 'file3.py',      # Rescue file3
                '-e', 'file1.py',      # Exclude file1 again
                '--dry-run'
            ]
            set_test_args(test_args)
            
            try:
                # Test long chain of alternating exclude/include patterns
                result = runner.invoke(main, [
                    str(repo_path),
                    '-w', '*.py',          # Start with all Python files
                    '-e', 'file1.py',      # Exclude file1
                    '-e', 'file2.py',      # Exclude file2
                    '-i', 'file1.py',      # Rescue file1
                    '-e', 'file3.py',      # Exclude file3
                    '-i', 'file2.py',      # Rescue file2
                    '-i', 'file3.py',      # Rescue file3
                    '-e', 'file1.py',      # Exclude file1 again
                    '--dry-run'
                ])
                assert result.exit_code == 0
                
                # Based on sequential processing:
                # - file1: included → excluded → excluded → included → excluded → included → included → excluded (final: excluded)
                # - file2: included → excluded → excluded → included → included → included → included → included (final: included)
                # - file3: included → included → included → included → excluded → included → included → included (final: included)
                # - file4: included (final: included)
                
                assert "+file1.py" not in result.output  # Finally excluded
                assert "+file2.py" in result.output      # Finally included
                assert "+file3.py" in result.output      # Finally included
                assert "+file4.py" in result.output      # Never changed
            finally:
                clear_test_args()
    
    def test_legacy_behavior_unchanged_without_mixing(self):
        """Test that existing CLI behavior is unchanged when not mixing -e and -i."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test file structure
            (repo_path / "main.py").write_text("print('main')")
            (repo_path / "test.py").write_text("print('test')")
            (repo_path / "README.md").write_text("# README")
            
            # Test exclude only (should work as before)
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-e', 'test.py', '--dry-run'])
            assert result.exit_code == 0
            assert "+main.py" in result.output
            assert "+test.py" not in result.output
            assert "+README.md" not in result.output
            
            # Test include only (should work as before)
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '-i', '*.md', '--dry-run'])
            assert result.exit_code == 0
            assert "+main.py" in result.output
            assert "+test.py" in result.output
            assert "+README.md" in result.output  # Rescued by include
    
    def test_sequential_processing_with_mode_flags_only(self):
        """Test that sequential processing only applies when using -w or -b mode flags."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create llm.md file with legacy INCLUDE/EXCLUDE
            llm_md = repo_path / "llm.md"
            llm_md.write_text("""INCLUDE:
*.py

EXCLUDE:
test.py
""")
            
            # Create test files
            (repo_path / "main.py").write_text("print('main')")
            (repo_path / "test.py").write_text("print('test')")
            
            # Without mode flags, should use legacy precedence (INCLUDE overrides EXCLUDE)
            result = runner.invoke(main, [str(repo_path), '--dry-run'])
            assert result.exit_code == 0
            
            # Legacy behavior: INCLUDE should rescue test.py from EXCLUDE
            assert "+test.py" in result.output
            assert "+main.py" in result.output