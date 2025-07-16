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