import pathspec
from pathlib import Path
from typing import List, Optional, Dict, Any, Union


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
        # Legacy format attributes
        self.include_patterns: List[str] = []
        self.exclude_patterns: List[str] = []
        self.only_patterns: List[str] = []
        self.cli_include = cli_include or []
        self.cli_exclude = cli_exclude or []
        self.cli_only = cli_only or []
        
        # New mode-based format attributes
        self.mode: Optional[str] = None
        self.implicit_patterns: List[str] = []
        self.sections: List[Dict[str, Any]] = []
        self.options: Dict[str, Any] = {}
        
        self._parse_config()
    
    def _parse_config(self):
        """Parse the llm.md configuration file."""
        if not self.config_path or not self.config_path.exists():
            return
        
        content = self.config_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        
        # Try to parse as new mode-based format first
        if self._try_parse_mode_based_format(lines):
            return
        
        # Fall back to legacy format
        self._parse_legacy_format(lines)
    
    def _try_parse_mode_based_format(self, lines: List[str]) -> bool:
        """Try to parse as new mode-based format. Returns True if successful."""
        # Find first non-comment, non-empty line
        first_content_line = None
        first_content_idx = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                first_content_line = stripped
                first_content_idx = i
                break
        
        if not first_content_line:
            return False
        
        # Check if first line is a mode declaration
        if first_content_line.upper() in ('WHITELIST:', 'BLACKLIST:'):
            self.mode = first_content_line.upper().rstrip(':')
            self._parse_mode_based_sections(lines, first_content_idx + 1)
            return True
        
        return False
    
    def _parse_mode_based_sections(self, lines: List[str], start_idx: int):
        """Parse sections in mode-based format."""
        current_section = {'type': self.mode, 'patterns': []}
        current_section_type = self.mode
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for new section headers
            if line.upper() in ('EXCLUDE:', 'INCLUDE:', 'OPTIONS:'):
                # Save current section if it has content
                if current_section['patterns'] or current_section_type == self.mode or current_section_type == 'OPTIONS':
                    self.sections.append(current_section.copy())
                
                # Start new section
                current_section_type = line.upper().rstrip(':')
                current_section = {'type': current_section_type, 'patterns': []}
                continue
            
            # Handle content based on section type
            if current_section_type == 'OPTIONS':
                self._parse_option_line(line)
            else:
                current_section['patterns'].append(line)
                
                # If this is the mode section, also add to implicit patterns
                if current_section_type == self.mode:
                    self.implicit_patterns.append(line)
        
        # Save final section
        if current_section['patterns'] or current_section_type == self.mode or current_section_type == 'OPTIONS':
            self.sections.append(current_section)
    
    def _parse_option_line(self, line: str):
        """Parse a line in OPTIONS section."""
        if ':' not in line:
            return
        
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        
        # Convert value to appropriate type
        self.options[key] = self._convert_option_value(value)
    
    def _convert_option_value(self, value: str) -> Union[str, bool, int, float]:
        """Convert option value to appropriate Python type."""
        # Boolean conversion
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Default to string
        return value
    
    def _parse_legacy_format(self, lines: List[str]):
        """Parse legacy ONLY/INCLUDE/EXCLUDE format."""
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
    
    # New mode-based format methods
    
    def get_mode(self) -> Optional[str]:
        """Get the current mode (WHITELIST/BLACKLIST) or None for legacy format."""
        return self.mode
    
    def get_sections(self) -> List[Dict[str, Any]]:
        """Get ordered list of pattern sections."""
        return self.sections.copy()
    
    def get_options(self) -> Dict[str, Any]:
        """Get parsed OPTIONS as dictionary."""
        return self.options.copy()
    
    def get_implicit_patterns(self) -> List[str]:
        """Get implicit patterns following mode declaration."""
        return self.implicit_patterns.copy()