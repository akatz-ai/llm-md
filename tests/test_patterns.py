import pytest
from pathlib import Path
import tempfile
import shutil
from llmd.parser import LlmMdParser, GitignoreParser
from llmd.scanner import RepoScanner


class TestPatternLogic:
    """Test the ONLY, INCLUDE, and EXCLUDE pattern logic."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository structure for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create test file structure
        files = [
            "README.md",
            "main.py",
            "test.py",
            ".hidden_file",
            ".github/workflows/test.yml",
            "src/module.py",
            "src/utils.py",
            "src/.hidden_module.py",
            "docs/index.md",
            "docs/api.md",
            "node_modules/package.json",
            "build/output.js",
            "__pycache__/cache.pyc",
            "data.json",
            "config.yaml",
            "image.png",
            "archive.zip"
        ]
        
        for file_path in files:
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Content of {file_path}")
        
        # Create .gitignore
        gitignore_content = """
node_modules/
build/
*.pyc
__pycache__/
"""
        (repo_path / ".gitignore").write_text(gitignore_content)
        
        yield repo_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_default_behavior(self, temp_repo):
        """Test default behavior without any patterns."""
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(None)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_names = [f.name for f in files]
        
        # Should include visible files, excluding gitignored and binary
        assert "README.md" in file_names
        assert "main.py" in file_names
        assert "test.py" in file_names
        assert "module.py" in file_names
        assert "utils.py" in file_names
        assert "index.md" in file_names
        assert "api.md" in file_names
        assert "data.json" in file_names
        assert "config.yaml" in file_names
        
        # Should exclude
        assert ".hidden_file" not in file_names
        assert "test.yml" not in file_names  # in hidden directory
        assert ".hidden_module.py" not in file_names
        assert "package.json" not in file_names  # gitignored
        assert "output.js" not in file_names  # gitignored
        assert "cache.pyc" not in file_names  # gitignored
        assert "image.png" not in file_names  # binary
        assert "archive.zip" not in file_names  # binary
    
    def test_only_patterns(self, temp_repo):
        """Test ONLY patterns bypass all exclusions."""
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(None, cli_only=["*.py", ".github/**", "build/*.js"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should include only matched files, even if gitignored or hidden
        assert "main.py" in file_paths
        assert "test.py" in file_paths
        assert "src/module.py" in file_paths
        assert "src/utils.py" in file_paths
        assert "src/.hidden_module.py" in file_paths  # hidden but matches
        assert ".github/workflows/test.yml" in file_paths  # hidden dir but matches
        assert "build/output.js" in file_paths  # gitignored but matches
        
        # Should exclude non-matching files
        assert "README.md" not in file_paths
        assert ".hidden_file" not in file_paths
        assert "data.json" not in file_paths
        assert "__pycache__/cache.pyc" not in file_paths  # doesn't match pattern
    
    def test_include_patterns_rescue(self, temp_repo):
        """Test INCLUDE patterns rescue files from exclusions."""
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(None, cli_include=[".github/**", "build/*.js", ".hidden_file"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Regular files should still be included
        assert "README.md" in file_paths
        assert "main.py" in file_paths
        assert "test.py" in file_paths
        
        # INCLUDE patterns should rescue these from exclusions
        assert ".github/workflows/test.yml" in file_paths  # rescued from hidden dir
        assert "build/output.js" in file_paths  # rescued from gitignore
        assert ".hidden_file" in file_paths  # rescued from hidden file exclusion
        
        # Files not rescued should still be excluded
        assert ".hidden_module.py" not in file_paths  # not in include pattern
        assert "package.json" not in file_paths  # gitignored, not rescued
        assert "image.png" not in file_paths  # binary
    
    def test_exclude_patterns(self, temp_repo):
        """Test EXCLUDE patterns add additional exclusions."""
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(None, cli_exclude=["*.md", "src/utils.py"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_names = [f.name for f in files]
        
        # Should include non-excluded files
        assert "main.py" in file_names
        assert "test.py" in file_names
        assert "module.py" in file_names
        assert "data.json" in file_names
        assert "config.yaml" in file_names
        
        # Should exclude based on patterns
        assert "README.md" not in file_names
        assert "index.md" not in file_names
        assert "api.md" not in file_names
        assert "utils.py" not in file_names
    
    def test_pattern_precedence(self, temp_repo):
        """Test the precedence: ONLY > INCLUDE rescue > normal exclusions."""
        gitignore_parser = GitignoreParser(temp_repo)
        
        # Test 1: ONLY overrides everything
        llm_parser = LlmMdParser(None, 
                                cli_only=["build/*.js"],
                                cli_include=["*.md"],
                                cli_exclude=["build/*"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Only build/*.js should be included despite exclude pattern
        assert file_paths == ["build/output.js"]
        
        # Test 2: INCLUDE rescues from exclusions when no ONLY
        llm_parser = LlmMdParser(None,
                                cli_include=["build/*.js", "*.md"],
                                cli_exclude=["*.md"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # MD files should be included (rescued by include) despite exclude
        assert "README.md" in file_paths
        assert "docs/index.md" in file_paths
        assert "build/output.js" in file_paths  # rescued from gitignore
        # Regular files still included
        assert "main.py" in file_paths
    
    def test_llm_md_file_patterns(self, temp_repo):
        """Test patterns from llm.md file."""
        # Create llm.md with patterns
        llm_md_content = """# Test llm.md

ONLY:
*.py
.github/**

INCLUDE:
build/*.js

EXCLUDE:
test.py
**/utils.py
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # ONLY patterns should take precedence
        assert "main.py" in file_paths
        assert "src/module.py" in file_paths
        assert ".github/workflows/test.yml" in file_paths
        
        # Files not matching ONLY patterns should be excluded
        assert "README.md" not in file_paths
        assert "build/output.js" not in file_paths  # INCLUDE ignored when ONLY exists
    
    def test_cli_overrides_file_patterns(self, temp_repo):
        """Test CLI patterns override file patterns."""
        # Create llm.md with patterns
        llm_md_content = """
ONLY:
*.md

INCLUDE:
*.py

EXCLUDE:
README.md
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        
        # CLI only patterns should override file only patterns
        llm_parser = LlmMdParser(llm_md_path, cli_only=["*.py"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should use CLI only pattern, not file only pattern
        assert "main.py" in file_paths
        assert "README.md" not in file_paths
        
        # When file has ONLY patterns but CLI has none, file ONLY patterns still apply
        # Create a new llm.md without ONLY patterns to test include override
        llm_md_content2 = """
INCLUDE:
*.py

EXCLUDE:
README.md
"""
        llm_md_path.write_text(llm_md_content2)
        
        # CLI include patterns should override file include patterns
        llm_parser = LlmMdParser(llm_md_path, cli_include=["*.json"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_names = [f.name for f in files]
        
        # Should see json rescued via CLI include override
        assert "data.json" in file_names
        
        # CLI exclude patterns are additive with file patterns
        llm_parser = LlmMdParser(llm_md_path, cli_exclude=["*.md"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_names = [f.name for f in files]
        
        # Both CLI and file excludes should apply
        assert "README.md" not in file_names  # excluded by both
        assert "index.md" not in file_names  # excluded by CLI
    
    def test_complex_patterns(self, temp_repo):
        """Test complex glob patterns."""
        gitignore_parser = GitignoreParser(temp_repo)
        
        # Test wildcard patterns
        llm_parser = LlmMdParser(None, cli_only=["**/*.py", "!**/__pycache__/**"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        assert "main.py" in file_paths
        assert "src/module.py" in file_paths
        assert "src/.hidden_module.py" in file_paths
        # Note: pathspec doesn't support ! negation, so __pycache__ would be included
        # if it had .py files matching the pattern
    
    def test_empty_patterns(self, temp_repo):
        """Test behavior with empty pattern lists."""
        gitignore_parser = GitignoreParser(temp_repo)
        
        # Empty lists should behave like no patterns
        llm_parser = LlmMdParser(None, cli_only=[], cli_include=[], cli_exclude=[])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        
        # Should behave like default
        file_names = [f.name for f in files]
        assert "README.md" in file_names
        assert "main.py" in file_names
        assert ".hidden_file" not in file_names


class TestSequentialPatternProcessing:
    """Test new mode-based sequential pattern processing for RepoScanner."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository structure for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create test file structure
        files = [
            "README.md",
            "main.py",
            "test.py", 
            ".hidden_file",
            ".github/workflows/test.yml",
            "src/module.py",
            "src/utils.py", 
            "src/.hidden_module.py",
            "docs/index.md",
            "docs/api.md",
            "node_modules/package.json",
            "build/output.js",
            "__pycache__/cache.pyc",
            "data.json",
            "config.yaml",
            "image.png",
            "archive.zip"
        ]
        
        for file_path in files:
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Content of {file_path}")
        
        # Create .gitignore
        gitignore_content = """
node_modules/
build/
*.pyc
__pycache__/
"""
        (repo_path / ".gitignore").write_text(gitignore_content)
        
        yield repo_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_whitelist_mode_sequential_processing(self, temp_repo):
        """Test WHITELIST mode starts with empty set and adds files sequentially."""
        # Create llm.md with WHITELIST mode
        llm_md_content = """WHITELIST:
src/
*.py

EXCLUDE:
src/utils.py

INCLUDE:
docs/*.md
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should include files matching WHITELIST implicit patterns
        assert "src/module.py" in file_paths
        assert "main.py" in file_paths
        assert "test.py" in file_paths
        
        # Should exclude src/utils.py due to EXCLUDE section
        assert "src/utils.py" not in file_paths
        
        # Should include docs/*.md due to INCLUDE section
        assert "docs/index.md" in file_paths
        assert "docs/api.md" in file_paths
        
        # Should NOT include files not matching WHITELIST patterns
        assert "README.md" not in file_paths
        assert "data.json" not in file_paths
        assert "config.yaml" not in file_paths
    
    def test_blacklist_mode_sequential_processing(self, temp_repo):
        """Test BLACKLIST mode starts with all files and removes files sequentially."""
        # Create llm.md with BLACKLIST mode
        llm_md_content = """BLACKLIST:
*.py
docs/

INCLUDE:
src/utils.py
docs/api.md
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should exclude Python files due to BLACKLIST implicit patterns
        assert "main.py" not in file_paths
        assert "test.py" not in file_paths
        assert "src/module.py" not in file_paths
        
        # Should include src/utils.py due to INCLUDE section (rescued)
        assert "src/utils.py" in file_paths
        
        # Should exclude docs/ due to BLACKLIST implicit patterns
        assert "docs/index.md" not in file_paths
        
        # Should include docs/api.md due to INCLUDE section (rescued)
        assert "docs/api.md" in file_paths
        
        # Should include other files not matching BLACKLIST patterns
        assert "README.md" in file_paths
        assert "data.json" in file_paths
        assert "config.yaml" in file_paths
    
    def test_default_exclusions_with_options(self, temp_repo):
        """Test that default exclusions are applied based on options."""
        # Create llm.md with options controlling default exclusions
        llm_md_content = """WHITELIST:
**/*

OPTIONS:
respect_gitignore: false
include_hidden: true
include_binary: false
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should include gitignored files (respect_gitignore=false)
        assert "node_modules/package.json" in file_paths
        assert "build/output.js" in file_paths
        
        # Should include hidden files (include_hidden=true)
        assert ".hidden_file" in file_paths
        assert ".github/workflows/test.yml" in file_paths
        assert "src/.hidden_module.py" in file_paths
        
        # Should exclude binary files (include_binary=false)
        assert "image.png" not in file_paths
        assert "archive.zip" not in file_paths
    
    def test_options_flags_override_default_exclusions(self, temp_repo):
        """Test that CLI options override default exclusion behavior."""
        # Create llm.md with default options
        llm_md_content = """BLACKLIST:

OPTIONS:
respect_gitignore: true
include_hidden: false
include_binary: false
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        
        # TODO: This test will need CLI option integration 
        # For now, test that scanner respects options from parser
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should exclude gitignored files (respect_gitignore=true)
        assert "node_modules/package.json" not in file_paths
        assert "build/output.js" not in file_paths
        
        # Should exclude hidden files (include_hidden=false)
        assert ".hidden_file" not in file_paths
        assert ".github/workflows/test.yml" not in file_paths
        
        # Should exclude binary files (include_binary=false)
        assert "image.png" not in file_paths
        assert "archive.zip" not in file_paths
    
    def test_scanner_works_with_updated_parser_interface(self, temp_repo):
        """Test scanner works with new parser methods: get_mode(), get_sections(), get_options()."""
        # Create llm.md with multiple sections
        llm_md_content = """WHITELIST:
*.py

EXCLUDE:
test_*.py

INCLUDE:
test_main.py

OPTIONS:
output: custom.md
respect_gitignore: true
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        # Create test_main.py for the test
        (temp_repo / "test_main.py").write_text("test content")
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        
        # Verify parser interface works
        assert llm_parser.get_mode() == "WHITELIST"
        sections = llm_parser.get_sections()
        assert len(sections) >= 3  # WHITELIST, EXCLUDE, INCLUDE
        options = llm_parser.get_options()
        assert options.get("output") == "custom.md"
        
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should include Python files
        assert "main.py" in file_paths
        
        # Should exclude test.py (matches test_*.py pattern)
        assert "test.py" not in file_paths
        
        # Should include test_main.py (rescued by INCLUDE)
        assert "test_main.py" in file_paths
    
    def test_sequential_processing_order_matters(self, temp_repo):
        """Test that sections are processed in order and later sections can override earlier ones."""
        # Create llm.md where section order matters
        llm_md_content = """WHITELIST:
*.py

EXCLUDE:
test.py

INCLUDE:
test.py

EXCLUDE:
main.py
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # test.py should be included (INCLUDE overrides earlier EXCLUDE)
        assert "test.py" in file_paths
        
        # main.py should be excluded (final EXCLUDE takes precedence)
        assert "main.py" not in file_paths
        
        # Other Python files should be included
        assert "src/module.py" in file_paths
        assert "src/utils.py" in file_paths
    
    def test_empty_mode_sections_handled_gracefully(self, temp_repo):
        """Test that empty sections are handled without errors."""
        # Create llm.md with empty sections
        llm_md_content = """WHITELIST:

EXCLUDE:

INCLUDE:

OPTIONS:
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        # Should not crash
        files = scanner.scan()
        
        # With empty WHITELIST, should have no files (except maybe rescued by default exclusions logic)
        # This tests the edge case handling
        assert isinstance(files, list)
    
    def test_legacy_format_still_works(self, temp_repo):
        """Test that existing legacy ONLY/INCLUDE/EXCLUDE format still works."""
        # Create llm.md with legacy format (no mode declaration)
        llm_md_content = """ONLY:
*.py

INCLUDE:
*.md

EXCLUDE:
test_*.py
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        llm_parser = LlmMdParser(llm_md_path)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should behave like before - ONLY patterns take precedence
        assert "main.py" in file_paths
        assert "test.py" in file_paths  # ONLY overrides EXCLUDE
        assert "src/module.py" in file_paths
        
        # Should not include non-matching files even if INCLUDE exists
        assert "README.md" not in file_paths  # ONLY takes precedence over INCLUDE