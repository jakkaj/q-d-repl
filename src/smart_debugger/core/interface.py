"""Abstract interface and data models for language-specific debuggers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DebugResult(BaseModel):
    """Standardized result from any language debugger."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool
    result: Any = None
    output: str = ""
    error: Optional[str] = None
    language: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BreakpointInfo(BaseModel):
    """Information about a breakpoint."""
    id: Optional[int] = None
    verified: bool = False
    line: int
    column: Optional[int] = None
    source: Optional[str] = None
    message: Optional[str] = None


class StackFrame(BaseModel):
    """Stack frame information."""
    id: int
    name: str
    source: Optional[str] = None
    line: int
    column: Optional[int] = None


class DebuggerInterface(ABC):
    """Abstract interface for language-specific debuggers."""
    
    @abstractmethod
    def debug(self, file_path: str, line_number: int, expression: str, 
             args: Optional[List[str]] = None, quiet_mode: bool = False) -> DebugResult:
        """
        Debug a file at specified line with given expression.
        
        Args:
            file_path: Path to the file to debug
            line_number: Line number to set breakpoint at
            expression: Expression to evaluate at breakpoint
            args: Optional command-line arguments
            quiet_mode: Whether to minimize output
            
        Returns:
            DebugResult with evaluation result or error
        """
        pass
    
    @abstractmethod
    def supports_file(self, file_path: str) -> bool:
        """
        Check if this debugger can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this debugger can handle the file
        """
        pass
    
    @abstractmethod
    def get_language_name(self) -> str:
        """
        Return the language name this debugger handles.
        
        Returns:
            Language name (e.g., 'python', 'csharp', 'javascript')
        """
        pass
    
    @abstractmethod
    def validate_environment(self) -> bool:
        """
        Check if required tools/dependencies are available.
        
        Returns:
            True if all requirements are met
        """
        pass