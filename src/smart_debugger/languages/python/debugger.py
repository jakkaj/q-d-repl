"""Python debugger implementation using sys.settrace."""

import sys
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import contextlib
import io
import tempfile

from ...core.interface import DebuggerInterface, DebugResult
from ...non_interactive import NonInteractiveDebugger, DebuggerExit


class PythonDebugger(DebuggerInterface):
    """Python debugger implementation using sys.settrace."""
    
    def debug(
        self, 
        file_path: str, 
        line_number: int, 
        expression: str, 
        args: Optional[List[str]] = None, 
        quiet_mode: bool = False
    ) -> DebugResult:
        """
        Debug a Python file at specified line with given expression.
        
        Args:
            file_path: Path to the Python file to debug
            line_number: Line number to set breakpoint at
            expression: Python expression to evaluate at breakpoint
            args: Optional command-line arguments
            quiet_mode: Whether to minimize output
            
        Returns:
            DebugResult with evaluation result or error
        """
        try:
            # Determine if this is a pytest test file
            is_pytest = self._is_pytest_file(file_path)
            
            if is_pytest:
                return self._debug_pytest(file_path, line_number, expression, args, quiet_mode)
            else:
                return self._debug_standalone(file_path, line_number, expression, args, quiet_mode)
                
        except Exception as e:
            return DebugResult(
                success=False,
                result=None,
                output="",
                error=str(e),
                language="python"
            )
    
    def _is_pytest_file(self, file_path: str) -> bool:
        """Check if the file is a pytest test file."""
        path = Path(file_path)
        
        # Check filename patterns
        if path.name.startswith('test_') or path.name.endswith('_test.py'):
            return True
        
        # Check if file contains test functions/classes
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if 'import pytest' in content or 'from pytest' in content:
                    return True
                if 'def test_' in content or 'class Test' in content:
                    return True
        except Exception:
            pass
        
        return False
    
    def _debug_pytest(
        self, 
        file_path: str, 
        line_number: int, 
        expression: str, 
        args: Optional[List[str]], 
        quiet_mode: bool
    ) -> DebugResult:
        """Debug a pytest test file."""
        # Create a temporary script to run the debugger
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'''
import sys
sys.path.insert(0, {repr(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))})

from smart_debugger.non_interactive import run_non_interactive_debug

exit_code = run_non_interactive_debug(
    file_path={repr(file_path)},
    line_no={line_number},
    command={repr(expression)},
    pytest_args={repr(args or [])},
    quiet_mode={quiet_mode}
)
sys.exit(exit_code)
''')
            script_path = f.name
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output
            output = result.stdout
            error = result.stderr if result.returncode != 0 else None
            
            # Extract REPL output if in quiet mode
            if quiet_mode and 'Breakpoint hit:' in result.stderr:
                # The actual output is in stdout
                repl_output = output.strip()
            else:
                # Extract output between markers
                repl_output = self._extract_repl_output(output)
            
            return DebugResult(
                success=result.returncode == 0,
                result=repl_output if repl_output else None,
                output=output if not quiet_mode else "",
                error=error,
                language="python"
            )
            
        finally:
            # Clean up temp file
            try:
                os.unlink(script_path)
            except:
                pass
    
    def _debug_standalone(
        self, 
        file_path: str, 
        line_number: int, 
        expression: str, 
        args: Optional[List[str]], 
        quiet_mode: bool
    ) -> DebugResult:
        """Debug a standalone Python script."""
        # Create a temporary script to run the debugger
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'''
import sys
import os
sys.path.insert(0, {repr(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))})

from smart_debugger.standalone import run_standalone_debug

exit_code = run_standalone_debug(
    file_path={repr(file_path)},
    line_no={line_number},
    command={repr(expression)},
    script_args={repr(args or [])},
    quiet_mode={quiet_mode}
)
sys.exit(exit_code)
''')
            script_path = f.name
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output
            output = result.stdout
            error = result.stderr if result.returncode != 0 else None
            
            # Extract REPL output
            if quiet_mode and 'Breakpoint hit:' in result.stderr:
                repl_output = output.strip()
            else:
                repl_output = self._extract_repl_output(output)
            
            return DebugResult(
                success=result.returncode == 0,
                result=repl_output if repl_output else None,
                output=output if not quiet_mode else "",
                error=error,
                language="python"
            )
            
        finally:
            # Clean up temp file
            try:
                os.unlink(script_path)
            except:
                pass
    
    def _extract_repl_output(self, output: str) -> Optional[str]:
        """Extract REPL output from between markers."""
        if not output:
            return None
        
        # Look for output between breakpoint markers
        lines = output.split('\n')
        in_breakpoint = False
        repl_lines = []
        
        for line in lines:
            if '=== BREAKPOINT HIT ===' in line:
                in_breakpoint = True
                continue
            elif '=== END BREAKPOINT ===' in line:
                in_breakpoint = False
                break
            elif in_breakpoint:
                repl_lines.append(line)
        
        if repl_lines:
            # Skip the "Executing:" line if present
            if repl_lines and repl_lines[0].startswith('Executing:'):
                repl_lines = repl_lines[1:]
            
            return '\n'.join(repl_lines).strip()
        
        return None
    
    def supports_file(self, file_path: str) -> bool:
        """Check if this debugger can handle the given file."""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() in ['.py', '.pyw', '.pyi']:
            return True
        
        # Check shebang
        if path.exists():
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#!') and 'python' in first_line:
                        return True
            except:
                pass
        
        return False
    
    def get_language_name(self) -> str:
        """Return the language name this debugger handles."""
        return "python"
    
    def validate_environment(self) -> bool:
        """Check if required tools/dependencies are available."""
        try:
            # Check Python is available (it should be since we're running in Python)
            import sys
            if sys.version_info < (3, 8):
                return False
            
            # Check pytest is available
            try:
                import pytest
            except ImportError:
                return False
            
            # Check that sys.settrace is available
            if not hasattr(sys, 'settrace'):
                return False
            
            return True
        except Exception:
            return False