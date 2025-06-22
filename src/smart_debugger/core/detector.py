"""Language detection functionality for Smart Debugger."""

import os
from pathlib import Path
from typing import Optional, Dict, Set


class LanguageDetector:
    """Detects programming language from file extension and content."""
    
    # Primary mapping from file extensions to languages
    EXTENSION_MAP: Dict[str, str] = {
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        '.cs': 'csharp',
        '.csx': 'csharp',
        '.fs': 'fsharp',
        '.fsx': 'fsharp',
        '.fsi': 'fsharp',
        '.vb': 'vbnet',
        '.java': 'java',
        '.js': 'javascript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.cc': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.scala': 'scala',
        '.sc': 'scala',
        '.lua': 'lua',
        '.pl': 'perl',
        '.pm': 'perl',
        '.r': 'r',
        '.R': 'r',
        '.m': 'matlab',
        '.jl': 'julia',
        '.dart': 'dart',
        '.ex': 'elixir',
        '.exs': 'elixir',
        '.clj': 'clojure',
        '.cljs': 'clojure',
        '.erl': 'erlang',
        '.hrl': 'erlang',
        '.hs': 'haskell',
        '.lhs': 'haskell',
        '.ml': 'ocaml',
        '.mli': 'ocaml',
        '.nim': 'nim',
        '.cr': 'crystal',
        '.zig': 'zig',
    }
    
    # Shebang patterns to language mapping
    SHEBANG_PATTERNS: Dict[str, str] = {
        'python': 'python',
        'python2': 'python',
        'python3': 'python',
        'node': 'javascript',
        'nodejs': 'javascript',
        'ruby': 'ruby',
        'perl': 'perl',
        'php': 'php',
        'bash': 'bash',
        'sh': 'shell',
        'zsh': 'shell',
        'lua': 'lua',
        'julia': 'julia',
    }
    
    def __init__(self):
        """Initialize the language detector."""
        self._extension_map = self.EXTENSION_MAP.copy()
        self._shebang_patterns = self.SHEBANG_PATTERNS.copy()
    
    def detect_language(self, file_path: str) -> str:
        """
        Detect language from file extension and optionally content.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Language identifier (e.g., 'python', 'csharp', 'javascript')
            
        Raises:
            ValueError: If language cannot be detected
        """
        path = Path(file_path)
        
        # Try detection by file extension first
        language = self._detect_by_extension(path)
        if language:
            return language
        
        # Try detection by shebang if file exists
        if path.exists() and path.is_file():
            language = self._detect_by_shebang(path)
            if language:
                return language
        
        # Try detection by content patterns
        if path.exists() and path.is_file():
            language = self._detect_by_content(path)
            if language:
                return language
        
        raise ValueError(f"Cannot detect language for file: {file_path}")
    
    def _detect_by_extension(self, path: Path) -> Optional[str]:
        """Detect language by file extension."""
        # Get all suffixes to handle files like .spec.ts
        suffixes = path.suffixes
        
        # Try from most specific to least specific
        for i in range(len(suffixes)):
            ext = ''.join(suffixes[i:]).lower()
            if ext in self._extension_map:
                return self._extension_map[ext]
        
        return None
    
    def _detect_by_shebang(self, path: Path) -> Optional[str]:
        """Detect language by shebang line."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                
            if not first_line.startswith('#!'):
                return None
            
            # Extract the interpreter from shebang
            shebang = first_line[2:].strip()
            
            # Check for env usage (e.g., #!/usr/bin/env python3)
            if 'env' in shebang:
                parts = shebang.split()
                if len(parts) >= 2:
                    interpreter = parts[-1].split('/')[-1]
                else:
                    return None
            else:
                # Direct interpreter path (e.g., #!/usr/bin/python3)
                interpreter = shebang.split('/')[-1].split()[0]
            
            # Remove version numbers (python3 -> python)
            base_interpreter = interpreter.rstrip('0123456789.')
            
            # Look up in shebang patterns
            for pattern, language in self._shebang_patterns.items():
                if pattern in base_interpreter:
                    return language
            
        except (IOError, UnicodeDecodeError):
            pass
        
        return None
    
    def _detect_by_content(self, path: Path) -> Optional[str]:
        """Detect language by content patterns."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # Read first few lines for pattern detection
                lines = []
                for _ in range(20):  # Check first 20 lines
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.strip())
            
            content = '\n'.join(lines)
            
            # Python-specific patterns
            if any(pattern in content for pattern in ['import ', 'from ', 'def ', 'class ', '__name__']):
                if 'def ' in content or 'class ' in content or '__name__' in content:
                    return 'python'
            
            # JavaScript/TypeScript patterns
            if any(pattern in content for pattern in ['const ', 'let ', 'var ', 'function ', 'require(', 'import ']):
                if 'interface ' in content or 'type ' in content or ': ' in content:
                    return 'typescript'
                return 'javascript'
            
            # C# patterns
            if any(pattern in content for pattern in ['using ', 'namespace ', 'public class', 'private class']):
                return 'csharp'
            
            # Java patterns
            if any(pattern in content for pattern in ['package ', 'import java', 'public class', 'public static void main']):
                return 'java'
            
            # Go patterns
            if any(pattern in content for pattern in ['package main', 'package ', 'import (', 'func main()']):
                return 'go'
            
            # Rust patterns
            if any(pattern in content for pattern in ['fn main()', 'use ', 'mod ', 'impl ', 'struct ', 'enum ']):
                return 'rust'
            
        except (IOError, UnicodeDecodeError):
            pass
        
        return None
    
    def get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions."""
        return set(self._extension_map.keys())
    
    def is_supported(self, file_path: str) -> bool:
        """Check if a file is supported by trying to detect its language."""
        try:
            self.detect_language(file_path)
            return True
        except ValueError:
            return False
    
    def add_extension_mapping(self, extension: str, language: str):
        """Add a custom extension to language mapping."""
        self._extension_map[extension.lower()] = language
    
    def add_shebang_pattern(self, pattern: str, language: str):
        """Add a custom shebang pattern to language mapping."""
        self._shebang_patterns[pattern] = language