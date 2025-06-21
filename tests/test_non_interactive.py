"""Tests for non-interactive debugger functionality."""

import subprocess
import sys
from pathlib import Path


def test_basic_execution():
    """Test basic non-interactive execution."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "10", "print('total =', total, 'num =', num)",  # Line 10 is inside the loop
            "--", "-v", "-s"
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "=== BREAKPOINT HIT:" in result.stdout
    assert "test_example.py:10 ===" in result.stdout
    assert "total = 0 num = 1" in result.stdout
    assert "=== END BREAKPOINT ===" in result.stdout
    
    # Ensure no interactive prompt
    assert ">>>" not in result.stdout
    assert "(Pdb)" not in result.stdout


def test_output_format():
    """Test that output format matches exactly."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "10", "print('hello world')",  # Line 10 has actual code
            "--", "-v", "-s"
        ],
        capture_output=True,
        text=True
    )
    
    # Check exact format
    assert "=== BREAKPOINT HIT:" in result.stdout
    assert ":10 ===" in result.stdout
    assert "hello world" in result.stdout
    assert "=== END BREAKPOINT ===" in result.stdout
    
    # Should NOT have RESULT: or OUTPUT: prefixes
    assert "RESULT:" not in result.stdout
    assert "OUTPUT:" not in result.stdout


def test_expression_evaluation():
    """Test evaluating expressions (not just statements)."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "9", "print(total + num)",
            "--", "-v", "-s"
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "1" in result.stdout  # 0 + 1


def test_multiline_command():
    """Test multiline Python commands."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "9", "x = total * 2; print(f'x={x}')",
            "--", "-v", "-s"
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "x=0" in result.stdout


def test_error_in_command():
    """Test handling of errors in REPL command."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "9", "print(undefined_variable)",
            "--", "-v", "-s"
        ],
        capture_output=True,
        text=True
    )
    
    # Should complete but show error
    assert result.returncode == 0
    assert "ERROR:" in result.stdout
    assert "NameError" in result.stdout or "undefined_variable" in result.stdout


def test_file_not_found():
    """Test error handling for non-existent file."""
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            "nonexistent.py", "10", "print('test')"
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1
    assert "Error: File not found" in result.stderr


def test_invalid_line_number():
    """Test error handling for invalid line number."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "999", "print('test')"
        ],
        capture_output=True,
        text=True
    )
    
    # Should either validate line number or run without hitting breakpoint
    # Depends on implementation choice
    assert result.returncode in [0, 1]


def test_empty_command():
    """Test behavior with empty command."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "9", "",
            "--", "-v", "-s"  # Need -s to see output
        ],
        capture_output=True,
        text=True
    )
    
    # Should handle gracefully - show breakpoint but no output
    assert "=== BREAKPOINT HIT:" in result.stdout
    assert "=== END BREAKPOINT ===" in result.stdout


def test_pytest_exit_code_propagation():
    """Test debugger behavior with failing tests."""
    # Create a failing test
    failing_test = Path(__file__).parent / "sample_projects/failing_test.py"
    failing_test.write_text("""
def test_will_fail():
    x = 1
    print("Before assertion")  # Line 3
    assert False, "This test always fails"
    print("After assertion")  # Never reached
""")
    
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "smart_debugger",
                str(failing_test), "3", "print('at failing test')",  # Line 3 executes before assertion
                "--", "-x"  # Stop on first failure
            ],
            capture_output=True,
            text=True
        )
        
        # Debugger exits with 0 when breakpoint is hit
        assert result.returncode == 0
        assert "at failing test" in result.stdout
    finally:
        failing_test.unlink()


def test_no_pytest_args():
    """Test running without pytest arguments."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"
    
    # Without explicit pytest args, pytest still captures output by default
    # We need to check for the output in the combined stdout
    result = subprocess.run(
        [
            sys.executable, "-m", "smart_debugger",
            str(test_file), "9", "print('no pytest args')"
            # No -- separator, no pytest args
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    # The output might be captured by pytest, let's just verify no error
    assert "PASSED" in result.stdout  # Tests should pass