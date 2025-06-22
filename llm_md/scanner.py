from pathlib import Path
from typing import List, Set
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
        
        # If there are include patterns, only scan those
        if self.llm_parser.has_include_patterns():
            files = self._scan_with_includes()
        else:
            files = self._scan_all_files()
        
        # Sort files for consistent output
        files.sort()
        
        return files
    
    def _scan_with_includes(self) -> List[Path]:
        """Scan only files matching include patterns."""
        files = []
        
        for path in self._walk_directory(self.repo_path):
            if not path.is_file():
                continue
            
            # Check if file matches include patterns
            if self.llm_parser.should_include(path, self.repo_path):
                # Still check gitignore and exclude patterns
                if not self._should_skip_file(path):
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
    
    def _walk_directory(self, directory: Path):
        """Walk directory tree, skipping certain directories."""
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in self.SKIP_DIRS and not item.name.startswith('.'):
                    yield from self._walk_directory(item)
            else:
                yield item
    
    def _should_skip_file(self, path: Path) -> bool:
        """Check if a file should be skipped."""
        # Check binary extensions
        if path.suffix.lower() in self.BINARY_EXTENSIONS:
            return True
        
        # Check gitignore
        if self.gitignore_parser.should_ignore(path):
            return True
        
        # Check exclude patterns from llm.md
        if self.llm_parser.should_exclude(path, self.repo_path):
            return True
        
        # Skip hidden files (unless explicitly included)
        if path.name.startswith('.') and not self.llm_parser.has_include_patterns():
            return True
        
        return False