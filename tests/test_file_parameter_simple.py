#!/usr/bin/env python3
"""
Simplified tests for the -f/--file parameter functionality.
These tests focus on the core functionality that matters.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestFileParameterSimple:
    """Simplified test suite for file parameter functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

        # Add src to PYTHONPATH
        src_path = Path(__file__).parent.parent / "src"
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(src_path)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_parameter_basic_functionality(self):
        """Test basic file parameter functionality with real test file."""
        # Create command file
        cmd_file = Path(self.temp_dir) / "debug.py"
        cmd_file.write_text('print("File parameter works!")')

        # Use existing test file that we know works
        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "-f",
                str(cmd_file),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "File parameter works!" in result.stdout

    def test_file_parameter_long_form(self):
        """Test --file long form parameter."""
        cmd_file = Path(self.temp_dir) / "debug.py"
        cmd_file.write_text('print("Long form file parameter works!")')

        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "--file",
                str(cmd_file),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "Long form file parameter works!" in result.stdout

    def test_pydebug_stdin_file_parameter(self):
        """Test pydebug-stdin with file parameter."""
        cmd_file = Path(self.temp_dir) / "debug.py"
        cmd_file.write_text('print("pydebug-stdin file parameter works!")')

        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "-f",
                str(cmd_file),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "pydebug-stdin file parameter works!" in result.stdout

    def test_file_parameter_with_quiet_mode(self):
        """Test file parameter with quiet mode."""
        cmd_file = Path(self.temp_dir) / "debug.py"
        cmd_file.write_text('print("Quiet mode with file parameter!")')

        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "--quiet",
                "-f",
                str(cmd_file),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "Quiet mode with file parameter!" in result.stdout
        # In quiet mode, banner goes to stderr
        assert "Smart Debugger" in result.stderr

    def test_multiline_file_parameter(self):
        """Test file parameter with multiline commands."""
        cmd_file = Path(self.temp_dir) / "debug.py"
        cmd_file.write_text(
            """
print("=== Multiline Debug ===")
print("Line 1 of debug output")
print("Line 2 of debug output")
print("=== End Debug ===")
"""
        )

        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "--quiet",
                "-f",
                str(cmd_file),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "=== Multiline Debug ===" in result.stdout
        assert "Line 1 of debug output" in result.stdout
        assert "Line 2 of debug output" in result.stdout
        assert "=== End Debug ===" in result.stdout

    def test_file_not_found_error(self):
        """Test error handling for non-existent command file."""
        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "-f",
                "/nonexistent/debug.py",
                "test.py",
                "10",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 1
        assert "Error: Command file not found: /nonexistent/debug.py" in result.stderr

    def test_empty_command_file_error(self):
        """Test error handling for empty command file."""
        # Create empty file
        cmd_file = Path(self.temp_dir) / "empty.py"
        cmd_file.write_text("")

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "-f",
                str(cmd_file),
                "test.py",
                "10",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 1
        assert f"ERROR: Command file {cmd_file} is empty" in result.stderr

    def test_missing_file_path_after_flag(self):
        """Test error when -f flag is provided without file path."""
        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [sys.executable, str(pydebug_path), "-f"],  # Missing file path
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 1
        assert "Error: -f flag requires a file path" in result.stderr

    @pytest.mark.skipif(
        os.name == "nt", reason="Permission test may not work on Windows"
    )
    def test_permission_denied_error(self):
        """Test error handling for permission denied."""
        # Create file with no read permissions
        cmd_file = Path(self.temp_dir) / "no_read.py"
        cmd_file.write_text('print("test")')
        cmd_file.chmod(0o000)

        try:
            pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
            result = subprocess.run(
                [
                    sys.executable,
                    str(pydebug_path),
                    "-f",
                    str(cmd_file),
                    "test.py",
                    "10",
                ],
                capture_output=True,
                text=True,
                env=self.env,
            )

            assert result.returncode == 1
            assert "Error: Permission denied" in result.stderr
        finally:
            # Restore permissions for cleanup
            cmd_file.chmod(0o644)

    def test_backward_compatibility_stdin(self):
        """Test that stdin piping still works without -f flag."""
        test_file = (
            Path(__file__).parent
            / "sample_projects"
            / "simple_project"
            / "test_example.py"
        )

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                str(test_file),
                "11",
                "--",
                "-k",
                "test_basic_calculation",
                "-v",
            ],
            capture_output=True,
            text=True,
            env=self.env,
            input='print("Stdin still works!")',
        )

        assert result.returncode == 0
        assert "Stdin still works!" in result.stdout

    def test_backward_compatibility_direct_command(self):
        """Test that direct command still works without -f flag."""
        # Create a simple standalone script
        script_file = Path(self.temp_dir) / "script.py"
        script_file.write_text(
            """
x = 10
y = 20
z = x + y
print(f"Result: {z}")  # Line 5
"""
        )

        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "--mode",
                "standalone",
                str(script_file),
                "3",
                'print("Direct command works!")',
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "Direct command works!" in result.stdout
