#!/usr/bin/env python3
"""
Tests for the -f/--file parameter functionality in pydebug and pydebug-stdin.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestFileParameter:
    """Test suite for file parameter functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_module.py"
        self.test_file.write_text(
            """
def test_function():
    x = 42
    y = "hello"
    config = {"key": "value", "number": 123}
    return x + len(y)
"""
        )

        # Add src to PYTHONPATH
        src_path = Path(__file__).parent.parent / "src"
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(src_path)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pydebug_with_file_parameter(self):
        """Test pydebug with -f parameter."""
        # Create command file
        cmd_file = Path(self.temp_dir) / "debug_cmd.py"
        cmd_file.write_text('print(f"x={x}, y={y}")')

        # Run pydebug with -f
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "smart_debugger",
                "--mode",
                "standalone",
                str(self.test_file),
                "4",
                'print("dummy")',
                "--",
                str(self.test_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        # First verify basic functionality works
        assert result.returncode == 0

        # Now test with file parameter via wrapper
        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "--mode",
                "standalone",
                "-f",
                str(cmd_file),
                str(self.test_file),
                "4",
                "--",
                str(self.test_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "x=42, y=hello" in result.stdout

    def test_pydebug_with_long_file_parameter(self):
        """Test pydebug with --file parameter."""
        # Create command file
        cmd_file = Path(self.temp_dir) / "debug_cmd.py"
        cmd_file.write_text('print(f"Config: {config}")')

        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "--mode",
                "standalone",
                "--file",
                str(cmd_file),
                str(self.test_file),
                "5",
                "--",
                str(self.test_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "Config: {'key': 'value', 'number': 123}" in result.stdout

    def test_pydebug_stdin_with_file_parameter(self):
        """Test pydebug-stdin with -f parameter overrides stdin."""
        # Create command file
        cmd_file = Path(self.temp_dir) / "debug_cmd.py"
        cmd_file.write_text('print("From file, not stdin")')

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"

        # Run with stdin input but -f should override it
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "--mode",
                "standalone",
                "-f",
                str(cmd_file),
                str(self.test_file),
                "3",
                "--",
                str(self.test_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
            input="print('This should be ignored')",
        )

        assert result.returncode == 0
        assert "From file, not stdin" in result.stdout
        assert "This should be ignored" not in result.stdout

    def test_exact_usage_pattern(self):
        """Test the exact usage pattern from requirements."""
        # Create directory structure
        scratch_dir = Path(self.temp_dir) / "scratch"
        scratch_dir.mkdir()
        debug_file = scratch_dir / "debug.py"
        debug_file.write_text('print(f"Config: {config}")')

        # Create a more realistic test file
        src_dir = Path(self.temp_dir) / "src" / "modules"
        src_dir.mkdir(parents=True)
        condense_file = src_dir / "condense.py"
        condense_file.write_text(
            '''
def process_data(data):
    """Process data with configuration."""
    config = {
        "version": "1.0",
        "debug": True,
        "max_items": 100
    }
    # Imagine line 150 is here
    result = []
    for item in data:
        if len(result) < config["max_items"]:
            result.append(item)
    return result
'''
        )

        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"

        # Run the exact command pattern (simplified for testing)
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "--quiet",
                "-f",
                str(debug_file),
                str(condense_file),
                "8",  # Line with config
                "--",
                str(condense_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "Config:" in result.stdout
        assert (
            '"version": "1.0"' in result.stdout or "'version': '1.0'" in result.stdout
        )

    def test_multiline_command_file(self):
        """Test complex multiline commands from file."""
        # Create multiline command file
        cmd_file = Path(self.temp_dir) / "complex_debug.py"
        cmd_file.write_text(
            """
import json
data = {"x": x, "y": y, "config": config}
print(json.dumps(data, indent=2))
print(f"Total: {x + len(y)}")
"""
        )

        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "--mode",
                "standalone",
                "--quiet",
                "-f",
                str(cmd_file),
                str(self.test_file),
                "5",
                "--",
                str(self.test_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert '"x": 42' in result.stdout
        assert '"y": "hello"' in result.stdout
        assert "Total: 47" in result.stdout

    def test_file_not_found_error(self):
        """Test error handling for non-existent command file."""
        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "-f",
                "/nonexistent/debug.py",
                str(self.test_file),
                "3",
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
                str(self.test_file),
                "3",
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

    def test_backward_compatibility_stdin(self):
        """Test that stdin piping still works without -f flag."""
        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"

        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "--mode",
                "standalone",
                str(self.test_file),
                "4",
                "--",
                str(self.test_file),
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

    def test_file_parameter_with_all_flags(self):
        """Test file parameter works with all flag combinations."""
        cmd_file = Path(self.temp_dir) / "test_flags.py"
        cmd_file.write_text('print("Testing all flags")')

        # Test with --mode, --quiet, and -f
        pydebug_stdin_path = Path(__file__).parent.parent / "src" / "pydebug-stdin"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_stdin_path),
                "--mode",
                "standalone",
                "--quiet",
                "-f",
                str(cmd_file),
                str(self.test_file),
                "3",
                "--",
                str(self.test_file),
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )

        assert result.returncode == 0
        assert "Testing all flags" in result.stdout
        # Quiet mode should suppress some output
        assert "Smart Debugger" in result.stderr  # Banner still shown

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
                    str(self.test_file),
                    "3",
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

    def test_pytest_mode_with_file_parameter(self):
        """Test file parameter works in pytest mode."""
        # Create a simple test file
        pytest_file = Path(self.temp_dir) / "test_sample.py"
        pytest_file.write_text(
            """
def test_example():
    data = {"test": "value"}
    assert data["test"] == "value"
"""
        )

        cmd_file = Path(self.temp_dir) / "pytest_debug.py"
        cmd_file.write_text('print(f"Data in test: {data}")')

        pydebug_path = Path(__file__).parent.parent / "src" / "pydebug.py"
        result = subprocess.run(
            [
                sys.executable,
                str(pydebug_path),
                "--quiet",
                "-f",
                str(cmd_file),
                str(pytest_file),
                "3",
                "--",
                "-xvs",
            ],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.temp_dir,
        )

        # Should work with pytest
        assert "Data in test: {'test': 'value'}" in result.stdout
