import pathspec
from pathlib import Path
from typing import List, Optional


class GitignoreParser:
    """Parse and apply .gitignore rules."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.spec = self._load_gitignore()
    
    def _load_gitignore(self) -> Optional[pathspec.PathSpec]:
        """Load .gitignore file and create PathSpec."""
        gitignore_path = self.repo_path / '.gitignore'
        if not gitignore_path.exists():
            return None
        
        patterns = gitignore_path.read_text(encoding='utf-8').splitlines()
        # Filter out comments and empty lines
        patterns = [p.strip() for p in patterns if p.strip() and not p.strip().startswith('#')]
        
        if not patterns:
            return None
            
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    
    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on .gitignore rules."""
        if not self.spec:
            return False
        
        # Get relative path from repo root
        try:
            rel_path = path.relative_to(self.repo_path)
        except ValueError:
            return True  # Path outside repo
        
        return self.spec.match_file(str(rel_path))


class LlmMdParser:
    """Parse llm.md configuration file."""
    
    def __init__(self, config_path: Optional[Path], cli_include: Optional[List[str]] = None, cli_exclude: Optional[List[str]] = None, cli_only: Optional[List[str]] = None):
        self.config_path = config_path
        self.include_patterns: List[str] = []
        self.exclude_patterns: List[str] = []
        self.only_patterns: List[str] = []
        self.cli_include = cli_include or []
        self.cli_exclude = cli_exclude or []
        self.cli_only = cli_only or []
        self._parse_config()
    
    def _parse_config(self):
        """Parse the llm.md configuration file."""
        if not self.config_path or not self.config_path.exists():
            return
        
        content = self.config_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for section headers
            if line.upper() == 'ONLY:':
                current_section = 'only'
                continue
            elif line.upper() == 'INCLUDE:':
                current_section = 'include'
                continue
            elif line.upper() == 'EXCLUDE:' or line.upper() == 'NOT INCLUDE:':
                current_section = 'exclude'
                continue
            
            # Add pattern to appropriate list
            if current_section == 'only':
                self.only_patterns.append(line)
            elif current_section == 'include':
                self.include_patterns.append(line)
            elif current_section == 'exclude':
                self.exclude_patterns.append(line)
    
    def has_only_patterns(self) -> bool:
        """Check if there are any only patterns specified."""
        return bool(self.only_patterns or self.cli_only)
    
    def has_include_patterns(self) -> bool:
        """Check if there are any include patterns specified."""
        return bool(self.include_patterns or self.cli_include)
    
    def should_include(self, path: Path, repo_path: Path) -> bool:
        """Check if a file should be included based on INCLUDE patterns."""
        # Combine CLI and config patterns (CLI takes precedence if both exist)
        all_patterns = self.cli_include if self.cli_include else self.include_patterns
        
        if not all_patterns:
            return True  # If no include patterns, include everything
        
        try:
            rel_path = path.relative_to(repo_path)
        except ValueError:
            return False
        
        rel_path_str = str(rel_path)
        
        # Check if file matches any include pattern
        spec = pathspec.PathSpec.from_lines('gitwildmatch', all_patterns)
        return spec.match_file(rel_path_str)
    
    def should_exclude(self, path: Path, repo_path: Path) -> bool:
        """Check if a file should be excluded based on EXCLUDE patterns."""
        # Combine CLI and config patterns (both are additive for excludes)
        all_patterns = self.cli_exclude + self.exclude_patterns
        
        if not all_patterns:
            return False
        
        try:
            rel_path = path.relative_to(repo_path)
        except ValueError:
            return True
        
        rel_path_str = str(rel_path)
        
        # Check if file matches any exclude pattern
        spec = pathspec.PathSpec.from_lines('gitwildmatch', all_patterns)
        return spec.match_file(rel_path_str)
    
    def matches_only(self, path: Path, repo_path: Path) -> bool:
        """Check if a file matches ONLY patterns."""
        # Combine CLI and config patterns (CLI takes precedence if both exist)
        all_patterns = self.cli_only if self.cli_only else self.only_patterns
        
        if not all_patterns:
            return False
        
        try:
            rel_path = path.relative_to(repo_path)
        except ValueError:
            return False
        
        rel_path_str = str(rel_path)
        
        # Check if file matches any only pattern
        spec = pathspec.PathSpec.from_lines('gitwildmatch', all_patterns)
        return spec.match_file(rel_path_str)