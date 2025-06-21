"""Tests for standalone Python file debugging mode."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Get the project root and source directory
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def test_standalone_basic_script():
    """Test debugging a simple standalone script."""
    # Create a test script
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
x = 10
y = 20
z = x + y
print(f"Result: {z}")  # Line 5 - breakpoint here
"""
        )
        script_path = f.name

    try:
        # Run with standalone mode
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            script_path,
            "5",
            'print(f"x={x}, y={y}, z={z}")',
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        # Check output
        assert result.returncode == 0
        assert "x=10, y=20, z=30" in result.stdout
        assert "Result: 30" in result.stdout

    finally:
        Path(script_path).unlink()


def test_standalone_with_arguments():
    """Test standalone script with command line arguments."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
import sys
print(f"Script: {sys.argv[0]}")
print(f"Args: {sys.argv[1:]}")  # Line 4
total = sum(int(arg) for arg in sys.argv[1:])
print(f"Sum: {total}")
"""
        )
        script_path = f.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            script_path,
            "4",
            'print(f"argv={sys.argv}")',
            "--",
            "10",
            "20",
            "30",
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        assert "['10', '20', '30']" in result.stdout
        assert "Sum: 60" in result.stdout

    finally:
        Path(script_path).unlink()


def test_standalone_quiet_mode():
    """Test standalone mode with quiet flag."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
data = {"key": "value", "count": 42}
result = data["count"] * 2  # Line 3
print(f"Final: {result}")
"""
        )
        script_path = f.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            "--quiet",
            script_path,
            "3",
            "print(data)",
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        assert "{'key': 'value', 'count': 42}" in result.stdout
        # In quiet mode, script output should still appear
        assert "Final: 84" in result.stdout
        # But no framework messages
        assert "BREAKPOINT HIT" not in result.stdout

    finally:
        Path(script_path).unlink()


def test_standalone_with_imports():
    """Test standalone script that imports modules."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
import json
import os

data = {"user": "test", "id": 123}
json_str = json.dumps(data)  # Line 6
print(f"JSON: {json_str}")
print(f"CWD: {os.getcwd()}")
"""
        )
        script_path = f.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            script_path,
            "6",
            'print(f"json module: {json.__name__}")',
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        assert "json module: json" in result.stdout
        assert 'JSON: {"user": "test", "id": 123}' in result.stdout

    finally:
        Path(script_path).unlink()


def test_standalone_script_with_error():
    """Test standalone script that has an error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
x = 10
y = 0
result = x / y  # Line 4 - will raise ZeroDivisionError
print("Should not reach here")
"""
        )
        script_path = f.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            script_path,
            "4",
            'print(f"About to divide by {y}")',
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        # Script should fail with error
        assert result.returncode != 0
        assert "About to divide by 0" in result.stdout
        assert "ZeroDivisionError" in result.stderr

    finally:
        Path(script_path).unlink()


def test_standalone_breakpoint_not_reached():
    """Test when breakpoint line is never reached."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
if False:
    x = 10  # Line 3 - never reached
print("Script completed")
"""
        )
        script_path = f.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            script_path,
            "3",
            'print("This should not execute")',
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        assert "This should not execute" not in result.stdout
        assert "Script completed" in result.stdout
        assert "Breakpoint at line 3 was never reached" in result.stderr

    finally:
        Path(script_path).unlink()


def test_standalone_with_main_guard():
    """Test script with if __name__ == '__main__' guard."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def main():
    x = 42
    print(f"Value: {x}")  # Line 4
    return x

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")
"""
        )
        script_path = f.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            script_path,
            "4",
            'print(f"__name__={__name__}")',
        ]

        # Set PYTHONPATH to include smart_debugger
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        assert "__name__=__main__" in result.stdout
        assert "Value: 42" in result.stdout
        assert "Result: 42" in result.stdout

    finally:
        Path(script_path).unlink()
