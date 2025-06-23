from pathlib import Path
from typing import List
import click
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
        files = []
        
        # If there are ONLY patterns, use them exclusively
        if self.llm_parser.has_only_patterns():
            files = self._scan_with_only()
        else:
            # Otherwise scan all files with normal filtering
            files = self._scan_all_files()
        
        # Sort files for consistent output
        files.sort()
        
        return files
    
    def _scan_with_only(self) -> List[Path]:
        """Scan only files matching ONLY patterns, ignoring all exclusions."""
        files = []
        
        for path in self._walk_directory(self.repo_path, check_only=True):
            if not path.is_file():
                continue
            
            # Check if file matches ONLY patterns - ignore all exclusions
            if self.llm_parser.matches_only(path, self.repo_path):
                files.append(path)
                if self.verbose:
                    click.echo(f"  + {path.relative_to(self.repo_path)}")
        
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
    
    def _walk_directory(self, directory: Path, check_only: bool = False):
        """Walk directory tree, skipping certain directories."""
        for item in directory.iterdir():
            if item.is_dir():
                # If using ONLY patterns, don't skip any directories
                if not check_only:
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
                
                yield from self._walk_directory(item, check_only=check_only)
            else:
                yield item
    
    def _might_have_includes_in_directory(self, directory: Path) -> bool:
        """Check if include or only patterns might match files in this directory."""
        if not self.llm_parser.has_include_patterns() and not self.llm_parser.has_only_patterns():
            return False
        
        # Get relative path from repo root
        try:
            rel_dir = directory.relative_to(self.repo_path)
        except ValueError:
            return False
        
        rel_dir_str = str(rel_dir) + '/'
        
        # Check if any include or only pattern might match files in this directory
        include_patterns = self.llm_parser.cli_include if self.llm_parser.cli_include else self.llm_parser.include_patterns
        only_patterns = self.llm_parser.cli_only if self.llm_parser.cli_only else self.llm_parser.only_patterns
        all_patterns = include_patterns + only_patterns
        
        for pattern in all_patterns:
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
        # If file matches INCLUDE patterns, it should be rescued from exclusions
        if self.llm_parser.has_include_patterns() and self.llm_parser.should_include(path, self.repo_path):
            return False
        
        # Check binary extensions
        if path.suffix.lower() in self.BINARY_EXTENSIONS:
            return True
        
        # Check gitignore
        if self.gitignore_parser.should_ignore(path):
            return True
        
        # Check exclude patterns from llm.md
        if self.llm_parser.should_exclude(path, self.repo_path):
            return True
        
        # Skip hidden files
        if path.name.startswith('.'):
            return True
        
        return False