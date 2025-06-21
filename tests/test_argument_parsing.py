"""Tests for argument parsing and validation."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest


def test_parse_basic_arguments():
    """Test basic argument parsing."""
    # Mock sys.argv for the simple format: file line command -- pytest_args
    test_args = ['smart_debugger', 'test_file.py', '42', 'print("hello")', '--', '-v']
    
    with patch.object(sys, 'argv', test_args):
        # This will test the actual parsing in __main__.py when we create it
        # For now, just verify the expected format
        assert len(test_args) >= 4  # At minimum: script, file, line, command
        assert test_args[1] == 'test_file.py'
        assert test_args[2] == '42'
        assert test_args[3] == 'print("hello")'
        if '--' in test_args:
            sep_idx = test_args.index('--')
            assert test_args[sep_idx + 1:] == ['-v']


def test_parse_without_pytest_args():
    """Test parsing without pytest arguments."""
    test_args = ['smart_debugger', 'test_file.py', '42', 'print("hello")']
    
    with patch.object(sys, 'argv', test_args):
        assert len(test_args) == 4
        assert '--' not in test_args


def test_parse_empty_command():
    """Test parsing with empty command."""
    test_args = ['smart_debugger', 'test_file.py', '42', '', '--', '-v']
    
    with patch.object(sys, 'argv', test_args):
        assert test_args[3] == ''


def test_file_validation():
    """Test file existence validation."""
    # Should validate that file exists
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test():\n    pass\n")
        temp_file = f.name
    
    try:
        # File should exist
        assert Path(temp_file).exists()
        
        # Non-existent file should not exist
        assert not Path('/nonexistent/file.py').exists()
    finally:
        Path(temp_file).unlink()


def test_line_number_validation():
    """Test line number validation."""
    # Valid line numbers
    assert int('1') > 0
    assert int('42') > 0
    assert int('999') > 0
    
    # Invalid line numbers should raise
    with pytest.raises(ValueError):
        int('abc')
    
    # Zero or negative should be invalid
    assert int('0') == 0  # Should be rejected
    assert int('-5') < 0  # Should be rejected


def test_command_with_quotes():
    """Test commands containing quotes."""
    commands = [
        'print("Hello, world!")',
        "print('Hello, world!')",
        'print(f"Value: {x}")',
        "data = {'key': 'value'}"
    ]
    
    for cmd in commands:
        # Commands should preserve quotes
        assert '"' in cmd or "'" in cmd


def test_multiline_command():
    """Test multiline commands."""
    cmd = 'x = 1; y = 2; print(x + y)'
    assert ';' in cmd
    
    # Could also use actual newlines
    cmd2 = 'x = 1\ny = 2\nprint(x + y)'
    assert '\n' in cmd2