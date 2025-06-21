#!/usr/bin/env python3
"""
Integration tests for the -f/--file parameter functionality.
These tests use real files to ensure the feature works correctly.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_file_parameter_with_real_test():
    """Test file parameter with a real pytest test file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create debug command file
        debug_file = Path(temp_dir) / "debug.py"
        debug_file.write_text('print("Debug output from file parameter!")')

        # Use an existing test file from our test suite
        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        # Run with file parameter
        result = subprocess.run(
            [
                str(Path(__file__).parent.parent / "src" / "pydebug-stdin"),
                "--quiet",
                "-f",
                str(debug_file),
                str(test_file),
                "11",  # Line in the loop
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Debug output from file parameter!" in result.stdout


def test_file_parameter_overrides_stdin():
    """Test that file parameter takes precedence over stdin."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create debug command file
        debug_file = Path(temp_dir) / "debug.py"
        debug_file.write_text('print("From file, not stdin")')

        # Use an existing test file
        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        # Run with both file parameter and stdin
        result = subprocess.run(
            [
                str(Path(__file__).parent.parent / "src" / "pydebug-stdin"),
                "--quiet",
                "-f",
                str(debug_file),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            input='print("This should be ignored")',
        )

        assert result.returncode == 0
        assert "From file, not stdin" in result.stdout
        assert "This should be ignored" not in result.stdout


def test_file_parameter_multiline():
    """Test file parameter with multiline debug commands."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiline debug command file
        debug_file = Path(temp_dir) / "debug_multi.py"
        debug_file.write_text(
            """
print("=== Debug Info ===")
print(f"total = {total}")
print(f"num = {num}")
print("=== End Debug ===")
"""
        )

        # Use an existing test file
        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        # Run with file parameter
        result = subprocess.run(
            [
                str(Path(__file__).parent.parent / "src" / "pydebug-stdin"),
                "--quiet",
                "-f",
                str(debug_file),
                str(test_file),
                "11",  # Line in the loop
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "=== Debug Info ===" in result.stdout
        assert "total = " in result.stdout
        assert "num = " in result.stdout


def test_production_debugging_pattern():
    """Test the production debugging pattern - debugging source by running tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create debug command file
        debug_file = Path(temp_dir) / "debug_prod.py"
        debug_file.write_text(
            'print(f"Debugging production code: total = {total}, num = {num}")'
        )

        # Debug the actual source file by running a test
        source_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        # Run test that exercises the code
        result = subprocess.run(
            [
                str(Path(__file__).parent.parent / "src" / "pydebug-stdin"),
                "--quiet",
                "-f",
                str(debug_file),
                str(source_file),
                "11",  # Line with loop variables
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Debugging production code:" in result.stdout
        assert "total =" in result.stdout
        assert "num =" in result.stdout


def test_file_not_found_error():
    """Test error handling for non-existent command file."""
    result = subprocess.run(
        [
            str(Path(__file__).parent.parent / "src" / "pydebug.py"),
            "-f",
            "/nonexistent/debug.py",
            "test.py",
            "10",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Error: Command file not found: /nonexistent/debug.py" in result.stderr


def test_empty_file_error():
    """Test error handling for empty command file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create empty file
        empty_file = Path(temp_dir) / "empty.py"
        empty_file.write_text("")

        result = subprocess.run(
            [
                str(Path(__file__).parent.parent / "src" / "pydebug-stdin"),
                "-f",
                str(empty_file),
                "test.py",
                "10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert f"ERROR: Command file {empty_file} is empty" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
