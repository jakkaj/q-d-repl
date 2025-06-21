"""
Non-interactive debugger for LLM agents.

This module provides a completely non-interactive debugging tool that:
1. Sets a breakpoint at a specific line
2. Executes a command when the breakpoint is hit
3. Prints the output
4. Exits cleanly
"""

import sys
from pathlib import Path


class DebuggerExit(Exception):
    """Custom exception to signal clean exit after breakpoint."""


class NonInteractiveDebugger:
    """Debugger that executes commands and exits without any interaction."""

    def __init__(
        self, file_path: str, line_no: int, command: str, quiet_mode: bool = False
    ):
        # Resolve path once during initialization
        self.file_path = Path(file_path).resolve()
        self.file_path_str = str(self.file_path)  # Cache string representation
        self.line_no = line_no
        self.command = command
        self.executed = False
        self.quiet_mode = quiet_mode
        self.trace_active = True  # Track if we're still tracing
        self.should_exit = False  # Flag to trigger clean exit
        self.repl_output = None  # Store REPL output for quiet mode
        self.in_test = False  # Track if we're inside a test function
        self.standalone_mode = False  # Set to True in StandaloneDebugger
        # Cache for resolved paths to avoid repeated resolution
        self._path_cache = {}

    def trace_function(self, frame, event, arg):
        """Trace function that executes command at breakpoint and exits."""
        # Track if we're in a test function
        if event == "call":
            func_name = frame.f_code.co_name
            if func_name.startswith("test_") or func_name.startswith("Test"):
                self.in_test = True
        elif event == "return":
            func_name = frame.f_code.co_name
            if func_name.startswith("test_") or func_name.startswith("Test"):
                self.in_test = False

        # Only process line events when we haven't executed yet
        if event == "line" and not self.executed:
            try:
                # Get the current file and line
                filename = frame.f_code.co_filename
                lineno = frame.f_lineno

                # Quick rejection for obvious non-matches
                # This avoids expensive path resolution for most files
                if not filename.endswith(self.file_path.name):
                    return self.trace_function

                # Check cache first
                if filename in self._path_cache:
                    resolved_path = self._path_cache[filename]
                else:
                    # Only resolve if filename looks like it might match
                    resolved_path = str(Path(filename).resolve())
                    self._path_cache[filename] = resolved_path

                # Check if this is our breakpoint
                if resolved_path == self.file_path_str and lineno == self.line_no:
                    self.executed = True

                    # Print location info (unless in quiet mode)
                    if not self.quiet_mode:
                        print(f"\n=== BREAKPOINT HIT: {filename}:{lineno} ===")

                    # Get frame locals and globals for execution context
                    locals_dict = frame.f_locals
                    globals_dict = frame.f_globals

                    # Execute the command
                    if self.quiet_mode:
                        # In quiet mode, capture output for later
                        import io

                        output_buffer = io.StringIO()

                        # Store the current stdout (which might already be redirected)
                        current_stdout = sys.stdout

                        try:
                            # Temporarily set stdout to our buffer
                            sys.stdout = output_buffer

                            try:
                                # Try to evaluate as expression first
                                result = eval(self.command, globals_dict, locals_dict)
                                if result is not None:
                                    print(result)  # Use print so it goes to our buffer
                            except:
                                # If evaluation fails, try execution
                                try:
                                    exec(self.command, globals_dict, locals_dict)
                                except Exception as e:
                                    print(f"ERROR: {e}")
                        finally:
                            # Always restore stdout
                            sys.stdout = current_stdout

                        self.repl_output = output_buffer.getvalue()

                        # Always show that breakpoint was hit in quiet mode
                        import sys as real_sys

                        real_sys.__stderr__.write(
                            f"Breakpoint hit: {filename}:{lineno}\n"
                        )

                        # Warn if no output was captured
                        if not self.repl_output.strip():
                            real_sys.__stderr__.write(
                                "Warning: No output captured from REPL command\n"
                            )

                        real_sys.__stderr__.flush()
                    else:
                        # Normal mode - use regular print
                        try:
                            # Try to evaluate as expression first
                            result = eval(self.command, globals_dict, locals_dict)
                            if result is not None:
                                print(result)
                        except:
                            # If evaluation fails, try execution
                            try:
                                exec(self.command, globals_dict, locals_dict)
                            except Exception as e:
                                print(f"ERROR: {e}")

                    # Print end marker (unless in quiet mode)
                    if not self.quiet_mode:
                        print("=== END BREAKPOINT ===\n")

                    # Stop tracing and signal exit
                    self.trace_active = False
                    self.should_exit = True
                    sys.settrace(None)

                    # In standalone mode, don't exit - let the script continue
                    if self.standalone_mode:
                        return None

                    # Only raise exception if we're in a test context
                    # Otherwise, let pytest continue to collect/run tests
                    if self.in_test:
                        raise DebuggerExit()
                    else:
                        # If not in test, use os._exit to ensure immediate exit
                        import os

                        # Flush output first
                        sys.stdout.flush()
                        sys.stderr.flush()
                        os._exit(0)

            except DebuggerExit:
                # Re-raise our custom exit exception
                raise
            except Exception as e:
                print(f"TRACE ERROR: {e}", file=sys.stderr)
                sys.settrace(None)
                return None

        # For non-line events or after execution, decide whether to continue tracing
        # Return None for files we definitely don't care about to improve performance
        if event == "call":
            filename = frame.f_code.co_filename
            # Skip tracing for pytest internal files and standard library
            if any(
                skip in filename
                for skip in [
                    "pytest",
                    "pluggy",
                    "_pytest",
                    "importlib",
                    "site-packages",
                ]
            ):
                return None  # Don't trace this file

        return self.trace_function


def run_non_interactive_debug(
    file_path: str,
    line_no: int,
    command: str,
    pytest_args: list,
    quiet_mode: bool = False,
) -> int:
    """
    Run pytest with non-interactive debugging.

    Args:
        file_path: Path to the test file
        line_no: Line number to break at
        command: Command to execute at breakpoint
        pytest_args: Arguments to pass to pytest
        quiet_mode: If True, capture all output except REPL result

    Returns:
        Exit code from pytest
    """
    import contextlib
    import io

    import pytest

    # Create debugger
    debugger = NonInteractiveDebugger(file_path, line_no, command, quiet_mode)

    # Set up trace function
    sys.settrace(debugger.trace_function)

    try:
        if quiet_mode:
            # Capture pytest output
            captured_stdout = io.StringIO()
            captured_stderr = io.StringIO()

            try:
                with contextlib.redirect_stdout(
                    captured_stdout
                ), contextlib.redirect_stderr(captured_stderr):
                    # Run pytest
                    exit_code = pytest.main([file_path] + pytest_args)
            except DebuggerExit:
                # Expected exit after breakpoint
                exit_code = 0

            # If debugger was executed and has output, print it
            if debugger.executed and debugger.repl_output:
                sys.stdout.write(debugger.repl_output)
                sys.stdout.flush()

            # Check if there were any pytest errors
            stderr_content = captured_stderr.getvalue()
            if exit_code != 0 and "PASSED" not in captured_stdout.getvalue():
                # Only show actual test failures, not just the exit after breakpoint
                if "SystemExit" not in stderr_content and debugger.executed:
                    # Breakpoint was hit, this is expected behavior
                    pass
                else:
                    # Real error occurred
                    sys.stderr.write(stderr_content)
        else:
            # Run pytest normally
            try:
                exit_code = pytest.main([file_path] + pytest_args)
            except DebuggerExit:
                # Expected exit after breakpoint
                exit_code = 0

        # If debugger flagged for exit, exit now with clean exit
        if debugger.should_exit:
            sys.exit(0)

        return exit_code
    finally:
        # Ensure trace is removed
        sys.settrace(None)
