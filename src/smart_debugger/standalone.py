"""
Standalone Python file debugger.

This module provides debugging for any Python file without requiring pytest.
It supports scripts, modules, and packages with proper execution context.
"""

import runpy
import sys
from pathlib import Path
from typing import List

from .non_interactive import DebuggerExit, NonInteractiveDebugger


class StandaloneDebugger(NonInteractiveDebugger):
    """Debugger for standalone Python files without pytest."""

    def __init__(
        self,
        file_path: str,
        line_no: int,
        command: str,
        script_args: List[str] = None,
        quiet_mode: bool = False,
    ):
        super().__init__(file_path, line_no, command, quiet_mode)
        self.script_args = script_args or []
        self.standalone_mode = True  # Flag to prevent immediate exit


def run_standalone_debug(
    file_path: str,
    line_no: int,
    command: str,
    script_args: List[str],
    quiet_mode: bool = False,
    is_module: bool = False,
) -> int:
    """
    Run standalone Python file with debugging.

    Args:
        file_path: Path to the Python file or module name
        line_no: Line number to break at
        command: Command to execute at breakpoint
        script_args: Arguments to pass to the script
        quiet_mode: If True, show only REPL output
        is_module: If True, treat file_path as a module name

    Returns:
        Exit code (0 for success)
    """
    # Save original sys.argv and path
    original_argv = sys.argv.copy()
    original_path = sys.path.copy()

    try:
        if is_module:
            # Module mode: file_path is a module name
            module_name = file_path

            # Find the module file for debugging
            try:
                import importlib.util

                # First try to find the module itself
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    if not quiet_mode:
                        print(
                            f"Error: Module not found: {module_name}", file=sys.stderr
                        )
                    return 1

                # For packages, we need to find the __main__ module
                if spec.submodule_search_locations is not None:
                    # This is a package, look for __main__
                    main_spec = importlib.util.find_spec(f"{module_name}.__main__")
                    if main_spec and main_spec.origin:
                        module_file = main_spec.origin
                    else:
                        if not quiet_mode:
                            print(
                                f"Error: Module {module_name} is not runnable (no __main__.py)",
                                file=sys.stderr,
                            )
                        return 1
                elif spec.origin:
                    # This is a regular module
                    module_file = spec.origin
                else:
                    if not quiet_mode:
                        print(
                            f"Error: Cannot find source file for module {module_name}",
                            file=sys.stderr,
                        )
                    return 1

            except Exception as e:
                if not quiet_mode:
                    print(f"Error finding module {module_name}: {e}", file=sys.stderr)
                return 1

            # Create debugger with the actual file path
            debugger = StandaloneDebugger(
                module_file, line_no, command, script_args, quiet_mode
            )

            # Set up sys.argv for the module
            sys.argv = [module_name] + script_args

            # Set up trace function
            sys.settrace(debugger.trace_function)

            try:
                # Run the module
                runpy.run_module(module_name, run_name="__main__", alter_sys=True)

                # If in quiet mode and debugger has output, print it
                if quiet_mode and debugger.executed and debugger.repl_output:
                    sys.stdout.write(debugger.repl_output)
                    sys.stdout.flush()

            except DebuggerExit:
                # In standalone mode, we don't exit after breakpoint
                # But still print quiet mode output if needed
                if quiet_mode and debugger.executed and debugger.repl_output:
                    sys.stdout.write(debugger.repl_output)
                    sys.stdout.flush()
            except SystemExit as e:
                # Module called sys.exit()
                return e.code if isinstance(e.code, int) else 0
            except Exception:
                # Unhandled exception in module
                if not quiet_mode:
                    import traceback

                    traceback.print_exc()
                return 1

        else:
            # Script mode: file_path is a file path
            # Create debugger
            debugger = StandaloneDebugger(
                file_path, line_no, command, script_args, quiet_mode
            )

            # Resolve the file path
            file_path = Path(file_path).resolve()

            # Set up trace function
            sys.settrace(debugger.trace_function)

            # Set up sys.argv for the script
            sys.argv = [str(file_path)] + script_args

            # Get the directory of the script
            script_dir = str(file_path.parent)

            # Add script directory to sys.path (at the beginning)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)

            # Create globals dict with proper __name__ and __file__
            script_globals = {
                "__name__": "__main__",
                "__file__": str(file_path),
                "__cached__": None,
                "__doc__": None,
                "__loader__": None,
                "__package__": None,
                "__spec__": None,
            }

            # Read and compile the script
            with open(file_path, "rb") as f:
                source = f.read()

            # Compile the code
            try:
                code = compile(source, str(file_path), "exec")
            except SyntaxError as e:
                if not quiet_mode:
                    print(f"Syntax Error in {file_path}: {e}", file=sys.stderr)
                return 1

            # Execute the script
            try:
                exec(code, script_globals)

                # If in quiet mode and debugger has output, print it
                if quiet_mode and debugger.executed and debugger.repl_output:
                    sys.stdout.write(debugger.repl_output)
                    sys.stdout.flush()

            except DebuggerExit:
                # In standalone mode, we don't exit after breakpoint
                # Continue executing the rest of the script
                # But still print quiet mode output if needed
                if quiet_mode and debugger.executed and debugger.repl_output:
                    sys.stdout.write(debugger.repl_output)
                    sys.stdout.flush()
            except SystemExit as e:
                # Script called sys.exit()
                return e.code if isinstance(e.code, int) else 0
            except Exception:
                # Unhandled exception in script
                if not quiet_mode:
                    import traceback

                    traceback.print_exc()
                return 1

        # If we get here and debugger was executed, it's success
        if debugger.executed:
            return 0
        else:
            # Breakpoint was never hit
            if not quiet_mode:
                print(
                    f"Warning: Breakpoint at line {line_no} was never reached",
                    file=sys.stderr,
                )
            return 0

    finally:
        # Restore original sys.argv and path
        sys.argv = original_argv
        sys.path = original_path
        # Remove trace
        sys.settrace(None)
