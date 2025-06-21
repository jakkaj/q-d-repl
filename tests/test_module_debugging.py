"""Tests for module debugging with -m flag."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Get the project root and source directory
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def test_module_debugging():
    """Test debugging a module with -m flag."""
    # Create a temporary module
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a package structure
        pkg_dir = Path(tmpdir) / "test_package"
        pkg_dir.mkdir()

        # Create __init__.py
        (pkg_dir / "__init__.py").write_text("")

        # Create __main__.py with some code
        (pkg_dir / "__main__.py").write_text(
            """import sys

def main():
    data = {"name": "test", "value": 42}  # Line 4
    print(f"Module started with args: {sys.argv[1:]}")
    result = data["value"] * 2
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    main()
"""
        )

        # Run with module mode
        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            "-m",
            "test_package",
            "5",
            'print(f"data={data}")',
        ]

        # Set PYTHONPATH to include both src directory and the temp directory
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{SRC_DIR}:{tmpdir}"

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        # Check output
        assert result.returncode == 0
        assert "data={'name': 'test', 'value': 42}" in result.stdout
        assert "Module started with args: []" in result.stdout
        assert "Result: 84" in result.stdout


def test_module_with_arguments():
    """Test module debugging with command line arguments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple module
        module_file = Path(tmpdir) / "argmod.py"
        module_file.write_text(
            """import sys

if __name__ == "__main__":
    args = sys.argv[1:]
    print(f"Got arguments: {args}")  # Line 5
    total = sum(int(arg) for arg in args if arg.isdigit())
    print(f"Sum of numeric args: {total}")
"""
        )

        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            "-m",
            "argmod",
            "5",
            'print(f"sys.argv={sys.argv}")',
            "--",
            "10",
            "20",
            "hello",
            "30",
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{SRC_DIR}:{tmpdir}"

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        assert "['10', '20', 'hello', '30']" in result.stdout
        assert "Sum of numeric args: 60" in result.stdout


def test_builtin_module():
    """Test debugging a built-in module."""
    # Try to debug json.tool module
    cmd = [
        sys.executable,
        "-m",
        "smart_debugger",
        "--mode",
        "standalone",
        "-m",
        "json.tool",
        "38",
        'print("At json.tool main")',  # Line might vary
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    # Create a test JSON file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"test": "data"}')
        json_file = f.name

    try:
        # Run with the JSON file as input
        with open(json_file, "r") as f:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                env=env,
                stdin=f,
            )

        # Should work even if breakpoint isn't hit
        assert result.returncode == 0
        # The JSON output should still appear
        assert '"test"' in result.stdout or "Breakpoint at line" in result.stderr

    finally:
        Path(json_file).unlink()


def test_module_not_found():
    """Test error handling for non-existent module."""
    cmd = [
        sys.executable,
        "-m",
        "smart_debugger",
        "--mode",
        "standalone",
        "-m",
        "nonexistent_module_xyz",
        "10",
        'print("test")',
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    result = subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
    )

    assert result.returncode != 0
    assert "Module not found: nonexistent_module_xyz" in result.stderr


def test_module_quiet_mode():
    """Test module debugging with quiet mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple module
        module_file = Path(tmpdir) / "quiet_test.py"
        module_file.write_text(
            """data = [1, 2, 3, 4, 5]
total = sum(data)
print(f"Total: {total}")  # Line 3
print("Done")
"""
        )

        cmd = [
            sys.executable,
            "-m",
            "smart_debugger",
            "--mode",
            "standalone",
            "-m",
            "--quiet",
            "quiet_test",
            "3",
            'print(f"data={data}, total={total}")',
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{SRC_DIR}:{tmpdir}"

        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env
        )

        assert result.returncode == 0
        # In quiet mode, only REPL output on stdout
        assert "data=[1, 2, 3, 4, 5], total=15" in result.stdout
        # Script output should still appear
        assert "Total: 15" in result.stdout
        assert "Done" in result.stdout
        # But no framework messages
        assert "BREAKPOINT HIT" not in result.stdout
