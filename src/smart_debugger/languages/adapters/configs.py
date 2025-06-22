"""Language-specific adapter configurations for DAP debugging."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
import os
import shutil
from pathlib import Path


class AdapterConfig(BaseModel):
    """Configuration for a debug adapter."""
    model_config = ConfigDict(extra='allow')
    
    language: str
    command: List[str]
    transport: str = Field(..., pattern="^(stdio|tcp)$")
    port: Optional[int] = Field(None, ge=1, le=65535)
    launch_type: str = ""
    file_extensions: List[str] = Field(default_factory=list)
    timeout: int = Field(30, ge=1, le=300)
    
    def validate_command(self) -> bool:
        """Check if the adapter command is available."""
        if not self.command:
            return False
        
        # Check if the first command (executable) is available
        executable = self.command[0]
        return shutil.which(executable) is not None
    
    def get_launch_config(self, file_path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get language-specific launch configuration."""
        base_config = {
            'type': self.launch_type,
            'name': f'Smart Debugger - {self.language}',
            'request': 'launch',
        }
        
        # Add language-specific configuration
        if self.language == 'python':
            return {
                **base_config,
                'program': file_path,
                'args': args or [],
                'console': 'internalConsole',
                'stopOnEntry': False,
                'python': self.command[0] if self.command else 'python'
            }
        
        elif self.language in ['csharp', 'fsharp', 'vbnet']:
            # For .NET, we need to find the compiled DLL
            dll_path = self._find_dotnet_dll(file_path)
            return {
                **base_config,
                'program': dll_path,
                'args': args or [],
                'cwd': str(Path(file_path).parent),
                'console': 'internalConsole',
                'stopOnEntry': False,
                'preLaunchTask': 'build'
            }
        
        elif self.language in ['javascript', 'typescript']:
            return {
                **base_config,
                'program': file_path,
                'args': args or [],
                'console': 'integratedTerminal',
                'stopOnEntry': False,
                'runtimeExecutable': 'node',
                'runtimeArgs': ['--inspect-brk=9229'] if self.transport == 'tcp' else []
            }
        
        elif self.language == 'go':
            return {
                **base_config,
                'mode': 'debug',
                'program': str(Path(file_path).parent),
                'args': args or [],
                'showGlobalVariables': True
            }
        
        elif self.language == 'rust':
            # For Rust, we need the executable path
            exe_path = self._find_rust_executable(file_path)
            return {
                **base_config,
                'program': exe_path,
                'args': args or [],
                'cwd': str(Path(file_path).parent),
                'console': 'internalConsole',
                'stopOnEntry': False
            }
        
        elif self.language == 'java':
            return {
                **base_config,
                'mainClass': self._get_java_main_class(file_path),
                'classpath': str(Path(file_path).parent),
                'args': args or [],
                'console': 'internalConsole',
                'stopOnEntry': False
            }
        
        else:
            # Generic configuration
            return {
                **base_config,
                'program': file_path,
                'args': args or []
            }
    
    def _find_dotnet_dll(self, source_file: str) -> str:
        """Find the compiled DLL for a .NET source file."""
        source_path = Path(source_file)
        project_dir = source_path.parent
        
        # Look for project file
        project_files = list(project_dir.glob('*.csproj')) + list(project_dir.glob('*.fsproj'))
        if not project_files:
            raise ValueError(f"No .NET project file found in {project_dir}")
        
        project_file = project_files[0]
        project_name = project_file.stem
        
        # Look for compiled DLL in typical output locations
        possible_paths = [
            project_dir / 'bin' / 'Debug' / 'net6.0' / f'{project_name}.dll',
            project_dir / 'bin' / 'Debug' / 'net7.0' / f'{project_name}.dll',
            project_dir / 'bin' / 'Debug' / 'net8.0' / f'{project_name}.dll',
            project_dir / 'bin' / 'Release' / 'net6.0' / f'{project_name}.dll',
            project_dir / 'bin' / 'Release' / 'net7.0' / f'{project_name}.dll',
            project_dir / 'bin' / 'Release' / 'net8.0' / f'{project_name}.dll',
        ]
        
        for dll_path in possible_paths:
            if dll_path.exists():
                return str(dll_path)
        
        raise ValueError(f"Compiled DLL not found for {project_name}. Please build the project first.")
    
    def _find_rust_executable(self, source_file: str) -> str:
        """Find the compiled executable for a Rust source file."""
        source_path = Path(source_file)
        project_dir = source_path
        
        # Find Cargo.toml
        while project_dir.parent != project_dir:
            if (project_dir / 'Cargo.toml').exists():
                break
            project_dir = project_dir.parent
        else:
            raise ValueError(f"Cargo.toml not found for {source_file}")
        
        # Parse project name from Cargo.toml
        cargo_toml = project_dir / 'Cargo.toml'
        project_name = project_dir.name  # Default fallback
        
        try:
            with open(cargo_toml, 'r') as f:
                for line in f:
                    if line.strip().startswith('name ='):
                        project_name = line.split('=')[1].strip().strip('"\'')
                        break
        except:
            pass
        
        # Look for executable
        exe_path = project_dir / 'target' / 'debug' / project_name
        if not exe_path.exists():
            raise ValueError(f"Rust executable not found: {exe_path}. Please build with 'cargo build'.")
        
        return str(exe_path)
    
    def _get_java_main_class(self, source_file: str) -> str:
        """Extract the main class name from a Java source file."""
        source_path = Path(source_file)
        
        # Try to extract class name from file
        try:
            with open(source_file, 'r') as f:
                content = f.read()
                
            # Look for public class declaration
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', content)
            if class_match:
                return class_match.group(1)
        except:
            pass
        
        # Fallback to filename without extension
        return source_path.stem


# Predefined adapter configurations
ADAPTER_CONFIGS: Dict[str, AdapterConfig] = {
    'python': AdapterConfig(
        language='python',
        command=['python', '-m', 'debugpy', '--listen', 'localhost:5678', '--wait-for-client'],
        transport='tcp',
        port=5678,
        launch_type='python',
        file_extensions=['.py', '.pyw', '.pyi'],
        timeout=30
    ),
    
    'csharp': AdapterConfig(
        language='csharp',
        command=['netcoredbg', '--interpreter=vscode'],
        transport='stdio',
        launch_type='coreclr',
        file_extensions=['.cs', '.csx'],
        timeout=30
    ),
    
    'fsharp': AdapterConfig(
        language='fsharp',
        command=['netcoredbg', '--interpreter=vscode'],
        transport='stdio',
        launch_type='coreclr',
        file_extensions=['.fs', '.fsx', '.fsi'],
        timeout=30
    ),
    
    'vbnet': AdapterConfig(
        language='vbnet',
        command=['netcoredbg', '--interpreter=vscode'],
        transport='stdio',
        launch_type='coreclr',
        file_extensions=['.vb'],
        timeout=30
    ),
    
    'javascript': AdapterConfig(
        language='javascript',
        command=['node', '--inspect-brk=9229'],
        transport='tcp',
        port=9229,
        launch_type='node',
        file_extensions=['.js', '.mjs', '.cjs', '.jsx'],
        timeout=30
    ),
    
    'typescript': AdapterConfig(
        language='typescript',
        command=['node', '--inspect-brk=9229', '--require', 'ts-node/register'],
        transport='tcp',
        port=9229,
        launch_type='node',
        file_extensions=['.ts', '.tsx'],
        timeout=30
    ),
    
    'go': AdapterConfig(
        language='go',
        command=['dlv', 'dap'],
        transport='stdio',
        launch_type='go',
        file_extensions=['.go'],
        timeout=30
    ),
    
    'rust': AdapterConfig(
        language='rust',
        command=['rust-gdb', '--interpreter=dap'],
        transport='stdio',
        launch_type='rust',
        file_extensions=['.rs'],
        timeout=45  # Rust can be slower
    ),
    
    'java': AdapterConfig(
        language='java',
        command=['java', '-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005'],
        transport='tcp',
        port=5005,
        launch_type='java',
        file_extensions=['.java'],
        timeout=30
    ),
    
    'cpp': AdapterConfig(
        language='cpp',
        command=['gdb', '--interpreter=dap'],
        transport='stdio',
        launch_type='cppdbg',
        file_extensions=['.cpp', '.cxx', '.cc', '.c++'],
        timeout=30
    ),
    
    'c': AdapterConfig(
        language='c',
        command=['gdb', '--interpreter=dap'],
        transport='stdio',
        launch_type='cppdbg',
        file_extensions=['.c', '.h'],
        timeout=30
    ),
}


def get_adapter_config(language: str) -> Optional[AdapterConfig]:
    """Get adapter configuration for a language."""
    return ADAPTER_CONFIGS.get(language)


def get_available_adapters() -> Dict[str, AdapterConfig]:
    """Get all adapter configurations where the command is available."""
    available = {}
    for language, config in ADAPTER_CONFIGS.items():
        if config.validate_command():
            available[language] = config
    return available


def register_adapter_config(language: str, config: AdapterConfig):
    """Register a new adapter configuration."""
    ADAPTER_CONFIGS[language] = config


def list_supported_languages() -> List[str]:
    """Get list of all supported languages."""
    return list(ADAPTER_CONFIGS.keys())


def list_available_languages() -> List[str]:
    """Get list of languages with available adapters."""
    return list(get_available_adapters().keys())