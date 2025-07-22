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
    
    def test_only_patterns_removed(self, temp_repo):
        """Test that ONLY patterns are no longer supported (Task 11)."""
        gitignore_parser = GitignoreParser(temp_repo)
        # cli_only parameter should no longer exist
        llm_parser = LlmMdParser(None)
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Without ONLY patterns, should behave like default (include all non-excluded files)
        assert "main.py" in file_paths
        assert "test.py" in file_paths
        assert "src/module.py" in file_paths
        assert "src/utils.py" in file_paths
        assert "README.md" in file_paths
        assert "data.json" in file_paths
        
        # Should still exclude hidden files, gitignored files, and binary files by default
        assert "src/.hidden_module.py" not in file_paths  # hidden
        assert ".github/workflows/test.yml" not in file_paths  # hidden dir
        assert "build/output.js" not in file_paths  # gitignored
        assert ".hidden_file" not in file_paths  # hidden
        assert "__pycache__/cache.pyc" not in file_paths  # gitignored
    
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
    
    def test_pattern_precedence_without_only(self, temp_repo):
        """Test the precedence: INCLUDE rescue > normal exclusions (Task 11: ONLY removed)."""
        gitignore_parser = GitignoreParser(temp_repo)
        
        # Test INCLUDE rescues from exclusions (no more ONLY patterns)
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
    
    def test_llm_md_file_patterns_without_only(self, temp_repo):
        """Test patterns from llm.md file without ONLY patterns (Task 11)."""
        # Create llm.md with patterns (ONLY section removed)
        llm_md_content = """# Test llm.md

INCLUDE:
build/*.js
.github/**
*.py

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
        
        # Should include normal files plus rescued files
        assert "main.py" in file_paths  # rescued by INCLUDE *.py
        assert "src/module.py" in file_paths  # rescued by INCLUDE *.py
        assert ".github/workflows/test.yml" in file_paths  # rescued by INCLUDE .github/**
        assert "build/output.js" in file_paths  # rescued by INCLUDE build/*.js
        assert "README.md" in file_paths  # normal file
        
        # test.py matches both INCLUDE *.py and EXCLUDE test.py
        # According to PRD, INCLUDE should force-include files that would otherwise be excluded
        assert "test.py" in file_paths  # force-included by INCLUDE *.py despite EXCLUDE test.py
        
        # src/utils.py matches both INCLUDE *.py and EXCLUDE **/utils.py
        # According to PRD, INCLUDE should force-include files that would otherwise be excluded  
        assert "src/utils.py" in file_paths  # force-included by INCLUDE *.py despite EXCLUDE **/utils.py
    
    def test_cli_overrides_file_patterns_without_only(self, temp_repo):
        """Test CLI patterns override file patterns (Task 11: ONLY patterns removed)."""
        # Create llm.md with patterns (no ONLY section)
        llm_md_content = """
INCLUDE:
*.py

EXCLUDE:
README.md
"""
        llm_md_path = temp_repo / "llm.md"
        llm_md_path.write_text(llm_md_content)
        
        gitignore_parser = GitignoreParser(temp_repo)
        
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
        """Test complex glob patterns (Task 11: ONLY patterns removed)."""
        gitignore_parser = GitignoreParser(temp_repo)
        
        # Test wildcard patterns with include instead of only
        llm_parser = LlmMdParser(None, cli_include=["**/*.py"])
        scanner = RepoScanner(temp_repo, gitignore_parser, llm_parser)
        files = scanner.scan()
        file_paths = [str(f.relative_to(temp_repo)) for f in files]
        
        # Should include all files plus rescued Python files
        assert "main.py" in file_paths
        assert "src/module.py" in file_paths
        assert "README.md" in file_paths  # also included (not only Python files)
        # Hidden Python files should be rescued by INCLUDE pattern
        assert "src/.hidden_module.py" in file_paths  # rescued by **/*.py pattern
    
    def test_empty_patterns(self, temp_repo):
        """Test behavior with empty pattern lists (Task 11: cli_only removed)."""
        gitignore_parser = GitignoreParser(temp_repo)
        
        # Empty lists should behave like no patterns (cli_only parameter removed)
        llm_parser = LlmMdParser(None, cli_include=[], cli_exclude=[])
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
            "test_main.py",  # Added to test test_*.py pattern
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
test*.py

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
        
        # Should exclude test.py (matches test*.py pattern)
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
    
    def test_legacy_format_without_only_still_works(self, temp_repo):
        """Test that legacy INCLUDE/EXCLUDE format still works (Task 11: ONLY removed)."""
        # Create llm.md with legacy format (no mode declaration, no ONLY section)
        llm_md_content = """INCLUDE:
*.md
*.py

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
        
        # Should include all normal files plus rescued files
        assert "main.py" in file_paths  # rescued by INCLUDE
        assert "src/module.py" in file_paths  # rescued by INCLUDE
        assert "README.md" in file_paths  # rescued by INCLUDE
        assert "docs/index.md" in file_paths  # rescued by INCLUDE
        assert "data.json" in file_paths  # normal file
        
        # Should exclude based on EXCLUDE patterns
        assert "test_main.py" not in file_paths  # excluded by test_*.py pattern