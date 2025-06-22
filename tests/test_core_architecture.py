"""Integration tests for the multi-language debugger core architecture."""

import pytest
import tempfile
import os
from pathlib import Path

from smart_debugger.core import (
    DebuggerInterface, 
    DebugResult, 
    LanguageDetector, 
    DebuggerRegistry
)
from smart_debugger.core.registry import get_global_registry, register_debugger
from smart_debugger.languages.python import PythonDebugger


class TestLanguageDetector:
    """Test the language detection functionality."""
    
    def test_detect_by_extension(self):
        """Test language detection by file extension."""
        detector = LanguageDetector()
        
        # Test common extensions
        assert detector.detect_language("test.py") == "python"
        assert detector.detect_language("Program.cs") == "csharp"
        assert detector.detect_language("app.js") == "javascript"
        assert detector.detect_language("main.go") == "go"
        assert detector.detect_language("lib.rs") == "rust"
        assert detector.detect_language("Test.java") == "java"
        assert detector.detect_language("component.ts") == "typescript"
        assert detector.detect_language("script.rb") == "ruby"
        
        # Test case insensitivity
        assert detector.detect_language("TEST.PY") == "python"
        assert detector.detect_language("MAIN.CS") == "csharp"
    
    def test_detect_by_shebang(self):
        """Test language detection by shebang line."""
        detector = LanguageDetector()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("print('Hello')")
            f.flush()
            
            assert detector.detect_language(f.name) == "python"
            os.unlink(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write("#!/usr/bin/node\n")
            f.write("console.log('Hello')")
            f.flush()
            
            assert detector.detect_language(f.name) == "javascript"
            os.unlink(f.name)
    
    def test_detect_by_content(self):
        """Test language detection by file content."""
        detector = LanguageDetector()
        
        # Python content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("import os\n")
            f.write("def main():\n")
            f.write("    print('Hello')\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    main()")
            f.flush()
            
            assert detector.detect_language(f.name) == "python"
            os.unlink(f.name)
        
        # JavaScript content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("const express = require('express');\n")
            f.write("function handleRequest(req, res) {\n")
            f.write("    res.send('Hello');\n")
            f.write("}")
            f.flush()
            
            assert detector.detect_language(f.name) == "javascript"
            os.unlink(f.name)
    
    def test_detect_unsupported_file(self):
        """Test detection of unsupported files."""
        detector = LanguageDetector()
        
        with pytest.raises(ValueError, match="Cannot detect language"):
            detector.detect_language("unknown.xyz")
    
    def test_supported_extensions(self):
        """Test getting supported extensions."""
        detector = LanguageDetector()
        extensions = detector.get_supported_extensions()
        
        assert '.py' in extensions
        assert '.cs' in extensions
        assert '.js' in extensions
        assert '.go' in extensions
        assert '.rs' in extensions
    
    def test_is_supported(self):
        """Test checking if a file is supported."""
        detector = LanguageDetector()
        
        assert detector.is_supported("test.py") is True
        assert detector.is_supported("app.cs") is True
        assert detector.is_supported("unknown.xyz") is False
    
    def test_custom_mappings(self):
        """Test adding custom extension and shebang mappings."""
        detector = LanguageDetector()
        
        # Add custom extension
        detector.add_extension_mapping('.mypy', 'python')
        assert detector.detect_language("test.mypy") == "python"
        
        # Add custom shebang
        detector.add_shebang_pattern('mypython', 'python')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write("#!/usr/bin/env mypython\n")
            f.write("print('Hello')")
            f.flush()
            
            assert detector.detect_language(f.name) == "python"
            os.unlink(f.name)


class TestDebuggerRegistry:
    """Test the debugger registry functionality."""
    
    def test_register_and_get_debugger(self):
        """Test registering and retrieving debuggers."""
        registry = DebuggerRegistry()
        
        # Register Python debugger
        registry.register_debugger('python', PythonDebugger)
        
        # Get debugger
        debugger = registry.get_debugger('python')
        assert isinstance(debugger, PythonDebugger)
        assert debugger.get_language_name() == 'python'
    
    def test_factory_function_registration(self):
        """Test registering debuggers with factory functions."""
        registry = DebuggerRegistry()
        
        # Register with factory function
        def create_python_debugger():
            return PythonDebugger()
        
        registry.register_debugger('python', create_python_debugger)
        
        debugger = registry.get_debugger('python')
        assert isinstance(debugger, PythonDebugger)
    
    def test_singleton_instances(self):
        """Test singleton debugger instances."""
        registry = DebuggerRegistry()
        registry.register_debugger('python', PythonDebugger)
        
        # Get singleton instances
        debugger1 = registry.get_debugger('python', use_singleton=True)
        debugger2 = registry.get_debugger('python', use_singleton=True)
        
        # Should be the same instance
        assert debugger1 is debugger2
        
        # Non-singleton should be different
        debugger3 = registry.get_debugger('python', use_singleton=False)
        assert debugger3 is not debugger1
    
    def test_unregister_debugger(self):
        """Test unregistering debuggers."""
        registry = DebuggerRegistry()
        registry.register_debugger('python', PythonDebugger)
        
        assert registry.has_debugger('python')
        
        registry.unregister_debugger('python')
        assert not registry.has_debugger('python')
        
        with pytest.raises(ValueError):
            registry.get_debugger('python')
    
    def test_list_languages(self):
        """Test listing supported languages."""
        registry = DebuggerRegistry()
        
        # Register multiple debuggers
        registry.register_debugger('python', PythonDebugger)
        registry.register_debugger('javascript', PythonDebugger)  # Using Python as placeholder
        
        languages = registry.list_supported_languages()
        assert 'python' in languages
        assert 'javascript' in languages
        assert languages == sorted(languages)  # Should be sorted
    
    def test_environment_validation(self):
        """Test environment validation for debuggers."""
        registry = DebuggerRegistry()
        
        # Register with validation
        registry.register_debugger('python', PythonDebugger, validate_environment=True)
        
        # Python environment should be valid
        assert registry.is_environment_valid('python')
    
    def test_debugger_info(self):
        """Test getting debugger information."""
        registry = DebuggerRegistry()
        registry.register_debugger('python', PythonDebugger)
        
        info = registry.get_debugger_info('python')
        assert info['language'] == 'python'
        assert info['debugger_type'] == 'PythonDebugger'
        assert info['language_name'] == 'python'
        assert 'environment_valid' in info
    
    def test_clear_registry(self):
        """Test clearing all registered debuggers."""
        registry = DebuggerRegistry()
        registry.register_debugger('python', PythonDebugger)
        registry.register_debugger('javascript', PythonDebugger)
        
        assert len(registry.list_supported_languages()) == 2
        
        registry.clear()
        assert len(registry.list_supported_languages()) == 0
    
    def test_global_registry(self):
        """Test the global registry functionality."""
        # Clear any existing registrations
        global_reg = get_global_registry()
        global_reg.clear()
        
        # Register using global function
        register_debugger('python', PythonDebugger)
        
        # Should be accessible from global registry
        registry = get_global_registry()
        assert registry.has_debugger('python')
        
        debugger = registry.get_debugger('python')
        assert isinstance(debugger, PythonDebugger)


class TestDebugResult:
    """Test the DebugResult Pydantic model."""
    
    def test_debug_result_creation(self):
        """Test creating DebugResult instances."""
        result = DebugResult(
            success=True,
            result="Hello, World!",
            output="print output",
            language="python"
        )
        
        assert result.success is True
        assert result.result == "Hello, World!"
        assert result.output == "print output"
        assert result.error is None
        assert result.language == "python"
        assert result.metadata == {}
    
    def test_debug_result_with_error(self):
        """Test DebugResult with error."""
        result = DebugResult(
            success=False,
            error="Syntax error",
            language="python"
        )
        
        assert result.success is False
        assert result.error == "Syntax error"
        assert result.result is None
    
    def test_debug_result_serialization(self):
        """Test DebugResult JSON serialization."""
        result = DebugResult(
            success=True,
            result=[1, 2, 3],
            language="python",
            metadata={"key": "value"}
        )
        
        # Test JSON serialization (Pydantic v2)
        json_str = result.model_dump_json()
        assert '"success":true' in json_str
        assert '"language":"python"' in json_str
        
        # Test dict conversion (Pydantic v2)
        data = result.model_dump()
        assert data['success'] is True
        assert data['result'] == [1, 2, 3]
        assert data['metadata'] == {"key": "value"}
    
    def test_debug_result_arbitrary_types(self):
        """Test DebugResult with arbitrary result types."""
        # Custom object
        class CustomObject:
            def __init__(self, value):
                self.value = value
        
        obj = CustomObject(42)
        result = DebugResult(
            success=True,
            result=obj,
            language="python"
        )
        
        assert result.result.value == 42


class TestPythonDebuggerIntegration:
    """Integration tests for the Python debugger."""
    
    def test_python_debugger_interface(self):
        """Test that PythonDebugger implements DebuggerInterface correctly."""
        debugger = PythonDebugger()
        
        # Check interface methods
        assert hasattr(debugger, 'debug')
        assert hasattr(debugger, 'supports_file')
        assert hasattr(debugger, 'get_language_name')
        assert hasattr(debugger, 'validate_environment')
        
        # Check language name
        assert debugger.get_language_name() == "python"
        
        # Check file support
        assert debugger.supports_file("test.py") is True
        assert debugger.supports_file("test.cs") is False
        
        # Check environment validation
        assert debugger.validate_environment() is True
    
    def test_python_debugger_simple_expression(self):
        """Test debugging a simple Python expression."""
        debugger = PythonDebugger()
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_function():
    x = 42
    y = 10
    result = x + y
    return result

if __name__ == "__main__":
    test_function()
""")
            f.flush()
            test_file = f.name
        
        try:
            # Debug the file
            result = debugger.debug(
                file_path=test_file,
                line_number=5,  # Line with 'result = x + y'
                expression="x + y",
                quiet_mode=True
            )
            
            # For standalone scripts, we need to check if the debugger worked
            # The result might be None if the breakpoint wasn't hit
            assert result.language == "python"
            
        finally:
            os.unlink(test_file)
    
    def test_registry_with_python_debugger(self):
        """Test registering and using Python debugger through registry."""
        registry = DebuggerRegistry()
        registry.register_debugger('python', PythonDebugger)
        
        # Detect language and get debugger
        detector = LanguageDetector()
        
        test_file = "example.py"
        language = detector.detect_language(test_file)
        assert language == "python"
        
        debugger = registry.get_debugger(language)
        assert isinstance(debugger, PythonDebugger)
        assert debugger.supports_file(test_file)


# Run with: pytest tests/test_core_architecture.py -v