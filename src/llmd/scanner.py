from pathlib import Path
from typing import List, Dict, Any, Set
import click
import pathspec
from .parser import GitignoreParser, LlmMdParser


class RepoScanner:
    """Scan repository files with filtering."""
    
    # Common binary and non-text file extensions to skip
    BINARY_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        '.exe', '.dll', '.so', '.dylib', '.bin', '.obj',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        '.pyc', '.pyo', '.class', '.o', '.a',
        '.db', '.sqlite', '.sqlite3'
    }
    
    # Directories to always skip
    SKIP_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', 
        'env', '.env', '.tox', '.pytest_cache', '.mypy_cache',
        'dist', 'build', 'target', '.next', '.nuxt'
    }
    
    def __init__(self, repo_path: Path, gitignore_parser: GitignoreParser, 
                 llm_parser: LlmMdParser, verbose: bool = False):
        self.repo_path = repo_path
        self.gitignore_parser = gitignore_parser
        self.llm_parser = llm_parser
        self.verbose = verbose
    
    def scan(self) -> List[Path]:
        """Scan repository and return list of files to include."""
        # Get mode and sections from parser
        mode = self.llm_parser.get_mode()
        
        # Handle legacy format or missing mode
        if mode is None:
            return self._scan_legacy()
        
        sections = self.llm_parser.get_sections()
        options = self.llm_parser.get_options()
        
        # 1. Create initial file set based on mode
        if mode == "WHITELIST":
            files_set = set()  # Start empty
        else:  # BLACKLIST
            all_files = self._get_all_files()
            # Apply default exclusions to initial BLACKLIST set
            files_set = self._apply_default_exclusions(set(all_files), options)
        
        # 2. Process sections sequentially
        for section in sections:
            files_set = self._process_section(files_set, section, mode, options)
        
        # 4. Convert to sorted list and return
        files = list(files_set)
        files.sort()
        return files
    
    
    def _scan_all_files(self) -> List[Path]:
        """Scan all files (excluding those that should be skipped)."""
        files = []
        
        for path in self._walk_directory(self.repo_path):
            if not path.is_file():
                continue
            
            if not self._should_skip_file(path):
                files.append(path)
                if self.verbose:
                    click.echo(f"  + {path.relative_to(self.repo_path)}")
        
        return files
    
    def _walk_directory(self, directory: Path):
        """Walk directory tree, skipping certain directories."""
        for item in directory.iterdir():
            if item.is_dir():
                # Check if directory might have includes before skipping
                if self._might_have_includes_in_directory(item):
                    # Don't skip if includes might match files inside
                    pass
                elif item.name in self.SKIP_DIRS:
                    # Skip known problematic directories
                    continue
                elif item.name.startswith('.'):
                    # Skip hidden directories
                    continue
                
                yield from self._walk_directory(item)
            else:
                yield item
    
    def _might_have_includes_in_directory(self, directory: Path) -> bool:
        """Check if include patterns might match files in this directory."""
        if not self.llm_parser.has_include_patterns():
            return False
        
        # Get relative path from repo root
        try:
            rel_dir = directory.relative_to(self.repo_path)
        except ValueError:
            return False
        
        rel_dir_str = str(rel_dir) + '/'
        
        # Check if any include pattern might match files in this directory
        include_patterns = self.llm_parser.cli_include if self.llm_parser.cli_include else self.llm_parser.include_patterns
        
        for pattern in include_patterns:
            # Check if pattern could match something in this directory
            # This is a simple check - if the pattern starts with or contains the directory path
            if pattern.startswith(rel_dir_str) or f'**/{rel_dir.name}/' in pattern or pattern.startswith('**/'):
                return True
            # Also check if the directory is part of the pattern path
            pattern_parts = pattern.split('/')
            dir_parts = rel_dir_str.rstrip('/').split('/')
            if len(dir_parts) <= len(pattern_parts):
                matches = True
                for i, dir_part in enumerate(dir_parts):
                    if pattern_parts[i] != '**' and pattern_parts[i] != '*' and pattern_parts[i] != dir_part:
                        matches = False
                        break
                if matches:
                    return True
        
        return False
    
    def _should_skip_file(self, path: Path) -> bool:
        """Check if a file should be skipped."""
        # Check if file matches INCLUDE patterns first - these force-include files
        # according to PRD: "INCLUDE patterns can force-include files that would otherwise be excluded"
        file_is_rescued = (self.llm_parser.has_include_patterns() and 
                          self.llm_parser.should_include(path, self.repo_path))
        
        if file_is_rescued:
            # INCLUDE patterns force-include files, overriding all exclusions
            return False
        
        # Check EXCLUDE patterns from llm.md
        if self.llm_parser.should_exclude(path, self.repo_path):
            return True
        
        # Check binary extensions
        if path.suffix.lower() in self.BINARY_EXTENSIONS:
            return True
        
        # Check gitignore
        if self.gitignore_parser.should_ignore(path):
            return True
        
        # Skip hidden files
        if path.name.startswith('.'):
            return True
        
        return False
    
    # New methods for mode-based sequential processing
    
    def _scan_legacy(self) -> List[Path]:
        """Fallback to legacy INCLUDE/EXCLUDE behavior (ONLY patterns removed)."""
        files = []
        
        # Scan all files with normal filtering (no more ONLY patterns)
        files = self._scan_all_files_legacy()
        
        # Sort files for consistent output
        files.sort()
        return files
    
    def _scan_all_files_legacy(self) -> List[Path]:
        """Legacy scan all files method."""
        files = []
        
        for path in self._walk_directory(self.repo_path):
            if not path.is_file():
                continue
            
            if not self._should_skip_file(path):
                files.append(path)
                if self.verbose:
                    click.echo(f"  + {path.relative_to(self.repo_path)}")
        
        return files
    
    def _get_all_files(self) -> List[Path]:
        """Discover all files in repository, including those in normally skipped directories."""
        files = []
        
        for path in self._walk_absolutely_all_directories(self.repo_path):
            if path.is_file():
                files.append(path)
        
        return files
    
    def _walk_absolutely_all_directories(self, directory: Path):
        """Walk directory tree, including normally skipped directories (except .git)."""
        for item in directory.iterdir():
            if item.is_dir():
                # Only skip .git directory (always unsafe)
                if item.name == '.git':
                    continue
                yield from self._walk_absolutely_all_directories(item)
            else:
                yield item
    
    def _walk_all_directories(self, directory: Path):
        """Walk directory tree, skipping only always-skipped directories (for legacy compatibility)."""
        for item in directory.iterdir():
            if item.is_dir():
                # Skip always-skipped directories
                if item.name in self.SKIP_DIRS:
                    continue
                yield from self._walk_all_directories(item)
            else:
                yield item
    
    def _apply_default_exclusions(self, files: Set[Path], options: Dict[str, Any]) -> Set[Path]:
        """Apply default exclusions based on options."""
        filtered_files = set()
        
        # Get option values with defaults
        respect_gitignore = options.get('respect_gitignore', True)
        include_hidden = options.get('include_hidden', False)
        include_binary = options.get('include_binary', False)
        
        for file_path in files:
            # Check gitignore
            if respect_gitignore and self.gitignore_parser.should_ignore(file_path):
                continue
            
            # Check hidden files
            if not include_hidden and self._is_hidden_file(file_path):
                continue
            
            # Check binary files
            if not include_binary and file_path.suffix.lower() in self.BINARY_EXTENSIONS:
                continue
            
            filtered_files.add(file_path)
        
        return filtered_files
    
    def _is_hidden_file(self, file_path: Path) -> bool:
        """Check if a file or any of its parent directories are hidden."""
        try:
            rel_path = file_path.relative_to(self.repo_path)
        except ValueError:
            return True  # Outside repo
        
        # Check if file itself is hidden
        if file_path.name.startswith('.'):
            return True
        
        # Check if any parent directory is hidden
        for part in rel_path.parts[:-1]:  # Exclude the filename itself
            if part.startswith('.'):
                return True
        
        return False
    
    def _should_include_file(self, file_path: Path, options: Dict[str, Any]) -> bool:
        """Check if a file should be included based on options (for WHITELIST/INCLUDE)."""
        # Get option values with defaults
        respect_gitignore = options.get('respect_gitignore', True)
        include_hidden = options.get('include_hidden', False)
        include_binary = options.get('include_binary', False)
        
        # Check gitignore
        if respect_gitignore and self.gitignore_parser.should_ignore(file_path):
            return False
        
        # Check hidden files
        if not include_hidden and self._is_hidden_file(file_path):
            return False
        
        # Check binary files
        if not include_binary and file_path.suffix.lower() in self.BINARY_EXTENSIONS:
            return False
        
        return True
    
    def _process_section(self, files: Set[Path], section: Dict[str, Any], mode: str, options: Dict[str, Any]) -> Set[Path]:
        """Process a single pattern section."""
        section_type = section.get('type')
        patterns = section.get('patterns', [])
        
        if not patterns:
            return files  # No patterns to process
        
        # Skip OPTIONS sections
        if section_type == 'OPTIONS':
            return files
        
        # Create pathspec for pattern matching
        try:
            spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
        except Exception:
            # If patterns are invalid, skip this section
            return files
        
        if section_type in ('WHITELIST', 'INCLUDE'):
            # Add matching files (WHITELIST in WHITELIST mode, INCLUDE in any mode)
            if section_type == 'WHITELIST' or section_type == 'INCLUDE':
                # Find all files that match and add them
                all_files = self._get_all_files()
                for file_path in all_files:
                    try:
                        rel_path = file_path.relative_to(self.repo_path)
                        if spec.match_file(str(rel_path)):
                            # Apply default exclusions for WHITELIST mode or INCLUDE sections
                            if self._should_include_file(file_path, options):
                                files.add(file_path)
                                if self.verbose:
                                    click.echo(f"  + {rel_path}")
                    except ValueError:
                        continue  # Skip files outside repo
        
        elif section_type in ('BLACKLIST', 'EXCLUDE'):
            # Remove matching files (BLACKLIST in BLACKLIST mode, EXCLUDE in any mode)
            if section_type == 'BLACKLIST' or section_type == 'EXCLUDE':
                files_to_remove = set()
                for file_path in files:
                    try:
                        rel_path = file_path.relative_to(self.repo_path)
                        if spec.match_file(str(rel_path)):
                            files_to_remove.add(file_path)
                            if self.verbose:
                                click.echo(f"  - {rel_path}")
                    except ValueError:
                        continue  # Skip files outside repo
                
                files -= files_to_remove
        
        return files