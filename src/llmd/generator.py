from pathlib import Path
from typing import List
import datetime


class MarkdownGenerator:
    """Generate markdown output with table of contents."""
    
    def generate(self, files: List[Path], repo_path: Path) -> str:
        """Generate the complete markdown document."""
        sections = []
        
        # Add header
        header = self._generate_header(repo_path, len(files))
        sections.append(header)
        
        # Generate TOC
        toc = self._generate_toc(files, repo_path)
        sections.append(toc)
        
        # Add file contents
        for file in files:
            section = self._generate_file_section(file, repo_path)
            sections.append(section)
        
        return '\n\n'.join(sections)
    
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