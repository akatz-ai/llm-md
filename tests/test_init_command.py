"""
Tests for llmd init Command with Template Generation (Task 5)

This file tests the init subcommand functionality:
- llmd init creates default template
- Template type options: -w/--whitelist, -b/--blacklist, --minimal  
- Templates match exact PRD format
- Graceful failure when llm.md already exists
- CLI help integration
- Flag validation for mutually exclusive options
"""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from llmd.cli import main


class TestInitCommandBasicFunctionality:
    """Test basic init command functionality."""
    
    def test_init_command_exists_in_help(self):
        """Test that init command appears in main help."""
        runner = CliRunner()
        
        # Test main help shows init command
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'init' in result.output.lower()
    
    def test_init_help_shows_command_options(self):
        """Test that init --help shows proper options."""
        runner = CliRunner()
        
        # Test init command help
        result = runner.invoke(main, ['init', '--help'])
        assert result.exit_code == 0
        assert '-w' in result.output or '--whitelist' in result.output
        assert '-b' in result.output or '--blacklist' in result.output
        assert '--minimal' in result.output

    def test_init_creates_default_template(self):
        """Test that 'llmd init' creates default blacklist template."""
        runner = CliRunner()
        
        # Change to temp directory
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['init'])
            assert result.exit_code == 0
            
            # Check that llm.md was created
            llm_md = Path('llm.md')
            assert llm_md.exists()
            
            # Check content matches default blacklist template
            content = llm_md.read_text()
            assert 'BLACKLIST:' in content
            assert 'OPTIONS:' in content
            assert 'output: llm-context.md' in content
            assert 'respect_gitignore: true' in content
            assert 'include_hidden: false' in content
            assert 'include_binary: false' in content


class TestInitTemplateTypes:
    """Test different template type generation."""
    
    def test_init_whitelist_template(self):
        """Test that 'llmd init -w' creates whitelist template."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test short flag
            result = runner.invoke(main, ['init', '-w'])
            assert result.exit_code == 0
            
            llm_md = Path('llm.md')
            assert llm_md.exists()
            
            content = llm_md.read_text()
            assert 'WHITELIST:' in content
            assert 'src/' in content
            assert 'lib/' in content or '*.py' in content
            assert 'OPTIONS:' in content
            assert 'EXCLUDE:' in content
            assert 'INCLUDE:' in content
    
    def test_init_whitelist_template_long_flag(self):
        """Test that 'llmd init --whitelist' creates whitelist template."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test long flag
            result = runner.invoke(main, ['init', '--whitelist'])
            assert result.exit_code == 0
            
            llm_md = Path('llm.md')
            assert llm_md.exists()
            
            content = llm_md.read_text()
            assert 'WHITELIST:' in content
    
    def test_init_blacklist_template(self):
        """Test that 'llmd init -b' creates blacklist template."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test short flag
            result = runner.invoke(main, ['init', '-b'])
            assert result.exit_code == 0
            
            llm_md = Path('llm.md')
            assert llm_md.exists()
            
            content = llm_md.read_text()
            assert 'BLACKLIST:' in content
            assert 'tests/' in content
            assert 'node_modules/' in content or '__pycache__/' in content
            assert 'OPTIONS:' in content
            assert 'INCLUDE:' in content
    
    def test_init_blacklist_template_long_flag(self):
        """Test that 'llmd init --blacklist' creates blacklist template."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test long flag
            result = runner.invoke(main, ['init', '--blacklist'])
            assert result.exit_code == 0
            
            llm_md = Path('llm.md')
            assert llm_md.exists()
            
            content = llm_md.read_text()
            assert 'BLACKLIST:' in content
    
    def test_init_minimal_template(self):
        """Test that 'llmd init --minimal' creates minimal template."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['init', '--minimal'])
            assert result.exit_code == 0
            
            llm_md = Path('llm.md')
            assert llm_md.exists()
            
            content = llm_md.read_text()
            # Minimal template should have mode and basic OPTIONS only
            assert 'WHITELIST:' in content or 'BLACKLIST:' in content
            assert 'OPTIONS:' in content
            assert 'output: llm-context.md' in content
            # Should NOT have extensive patterns or complex sections
            assert content.count('\n') < 10  # Keep it minimal


class TestInitTemplateContent:
    """Test that templates match exact PRD format specifications."""
    
    def test_default_template_matches_prd_format(self):
        """Test that default template follows PRD format exactly."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['init'])
            assert result.exit_code == 0
            
            content = Path('llm.md').read_text()
            
            # Check PRD format requirements
            lines = content.split('\n')
            
            # Mode must be first non-comment line
            non_comment_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            assert non_comment_lines[0].startswith('BLACKLIST:')
            
            # Must have OPTIONS section
            assert 'OPTIONS:' in content
            assert 'output: llm-context.md' in content
            assert 'respect_gitignore: true' in content
            assert 'include_hidden: false' in content
            assert 'include_binary: false' in content
    
    def test_whitelist_template_matches_prd_format(self):
        """Test that whitelist template follows PRD format exactly."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['init', '-w'])
            assert result.exit_code == 0
            
            content = Path('llm.md').read_text()
            lines = content.split('\n')
            
            # Mode must be first non-comment line
            non_comment_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            assert non_comment_lines[0].startswith('WHITELIST:')
            
            # Must have proper sections
            assert 'OPTIONS:' in content
            assert 'EXCLUDE:' in content
            assert 'INCLUDE:' in content
    
    def test_blacklist_template_matches_prd_format(self):
        """Test that blacklist template follows PRD format exactly."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['init', '-b'])
            assert result.exit_code == 0
            
            content = Path('llm.md').read_text()
            lines = content.split('\n')
            
            # Mode must be first non-comment line  
            non_comment_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            assert non_comment_lines[0].startswith('BLACKLIST:')
            
            # Must have proper sections
            assert 'OPTIONS:' in content
            assert 'INCLUDE:' in content


class TestInitErrorHandling:
    """Test error handling for init command."""
    
    def test_init_fails_when_llm_md_exists(self):
        """Test that init fails gracefully when llm.md already exists."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Create existing llm.md
            Path('llm.md').write_text('WHITELIST:\nexisting content')
            
            # Try to init - should fail
            result = runner.invoke(main, ['init'])
            assert result.exit_code != 0
            assert 'already exists' in result.output.lower() or 'exist' in result.output.lower()
            
            # Original content should be preserved
            content = Path('llm.md').read_text()
            assert 'existing content' in content
    
    def test_init_flags_are_mutually_exclusive(self):
        """Test that init template flags are mutually exclusive."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test -w and -b together
            result = runner.invoke(main, ['init', '-w', '-b'])
            assert result.exit_code != 0
            assert 'mutually exclusive' in result.output.lower()
            
            # Test -w and --minimal together
            result = runner.invoke(main, ['init', '-w', '--minimal'])
            assert result.exit_code != 0
            assert 'mutually exclusive' in result.output.lower()
            
            # Test -b and --minimal together
            result = runner.invoke(main, ['init', '-b', '--minimal'])
            assert result.exit_code != 0
            assert 'mutually exclusive' in result.output.lower()
            
            # Test all three together
            result = runner.invoke(main, ['init', '-w', '-b', '--minimal'])
            assert result.exit_code != 0
            assert 'mutually exclusive' in result.output.lower()


class TestInitSuccessMessages:
    """Test success messages and user feedback."""
    
    def test_init_provides_success_message(self):
        """Test that init provides clear success message."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['init'])
            assert result.exit_code == 0
            assert 'created' in result.output.lower() or 'generated' in result.output.lower()
            assert 'llm.md' in result.output
    
    def test_init_success_message_indicates_template_type(self):
        """Test that success message indicates which template type was created."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test whitelist template
            result = runner.invoke(main, ['init', '-w'])
            assert result.exit_code == 0
            assert 'whitelist' in result.output.lower()
            
        with runner.isolated_filesystem():
            # Test blacklist template  
            result = runner.invoke(main, ['init', '-b'])
            assert result.exit_code == 0
            assert 'blacklist' in result.output.lower()
            
        with runner.isolated_filesystem():
            # Test minimal template
            result = runner.invoke(main, ['init', '--minimal'])
            assert result.exit_code == 0
            assert 'minimal' in result.output.lower()


class TestInitCommandIntegration:
    """Test that init command integrates properly with main CLI."""
    
    def test_init_command_in_main_cli_help(self):
        """Test that init appears in main CLI help as a subcommand."""
        runner = CliRunner()
        
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        # Should show commands section with init
        assert 'Commands:' in result.output or 'commands:' in result.output
        assert 'init' in result.output
    
    def test_main_command_still_works_after_init_added(self):
        """Test that main command functionality still works after adding init."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "test.py").write_text("print('test')")
            
            # Main command should still work
            result = runner.invoke(main, [str(repo_path), '-w', '*.py', '--dry-run'])
            assert result.exit_code == 0
            assert "+test.py" in result.output