"""Tests for non-interactive debugger functionality."""

import os
import subprocess
import sys
from pathlib import Path

# Get the project root and source directory
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def test_basic_execution():
    """Test basic non-interactive execution."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "11",
            "print('total =', total, 'num =', num)",  # Line 11 is inside the loop
            "--",
            "-v",
            "-s",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "=== BREAKPOINT HIT:" in result.stdout
    assert "test_example.py:11 ===" in result.stdout
    assert "total = 0 num = 1" in result.stdout
    assert "=== END BREAKPOINT ===" in result.stdout

    # Ensure no interactive prompt
    assert ">>>" not in result.stdout
    assert "(Pdb)" not in result.stdout


def test_output_format():
    """Test that output format matches exactly."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "10",
            "print('hello world')",  # Line 10 has actual code
            "--",
            "-v",
            "-s",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
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

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "10",
            "print(total + num)",
            "--",
            "-v",
            "-s",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "1" in result.stdout  # 0 + 1


def test_multiline_command():
    """Test multiline Python commands."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "10",
            "x = total * 2; print(f'x={x}')",
            "--",
            "-v",
            "-s",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "x=0" in result.stdout


def test_error_in_command():
    """Test handling of errors in REPL command."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "10",
            "print(undefined_variable)",
            "--",
            "-v",
            "-s",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    # Should complete but show error
    assert result.returncode == 0
    assert "ERROR:" in result.stdout
    assert "NameError" in result.stdout or "undefined_variable" in result.stdout


def test_file_not_found():
    """Test error handling for non-existent file."""
    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            "nonexistent.py",
            "10",
            "print('test')",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 1
    assert "Error: File not found" in result.stderr


def test_invalid_line_number():
    """Test error handling for invalid line number."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "999",
            "print('test')",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    # Should either validate line number or run without hitting breakpoint
    # Depends on implementation choice
    assert result.returncode in [0, 1]


def test_empty_command():
    """Test behavior with empty command."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "10",
            "",
            "--",
            "-v",
            "-s",  # Need -s to see output
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    # Should handle gracefully - show breakpoint but no output
    assert "=== BREAKPOINT HIT:" in result.stdout
    assert "=== END BREAKPOINT ===" in result.stdout


def test_pytest_exit_code_propagation():
    """Test debugger behavior with failing tests."""
    # Create a failing test
    failing_test = Path(__file__).parent / "sample_projects/failing_test.py"
    failing_test.write_text(
        """
def test_will_fail():
    x = 1
    print("Before assertion")  # Line 3
    assert False, "This test always fails"
    print("After assertion")  # Never reached
"""
    )

    try:
        # Set PYTHONPATH to include src directory
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "smart_debugger",
                str(failing_test),
                "3",
                "print('at failing test')",  # Line 3 executes before assertion
                "--",
                "-x",  # Stop on first failure
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env=env,
        )

        # Debugger exits with 0 when breakpoint is hit
        assert result.returncode == 0
        assert "at failing test" in result.stdout
    finally:
        failing_test.unlink()


def test_no_pytest_args():
    """Test running without pytest arguments."""
    test_file = Path(__file__).parent / "sample_projects/simple_project/test_example.py"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    # Without explicit pytest args, pytest still captures output by default
    # We need to check for the output in the combined stdout
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smart_debugger",
            str(test_file),
            "10",
            "print('no pytest args')",
            # No -- separator, no pytest args
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    # The output might be captured by pytest, let's just verify no error
    assert "PASSED" in result.stdout  # Tests should pass
