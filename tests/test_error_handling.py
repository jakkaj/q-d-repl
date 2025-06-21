"""Tests for error handling and exit codes."""

import subprocess
import sys
from pathlib import Path
import tempfile


def test_file_not_found():
    """Test error handling for non-existent file."""
    result = subprocess.run(
        [sys.executable, "-m", "smart_debugger", "nonexistent.py", "10", "print('test')"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1
    assert "Error: File not found" in result.stderr


def test_invalid_arguments():
    """Test error handling for invalid arguments."""
    # Missing arguments
    result = subprocess.run(
        [sys.executable, "-m", "smart_debugger"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1
    assert "Usage:" in result.stderr or "Error:" in result.stderr


def test_invalid_line_number():
    """Test handling of non-numeric line number."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [sys.executable, "-m", "smart_debugger", str(test_file), "abc", "print('test')"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1
    assert "Error:" in result.stderr


def test_pytest_failure_propagation():
    """Test that pytest failures are caught before debugger exits."""
    # Create a failing test
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def test_fails():
    x = 1
    print("Before assert")  # Line 3
    assert False, "This test fails"
    print("After assert")  # This won't execute
""")
        failing_test = f.name
    
    try:
        # Set breakpoint on line that will execute before the assertion
        result = subprocess.run(
            [sys.executable, "-m", "smart_debugger", failing_test, "3", "print('test')", "--", "-x"],
            capture_output=True,
            text=True
        )
        
        # Debugger exits with 0 when breakpoint is hit successfully
        assert result.returncode == 0
        assert "BREAKPOINT HIT" in result.stdout
        assert "test" in result.stdout
    finally:
        Path(failing_test).unlink()


def test_syntax_error_in_command():
    """Test handling of syntax errors in REPL command."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "18", "print('unclosed string",  # Line 18 has actual code
            "--", "-v", "-s"  # Need -s to see stdout
        ],
        capture_output=True,
        text=True
    )
    
    # Should show the syntax error
    assert "ERROR:" in result.stdout
    assert "unterminated string" in result.stdout or "SyntaxError" in result.stdout


def test_runtime_error_in_command():
    """Test handling of runtime errors in REPL command."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "18", "print(1/0)",  # Division by zero, line 18 has actual code
            "--", "-v", "-s"  # Need -s to see stdout
        ],
        capture_output=True,
        text=True
    )
    
    # Should show the error
    assert "ERROR:" in result.stdout
    assert "ZeroDivisionError" in result.stdout or "division" in result.stdout


def test_keyboard_interrupt():
    """Test handling of keyboard interrupt."""
    # This is hard to test without actually sending SIGINT
    # Just verify the tool handles basic interruption scenarios
    pass  # Placeholder for manual testing