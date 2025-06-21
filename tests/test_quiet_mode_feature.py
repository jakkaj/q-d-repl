"""Tests for quiet mode functionality."""
import subprocess
import sys
import os
from pathlib import Path

# Get the smart_debugger directory
SMART_DEBUGGER_DIR = Path(__file__).parent.parent
SUBSTRATE_DIR = SMART_DEBUGGER_DIR.parent


def test_quiet_mode_shows_only_repl_output():
    """Test that quiet mode only shows REPL output and version banner."""
    # Create a simple test file
    test_file = SMART_DEBUGGER_DIR / "tests" / "test_quiet_mode.py"
    
    # Run with quiet mode
    cmd = [
        sys.executable, "-m", "smart_debugger.smart_debugger",
        "--quiet",
        str(test_file), "9", 'print("QUIET_OUTPUT: 42")',
        "--", "-s"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(SUBSTRATE_DIR),
        capture_output=True,
        text=True
    )
    
    # Check that we got the version banner on stderr
    assert "Smart Debugger v1.2.0" in result.stderr
    
    # Check that we got only the REPL output on stdout
    assert "QUIET_OUTPUT: 42" in result.stdout
    
    # Check that pytest output is suppressed
    assert "test session starts" not in result.stdout
    assert "PASSED" not in result.stdout
    assert "collecting" not in result.stdout


def test_quiet_mode_shows_repl_errors():
    """Test that quiet mode shows REPL errors."""
    test_file = SMART_DEBUGGER_DIR / "tests" / "test_quiet_mode.py"
    
    # Run with an undefined variable
    cmd = [
        sys.executable, "-m", "smart_debugger.smart_debugger",
        "--quiet",
        str(test_file), "9", 'print(undefined_variable)',
        "--", "-s"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(SUBSTRATE_DIR),
        capture_output=True,
        text=True
    )
    
    # Check that we got the error
    assert "ERROR:" in result.stdout
    assert "undefined_variable" in result.stdout


def test_normal_mode_shows_all_output():
    """Test that normal mode shows all pytest output."""
    test_file = SMART_DEBUGGER_DIR / "tests" / "test_quiet_mode.py"
    
    # Run without quiet mode
    cmd = [
        sys.executable, "-m", "smart_debugger.smart_debugger",
        str(test_file), "9", 'print("NORMAL_OUTPUT: 42")',
        "--", "-s"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(SUBSTRATE_DIR),
        capture_output=True,
        text=True
    )
    
    # Check that we got the version banner
    assert "Smart Debugger v1.2.0" in result.stderr
    
    # Check that we got pytest output
    assert "test session starts" in result.stdout
    assert "BREAKPOINT HIT" in result.stdout
    assert "NORMAL_OUTPUT: 42" in result.stdout
    assert "END BREAKPOINT" in result.stdout


def test_quiet_mode_with_test_failure():
    """Test that quiet mode shows real test failures."""
    # Create a failing test
    failing_test = SMART_DEBUGGER_DIR / "tests" / "test_failing.py"
    failing_test.write_text("""
def test_will_fail():
    x = 1
    y = 2
    assert x == y  # This will fail
    print("This line should not execute")  # Line 5
""")
    
    try:
        # Run with quiet mode on a line after the assertion
        cmd = [
            sys.executable, "-m", "smart_debugger.smart_debugger",
            "--quiet",
            str(failing_test), "6", 'print("Should not reach here")',
            "--", "-s"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(SUBSTRATE_DIR),
            capture_output=True,
            text=True
        )
        
        # The test should fail before reaching our breakpoint
        assert result.returncode != 0
        assert "Should not reach here" not in result.stdout
        
    finally:
        # Clean up
        if failing_test.exists():
            failing_test.unlink()


def test_quiet_mode_complex_output():
    """Test quiet mode with complex multiline output."""
    test_file = SMART_DEBUGGER_DIR / "tests" / "test_quiet_mode.py"
    
    # Run with multiline output
    cmd = [
        sys.executable, "-m", "smart_debugger.smart_debugger",
        "--quiet",
        str(test_file), "9", '''print("""Line 1
Line 2
Line 3""")''',
        "--", "-s"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(SUBSTRATE_DIR),
        capture_output=True,
        text=True
    )
    
    # Check that all lines are present
    assert "Line 1" in result.stdout
    assert "Line 2" in result.stdout
    assert "Line 3" in result.stdout
    
    # But no pytest output
    assert "test session starts" not in result.stdout


def test_version_banner_always_shows():
    """Test that version banner always appears on stderr."""
    test_file = SMART_DEBUGGER_DIR / "tests" / "test_quiet_mode.py"
    
    # Test both modes
    for quiet_flag in ["--quiet", ""]:
        cmd = [
            sys.executable, "-m", "smart_debugger.smart_debugger",
        ]
        if quiet_flag:
            cmd.append(quiet_flag)
        cmd.extend([
            str(test_file), "9", 'print("test")',
            "--", "-s"
        ])
        
        result = subprocess.run(
            cmd,
            cwd=str(SUBSTRATE_DIR),
            capture_output=True,
            text=True
        )
        
        # Version banner should always be on stderr
        assert "Smart Debugger v1.2.0" in result.stderr
        assert "Non-interactive debugging for LLM agents" in result.stderr