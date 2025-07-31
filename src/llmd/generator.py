from pathlib import Path
from typing import List
import datetime
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed


class MarkdownGenerator:
    """Generate markdown output with table of contents."""
    
    def __init__(self):
        # Use thread pool for I/O-bound operations
        self.max_workers = min(32, (multiprocessing.cpu_count() or 1) * 4)
    
    def generate(self, files: List[Path], repo_path: Path) -> str:
        """Optimized generation with parallel file reading."""
        sections = []
        
        # Add header
        header = self._generate_header(repo_path, len(files))
        sections.append(header)
        
        # Generate TOC
        toc = self._generate_toc(files, repo_path)
        sections.append(toc)
        
        # Process files in parallel
        file_sections = self._process_files_parallel(files, repo_path)
        sections.extend(file_sections)
        
        return '\n\n'.join(sections)
    
    def _process_files_parallel(self, files: List[Path], repo_path: Path) -> List[str]:
        """Process multiple files in parallel."""
        file_sections = [None] * len(files)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file processing tasks
            future_to_index = {
                executor.submit(self._generate_file_section_optimized, file, repo_path): i
                for i, file in enumerate(files)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    file_sections[index] = future.result()
                except Exception as e:
                    # Handle errors gracefully
                    file_sections[index] = f"## Error processing file\n\n```\n{str(e)}\n```"
        
        return file_sections
    
    def _generate_file_section_optimized(self, file: Path, repo_path: Path) -> str:
        """Optimized file section generation with chunk reading for large files."""
        rel_path = file.relative_to(repo_path)
        language = self._get_language(file)
        
        try:
            # Check file size first
            file_size = file.stat().st_size
            
            if file_size > 10_000_000:  # 10MB threshold
                content = "[File too large - content omitted]"
            elif file_size > 1_000_000:  # 1MB threshold - read in chunks
                content = self._read_large_file(file)
            else:
                content = file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = "[Binary or non-UTF-8 file - content omitted]"
        except Exception as e:
            content = f"[Error reading file: {e}]"
        
        return f"## {rel_path}\n\n```{language}\n{content}\n```"
    
    def _read_large_file(self, file: Path, chunk_size: int = 65536) -> str:
        """Read large files in chunks to avoid memory spikes."""
        chunks = []
        with open(file, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
        return ''.join(chunks)
    
    def _generate_header(self, repo_path: Path, file_count: int) -> str:
        """Generate document header."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# LLM Context for {repo_path.name}

Generated on: {timestamp}  
Repository: `{repo_path}`  
Total files: {file_count}

---"""
    
    def _generate_anchor(self, text: str) -> str:
        """Generate anchor ID following GitHub Flavored Markdown rules.
        
        GitHub's auto-generation rules:
        - Convert to lowercase
        - Keep alphanumeric characters and underscores/hyphens
        - Remove dots, slashes, and other special characters
        - Don't replace with hyphens, just remove them
        """
        # Convert to lowercase
        anchor = text.lower()
        
        # Remove dots and slashes entirely (don't replace with hyphens)
        anchor = anchor.replace('.', '').replace('/', '')
        
        # Keep only alphanumeric, underscores, and hyphens
        import re
        anchor = re.sub(r'[^a-z0-9_-]', '', anchor)
        
        return anchor
    
    def _generate_toc(self, files: List[Path], repo_path: Path) -> str:
        """Generate table of contents."""
        lines = ["## Table of Contents\n"]
        
        for i, file in enumerate(files, 1):
            rel_path = file.relative_to(repo_path)
            # Create anchor-friendly link using GitHub standard
            anchor = self._generate_anchor(str(rel_path))
            lines.append(f"{i}. [{rel_path}](#{anchor})")
        
        return '\n'.join(lines)
    
    def _generate_file_section(self, file: Path, repo_path: Path) -> str:
        """Generate a section for a single file."""
        rel_path = file.relative_to(repo_path)
        
        # Determine language for syntax highlighting
        language = self._get_language(file)
        
        # Read file content
        try:
            content = file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = "[Binary or non-UTF-8 file - content omitted]"
        except Exception as e:
            content = f"[Error reading file: {e}]"
        
        # Build section - let markdown processor auto-generate anchors
        section = f"""## {rel_path}

```{language}
{content}
```"""
        
        return section
    
    def _get_language(self, file: Path) -> str:
        """Get language identifier for syntax highlighting."""
        suffix_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.R': 'r',
            '.m': 'objc',
            '.mm': 'objc',
            '.pl': 'perl',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.lua': 'lua',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'conf',
            '.md': 'markdown',
            '.rst': 'rst',
            '.tex': 'latex',
            '.dockerfile': 'dockerfile',
            '.Dockerfile': 'dockerfile',
            '.makefile': 'makefile',
            '.Makefile': 'makefile',
            '.cmake': 'cmake',
            '.vim': 'vim',
            '.vue': 'vue',
            '.svelte': 'svelte'
        }
        
        # Check exact filename matches first
        filename_to_lang = {
            'Dockerfile': 'dockerfile',
            'Makefile': 'makefile',
            'CMakeLists.txt': 'cmake',
            'requirements.txt': 'text',
            'package.json': 'json',
            'tsconfig.json': 'json',
            '.gitignore': 'gitignore',
            '.dockerignore': 'dockerignore'
        }
        
        if file.name in filename_to_lang:
            return filename_to_lang[file.name]
        
        return suffix_to_lang.get(file.suffix.lower(), 'text')