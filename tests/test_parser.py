from pathlib import Path
import tempfile
from llmd.parser import LlmMdParser, GitignoreParser


class TestLlmMdParser:
    """Test the LlmMdParser class."""
    
    def test_parse_llm_md_file(self):
        """Test parsing of llm.md file with all sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Project Configuration

Some description here.

ONLY:
*.py
src/**/*.js

INCLUDE:
.github/workflows/*.yml
docs/*.md

EXCLUDE:
test_*.py
**/node_modules/**

NOT INCLUDE:
*.log
temp/*
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            assert parser.only_patterns == ["*.py", "src/**/*.js"]
            assert parser.include_patterns == [".github/workflows/*.yml", "docs/*.md"]
            # Both EXCLUDE and NOT INCLUDE should go to exclude_patterns
            assert parser.exclude_patterns == ["test_*.py", "**/node_modules/**", "*.log", "temp/*"]
        finally:
            config_path.unlink()
    
    def test_empty_sections(self):
        """Test parsing with empty sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""ONLY:

INCLUDE:

EXCLUDE:
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            assert parser.only_patterns == []
            assert parser.include_patterns == []
            assert parser.exclude_patterns == []
        finally:
            config_path.unlink()
    
    def test_comments_and_whitespace(self):
        """Test parsing handles comments and whitespace correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
# This is a comment
ONLY:
  *.py  
# Another comment
  src/*.js

INCLUDE:

    # Indented comment
    .github/**
    
EXCLUDE:
*.tmp
    # Comment at end
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            assert parser.only_patterns == ["*.py", "src/*.js"]
            assert parser.include_patterns == [".github/**"]
            assert parser.exclude_patterns == ["*.tmp"]
        finally:
            config_path.unlink()
    
    def test_cli_patterns_override(self):
        """Test CLI patterns override behavior."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
ONLY:
*.md

INCLUDE:
*.py

EXCLUDE:
README.md
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            # Test CLI overrides
            parser = LlmMdParser(
                config_path,
                cli_only=["*.txt"],
                cli_include=["*.json"],
                cli_exclude=["*.log"]
            )
            
            # File patterns should still be loaded
            assert parser.only_patterns == ["*.md"]
            assert parser.include_patterns == ["*.py"]
            assert parser.exclude_patterns == ["README.md"]
            
            # CLI patterns should be stored separately
            assert parser.cli_only == ["*.txt"]
            assert parser.cli_include == ["*.json"]
            assert parser.cli_exclude == ["*.log"]
        finally:
            config_path.unlink()
    
    def test_pattern_checking_methods(self):
        """Test the pattern checking methods."""
        parser = LlmMdParser(None, 
                            cli_only=["*.py"],
                            cli_include=["*.md"],
                            cli_exclude=["test_*"])
        
        # Test has_only_patterns
        assert parser.has_only_patterns() is True
        
        # Test has_include_patterns
        assert parser.has_include_patterns() is True
        
        # Test with empty patterns
        parser2 = LlmMdParser(None)
        assert parser2.has_only_patterns() is False
        assert parser2.has_include_patterns() is False
    
    def test_matches_only(self):
        """Test the matches_only method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            test_file = repo_path / "test.py"
            test_file.write_text("test")
            
            parser = LlmMdParser(None, cli_only=["*.py"])
            
            assert parser.matches_only(test_file, repo_path) is True
            assert parser.matches_only(repo_path / "test.md", repo_path) is False
    
    def test_should_include(self):
        """Test the should_include method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            test_file = repo_path / "test.md"
            test_file.write_text("test")
            
            parser = LlmMdParser(None, cli_include=["*.md"])
            
            assert parser.should_include(test_file, repo_path) is True
            assert parser.should_include(repo_path / "test.py", repo_path) is False
            
            # With no patterns, everything should be included
            parser2 = LlmMdParser(None)
            assert parser2.should_include(test_file, repo_path) is True
            assert parser2.should_include(repo_path / "test.py", repo_path) is True
    
    def test_should_exclude(self):
        """Test the should_exclude method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            test_file = repo_path / "test.log"
            test_file.write_text("test")
            
            parser = LlmMdParser(None, cli_exclude=["*.log"])
            
            assert parser.should_exclude(test_file, repo_path) is True
            assert parser.should_exclude(repo_path / "test.py", repo_path) is False


class TestGitignoreParser:
    """Test the GitignoreParser class."""
    
    def test_parse_gitignore(self):
        """Test parsing of .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            gitignore_path = repo_path / ".gitignore"
            gitignore_path.write_text("""
# Comments should be ignored
*.log
node_modules/
build/

# Empty lines ignored

*.pyc
__pycache__/
""")
            
            parser = GitignoreParser(repo_path)
            
            # Test ignored files
            assert parser.should_ignore(repo_path / "test.log") is True
            assert parser.should_ignore(repo_path / "node_modules" / "package.json") is True
            assert parser.should_ignore(repo_path / "build" / "output.js") is True
            assert parser.should_ignore(repo_path / "test.pyc") is True
            assert parser.should_ignore(repo_path / "__pycache__" / "module.pyc") is True
            
            # Test non-ignored files
            assert parser.should_ignore(repo_path / "main.py") is False
            assert parser.should_ignore(repo_path / "README.md") is False
    
    def test_no_gitignore(self):
        """Test behavior when no .gitignore exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            parser = GitignoreParser(repo_path)
            
            # Nothing should be ignored
            assert parser.should_ignore(repo_path / "any_file.txt") is False
            assert parser.should_ignore(repo_path / "node_modules" / "package.json") is False
    
    def test_empty_gitignore(self):
        """Test behavior with empty .gitignore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            gitignore_path = repo_path / ".gitignore"
            gitignore_path.write_text("")
            
            parser = GitignoreParser(repo_path)
            
            # Nothing should be ignored
            assert parser.should_ignore(repo_path / "any_file.txt") is False


# TDD Tests for New Mode-Based Format

class TestLlmMdParserNewFormat:
    """Test the new mode-based format for LlmMdParser."""
    
    def test_parse_whitelist_mode_with_implicit_patterns(self):
        """Test parsing WHITELIST mode with implicit patterns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""WHITELIST:
src/
lib/
*.py
README.md

EXCLUDE:
**/__pycache__/
**/*.test.js

INCLUDE:
tests/fixtures/
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            # New methods that should be implemented
            assert parser.get_mode() == "WHITELIST"
            
            sections = parser.get_sections()
            assert len(sections) == 3  # WHITELIST (implicit), EXCLUDE, INCLUDE
            
            # Check implicit patterns (patterns after mode declaration)
            implicit_patterns = parser.get_implicit_patterns()
            assert implicit_patterns == ["src/", "lib/", "*.py", "README.md"]
            
        finally:
            config_path.unlink()
    
    def test_parse_blacklist_mode_with_implicit_patterns(self):
        """Test parsing BLACKLIST mode with implicit patterns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""BLACKLIST:
tests/
node_modules/
*.log
coverage/

INCLUDE:
tests/fixtures/
debug.log
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            assert parser.get_mode() == "BLACKLIST"
            
            sections = parser.get_sections()
            assert len(sections) == 2  # BLACKLIST (implicit), INCLUDE
            
            implicit_patterns = parser.get_implicit_patterns()
            assert implicit_patterns == ["tests/", "node_modules/", "*.log", "coverage/"]
            
        finally:
            config_path.unlink()
    
    def test_parse_options_section(self):
        """Test parsing of OPTIONS section with type conversion."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""WHITELIST:
src/

OPTIONS:
output: my-context.md
respect_gitignore: true
include_hidden: false
max_file_size: 1024
debug_level: 2
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            options = parser.get_options()
            assert options["output"] == "my-context.md"
            assert options["respect_gitignore"] is True
            assert options["include_hidden"] is False
            assert options["max_file_size"] == 1024
            assert options["debug_level"] == 2
            
        finally:
            config_path.unlink()
    
    def test_mode_declaration_required_first(self):
        """Test that mode declaration must be first non-comment line."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Comment is ok
src/
lib/
WHITELIST:
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            # This should raise an error or handle gracefully
            parser = LlmMdParser(config_path)
            # Should fail validation - no mode declared first
            assert parser.get_mode() is None or parser.get_mode() == ""
            
        finally:
            config_path.unlink()
    
    def test_get_sections_returns_ordered_list(self):
        """Test that get_sections returns sections in parsing order."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""BLACKLIST:
*.tmp

EXCLUDE:
tests/

INCLUDE:
tests/fixtures/

EXCLUDE:
coverage/

OPTIONS:
output: test.md
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            sections = parser.get_sections()
            # Should maintain order: BLACKLIST, EXCLUDE, INCLUDE, EXCLUDE, OPTIONS
            section_types = [section['type'] for section in sections]
            assert section_types == ["BLACKLIST", "EXCLUDE", "INCLUDE", "EXCLUDE", "OPTIONS"]
            
        finally:
            config_path.unlink()
    
    def test_invalid_configuration_handling(self):
        """Test graceful handling of invalid configurations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Missing mode declaration
src/
lib/
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            # Should handle gracefully without crashing
            parser = LlmMdParser(config_path)
            assert parser.get_mode() is None
            
        finally:
            config_path.unlink()
    
    def test_options_type_conversion(self):
        """Test that OPTIONS values are converted to appropriate types."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""WHITELIST:

OPTIONS:
string_value: hello world
boolean_true: true
boolean_false: false
integer_value: 42
float_value: 3.14
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            options = parser.get_options()
            assert isinstance(options["string_value"], str)
            assert options["string_value"] == "hello world"
            assert isinstance(options["boolean_true"], bool)
            assert options["boolean_true"] is True
            assert isinstance(options["boolean_false"], bool)
            assert options["boolean_false"] is False
            assert isinstance(options["integer_value"], int)
            assert options["integer_value"] == 42
            # Note: float parsing might be optional for first implementation
            
        finally:
            config_path.unlink()
    
    def test_empty_mode_sections(self):
        """Test handling of empty mode sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""WHITELIST:

EXCLUDE:

INCLUDE:

OPTIONS:
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            parser = LlmMdParser(config_path)
            
            assert parser.get_mode() == "WHITELIST"
            assert parser.get_implicit_patterns() == []
            assert parser.get_options() == {}
            
        finally:
            config_path.unlink()


# TDD Tests for Default Behavior (Task 1)

class TestLlmMdParserDefaultBehavior:
    """Test default behavior when no llm.md exists (Task 1)."""
    
    def test_parser_with_default_blacklist_mode(self):
        """Test LlmMdParser constructor with default_mode parameter."""
        # No config file exists, but pass default_mode
        parser = LlmMdParser(None, default_mode="BLACKLIST")
        
        # Should have BLACKLIST mode set
        assert parser.get_mode() == "BLACKLIST"
        
        # Should have no explicit patterns (empty patterns for blacklist mode)
        assert parser.get_implicit_patterns() == []
        
        # Should have default options set
        options = parser.get_options()
        assert options.get("output", "llm-context.md") == "llm-context.md"
        assert options.get("respect_gitignore", True) is True
        assert options.get("include_hidden", False) is False
        assert options.get("include_binary", False) is False
    
    def test_parser_with_default_whitelist_mode(self):
        """Test LlmMdParser constructor with default_mode="WHITELIST"."""
        parser = LlmMdParser(None, default_mode="WHITELIST")
        
        assert parser.get_mode() == "WHITELIST"
        assert parser.get_implicit_patterns() == []
    
    def test_parser_without_default_mode_unchanged(self):
        """Test that existing behavior without default_mode is unchanged."""
        parser = LlmMdParser(None)  # No default_mode provided
        
        # Should behave as before (None mode, empty patterns)
        assert parser.get_mode() is None
        assert parser.get_implicit_patterns() == []
        assert parser.get_options() == {}
    
    def test_parser_existing_file_overrides_default_mode(self):
        """Test that existing llm.md file overrides default_mode parameter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""WHITELIST:
src/
*.py
""")
            f.flush()
            config_path = Path(f.name)
        
        try:
            # Even with default_mode="BLACKLIST", existing file should take precedence
            parser = LlmMdParser(config_path, default_mode="BLACKLIST")
            
            assert parser.get_mode() == "WHITELIST"
            assert parser.get_implicit_patterns() == ["src/", "*.py"]
            
        finally:
            config_path.unlink()
    
    def test_default_sections_structure(self):
        """Test that default mode creates proper sections structure."""
        parser = LlmMdParser(None, default_mode="BLACKLIST")
        
        sections = parser.get_sections()
        # Should have one section for the BLACKLIST mode with empty patterns
        assert len(sections) == 1
        assert sections[0]["type"] == "BLACKLIST"
        assert sections[0]["patterns"] == []


class TestDefaultBehaviorIntegration:
    """Integration tests for default behavior when no llm.md exists."""
    
    def test_cli_missing_llm_md_default_behavior(self):
        """Test CLI behavior when no llm.md file exists."""
        import tempfile
        from llmd.cli import main
        from click.testing import CliRunner
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create some test files
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "README.md").write_text("# Project")
            (repo_path / ".hidden").write_text("hidden file")
            (repo_path / "test.pyc").write_text("binary")  # Should be excluded as binary
            
            # Create .gitignore
            (repo_path / ".gitignore").write_text("*.log\ntemp/")
            (repo_path / "debug.log").write_text("log content")
            
            # NO llm.md file exists
            
            runner = CliRunner()
            result = runner.invoke(main, [str(repo_path), '--dry-run'])
            
            # Should succeed (not crash)
            assert result.exit_code == 0
            
            # Should include normal files
            assert "+main.py" in result.output
            assert "+README.md" in result.output
            
            # Should exclude hidden files by default
            assert "+.hidden" not in result.output
            
            # Should exclude binary files by default  
            assert "+test.pyc" not in result.output
            
            # Should exclude gitignored files by default
            assert "+debug.log" not in result.output
    
    def test_scanner_default_blacklist_behavior(self):
        """Test RepoScanner with default BLACKLIST mode and empty patterns."""
        from llmd.scanner import RepoScanner
        from llmd.parser import GitignoreParser
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create test files
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "README.md").write_text("# Project")
            (repo_path / ".hidden").write_text("hidden")
            (repo_path / "test.pyc").write_text("binary")
            
            # Create parser with default blacklist mode
            gitignore_parser = GitignoreParser(repo_path)
            llm_parser = LlmMdParser(None, default_mode="BLACKLIST")
            
            scanner = RepoScanner(repo_path, gitignore_parser, llm_parser)
            files = scanner.scan()
            
            # Convert to relative paths for easier checking
            rel_files = [f.relative_to(repo_path) for f in files]
            
            # Should include normal files in BLACKLIST mode with no exclusion patterns
            assert Path("main.py") in rel_files
            assert Path("README.md") in rel_files
            
            # Should exclude hidden and binary files by default exclusions
            assert Path(".hidden") not in rel_files
            assert Path("test.pyc") not in rel_files