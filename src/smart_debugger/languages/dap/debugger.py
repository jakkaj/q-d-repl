"""Generic DAP debugger implementation for multi-language support."""

import os
import time
import logging
from typing import Optional, List
from pathlib import Path

from ...core.interface import DebuggerInterface, DebugResult
from .service import DAPService
from ..adapters.configs import get_adapter_config, AdapterConfig


logger = logging.getLogger(__name__)


class DAPDebugger(DebuggerInterface):
    """Generic debugger that uses DAP for any language."""
    
    def __init__(self, language: str):
        """
        Initialize DAP debugger for a specific language.
        
        Args:
            language: Language identifier (e.g., 'csharp', 'javascript', 'go')
        """
        self.language = language
        self.adapter_config = get_adapter_config(language)
        
        if not self.adapter_config:
            raise ValueError(f"No adapter configuration found for language: {language}")
        
        self.dap_service = None
    
    def debug(
        self, 
        file_path: str, 
        line_number: int, 
        expression: str, 
        args: Optional[List[str]] = None, 
        quiet_mode: bool = False
    ) -> DebugResult:
        """
        Debug a file at specified line with given expression using DAP.
        
        Args:
            file_path: Path to the file to debug
            line_number: Line number to set breakpoint at
            expression: Expression to evaluate at breakpoint
            args: Optional command-line arguments
            quiet_mode: Whether to minimize output
            
        Returns:
            DebugResult with evaluation result or error
        """
        try:
            # Ensure file exists
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return DebugResult(
                    success=False,
                    result=None,
                    output="",
                    error=f"File not found: {file_path}",
                    language=self.language
                )
            
            # Create DAP service
            adapter_dict = self.adapter_config.model_dump()
            self.dap_service = DAPService(adapter_dict)
            
            with self.dap_service:
                # Start the adapter
                if not self.dap_service.start_adapter():
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error=f"Failed to start {self.language} debug adapter",
                        language=self.language
                    )
                
                # Initialize DAP session
                init_response = self.dap_service.initialize()
                if not init_response.get('success', True):
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error=f"Failed to initialize debug adapter: {init_response.get('message', 'Unknown error')}",
                        language=self.language
                    )
                
                # Set breakpoint
                bp_response = self.dap_service.set_breakpoints(file_path, [line_number])
                if not bp_response.get('success', True):
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error=f"Failed to set breakpoint: {bp_response.get('message', 'Unknown error')}",
                        language=self.language
                    )
                
                # Get launch configuration
                launch_config = self.adapter_config.get_launch_config(file_path, args)
                
                # Launch program
                launch_response = self.dap_service.launch(launch_config)
                if not launch_response.get('success', True):
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error=f"Failed to launch program: {launch_response.get('message', 'Unknown error')}",
                        language=self.language
                    )
                
                # Configuration done
                self.dap_service.configuration_done()
                
                # Wait for breakpoint hit (stopped event)
                stopped_event = self.dap_service.wait_for_event('stopped', timeout=30)
                if not stopped_event:
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error="Breakpoint not hit within timeout",
                        language=self.language
                    )
                
                # Check if stopped due to breakpoint
                stop_reason = stopped_event.get('body', {}).get('reason', '')
                if stop_reason != 'breakpoint':
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error=f"Program stopped due to: {stop_reason}",
                        language=self.language
                    )
                
                # Get thread and frame information
                thread_id = stopped_event.get('body', {}).get('threadId', 1)
                
                stack_response = self.dap_service.get_stack_trace(thread_id)
                if not stack_response.get('success', True):
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error="Failed to get stack trace",
                        language=self.language
                    )
                
                stack_frames = stack_response.get('body', {}).get('stackFrames', [])
                if not stack_frames:
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error="No stack frames available",
                        language=self.language
                    )
                
                frame_id = stack_frames[0].get('id', 0)
                
                # Evaluate expression
                eval_response = self.dap_service.evaluate(expression, frame_id)
                
                if eval_response.get('success', True):
                    result_value = eval_response.get('body', {}).get('result', '')
                    result_type = eval_response.get('body', {}).get('type', '')
                    
                    # Format result based on quiet mode
                    if quiet_mode:
                        output = ""
                    else:
                        output = f"Expression: {expression}\nResult: {result_value}"
                        if result_type:
                            output += f"\nType: {result_type}"
                    
                    return DebugResult(
                        success=True,
                        result=result_value,
                        output=output,
                        error=None,
                        language=self.language,
                        metadata={
                            'type': result_type,
                            'frame_id': frame_id,
                            'thread_id': thread_id
                        }
                    )
                else:
                    error_msg = eval_response.get('message', 'Expression evaluation failed')
                    return DebugResult(
                        success=False,
                        result=None,
                        output="",
                        error=error_msg,
                        language=self.language
                    )
        
        except Exception as e:
            logger.error(f"DAP debugging error for {self.language}: {e}")
            return DebugResult(
                success=False,
                result=None,
                output="",
                error=str(e),
                language=self.language
            )
        
        finally:
            # Cleanup is handled by the context manager
            pass
    
    def supports_file(self, file_path: str) -> bool:
        """Check if this debugger can handle the given file."""
        if not self.adapter_config:
            return False
        
        path = Path(file_path)
        ext = path.suffix.lower()
        
        return ext in self.adapter_config.file_extensions
    
    def get_language_name(self) -> str:
        """Return the language name this debugger handles."""
        return self.language
    
    def validate_environment(self) -> bool:
        """Check if required tools/dependencies are available."""
        if not self.adapter_config:
            return False
        
        # Check if adapter command is available
        return self.adapter_config.validate_command()
    
    def get_adapter_info(self) -> dict:
        """Get information about the adapter configuration."""
        if not self.adapter_config:
            return {'available': False}
        
        return {
            'available': self.validate_environment(),
            'command': self.adapter_config.command,
            'transport': self.adapter_config.transport,
            'port': self.adapter_config.port,
            'file_extensions': self.adapter_config.file_extensions,
            'timeout': self.adapter_config.timeout
        }