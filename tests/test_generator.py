import pytest
from pathlib import Path
import tempfile
import shutil
from llmd.generator import MarkdownGenerator


class TestMarkdownGenerator:
    """Test the markdown generation functionality."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository with test files."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create test files with various naming patterns
        test_files = [
            "main.py",
            "test.file.py",
            "src/main.py", 
            "src/test.config.json",
            "docs/readme.md",
            "config.yaml",
            "package.json"
        ]
        
        for file_path in test_files:
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"# Content of {file_path}\nSample file content")
        
        yield repo_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_toc_anchor_generation_for_simple_files(self, temp_repo):
        """Test TOC anchor generation for files without dots in names."""
        generator = MarkdownGenerator()
        files = [temp_repo / "main.py"]
        
        result = generator.generate(files, temp_repo)
        
        # Check that TOC contains correct anchor link
        assert "[main.py](#mainpy)" in result
        
        # Check that section header has matching anchor
        assert "## main.py" in result
        # The auto-generated anchor should be #mainpy (GitHub style)
    
    def test_toc_anchor_generation_for_files_with_dots(self, temp_repo):
        """Test TOC anchor generation for files with dots in names."""
        generator = MarkdownGenerator() 
        files = [temp_repo / "test.file.py"]
        
        result = generator.generate(files, temp_repo)
        
        # Check that TOC contains correct anchor link matching GitHub's auto-generation
        assert "[test.file.py](#testfilepy)" in result
        
        # Check that section header does NOT have custom anchor syntax
        assert "## test.file.py" in result
        assert "{#" not in result  # Should not contain custom anchor syntax
    
    def test_toc_anchor_generation_for_paths_with_slashes(self, temp_repo):
        """Test TOC anchor generation for file paths containing slashes."""
        generator = MarkdownGenerator()
        files = [temp_repo / "src" / "main.py"]
        
        result = generator.generate(files, temp_repo)
        
        # Check that TOC contains correct anchor link
        assert "[src/main.py](#srcmainpy)" in result
        
        # Check that section header matches
        assert "## src/main.py" in result
    
    def test_toc_anchor_generation_for_complex_paths(self, temp_repo):
        """Test TOC anchor generation for complex file paths with dots and slashes."""
        generator = MarkdownGenerator()
        files = [temp_repo / "src" / "test.config.json"]
        
        result = generator.generate(files, temp_repo)
        
        # Check that TOC contains correct anchor link
        assert "[src/test.config.json](#srctestconfigjson)" in result
        
        # Check that section header matches  
        assert "## src/test.config.json" in result
    
    def test_multiple_files_have_consistent_anchors(self, temp_repo):
        """Test that multiple files all have consistent anchor generation."""
        generator = MarkdownGenerator()
        files = [
            temp_repo / "main.py",
            temp_repo / "test.file.py",
            temp_repo / "src" / "main.py",
            temp_repo / "src" / "test.config.json"
        ]
        
        result = generator.generate(files, temp_repo)
        
        # Check all TOC entries have correct anchor format
        toc_entries = [
            "[main.py](#mainpy)",
            "[test.file.py](#testfilepy)", 
            "[src/main.py](#srcmainpy)",
            "[src/test.config.json](#srctestconfigjson)"
        ]
        
        for entry in toc_entries:
            assert entry in result
        
        # Check all section headers exist (without custom anchor syntax)
        section_headers = [
            "## main.py",
            "## test.file.py",
            "## src/main.py", 
            "## src/test.config.json"
        ]
        
        for header in section_headers:
            assert header in result
        
        # Ensure no custom anchor syntax is present
        assert "{#" not in result
    
    def test_anchor_generation_follows_github_standard(self, temp_repo):
        """Test that anchor generation follows GitHub Flavored Markdown standard."""
        generator = MarkdownGenerator()
        
        # Test edge cases for anchor generation
        test_cases = [
            ("file.name.py", "filenamepy"),
            ("my-file.py", "my-filepy"),
            ("file_name.py", "file_namepy"),
            ("File.Name.Py", "filenamepy"),  # should be lowercase
            ("file123.py", "file123py"),
            ("src/sub.dir/file.py", "srcsubdirfilepy")
        ]
        
        for filename, expected_anchor in test_cases:
            # Create test file
            file_path = temp_repo / filename.replace("/", "/")
            file_path.parent.mkdir(parents=True, exist_ok=True) 
            file_path.write_text("test content")
            
            result = generator.generate([file_path], temp_repo)
            
            # Check TOC entry uses expected anchor
            expected_toc_entry = f"[{filename}](#{expected_anchor})"
            assert expected_toc_entry in result
            
            # Clean up for next iteration
            file_path.unlink()
    
    def test_anchor_generation_helper_method(self, temp_repo):
        """Test the internal anchor generation method directly."""
        generator = MarkdownGenerator()
        
        # Test anchor generation for various inputs
        test_cases = [
            ("main.py", "mainpy"),
            ("test.file.py", "testfilepy"),
            ("src/main.py", "srcmainpy"), 
            ("src/test.config.json", "srctestconfigjson"),
            ("My-File.Test.Py", "my-filetestpy"),
            ("file_name.extension", "file_nameextension")
        ]
        
        for input_text, expected in test_cases:
            result = generator._generate_anchor(input_text)
            assert result == expected, f"Expected {expected}, got {result} for input {input_text}"
    
    def test_existing_functionality_not_broken(self, temp_repo):
        """Test that existing generator functionality still works correctly."""
        generator = MarkdownGenerator()
        files = [temp_repo / "main.py", temp_repo / "config.yaml"]
        
        result = generator.generate(files, temp_repo)
        
        # Check document structure is intact
        assert f"# LLM Context for {temp_repo.name}" in result
        assert "Generated on:" in result
        assert f"Repository: `{temp_repo}`" in result
        assert "Total files: 2" in result
        assert "## Table of Contents" in result
        
        # Check file contents are included
        assert "```python" in result  # For main.py
        assert "```yaml" in result    # For config.yaml
        assert "# Content of main.py" in result
        assert "# Content of config.yaml" in result