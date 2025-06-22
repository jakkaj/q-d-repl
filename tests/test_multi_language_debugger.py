"""Unit tests for the multi-language debugger implementation."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from smart_debugger.multi_language import (
    setup_multi_language_debugger,
    debug_file,
    list_supported_languages,
    list_available_languages,
    get_language_info
)
from smart_debugger.core import DebuggerRegistry, LanguageDetector, DebugResult
from smart_debugger.languages.python import PythonDebugger
from smart_debugger.languages.dap import DAPDebugger
from smart_debugger.languages.adapters.configs import AdapterConfig, get_adapter_config


class TestMultiLanguageSetup:
    """Test the multi-language debugger setup functionality."""
    
    def test_setup_multi_language_debugger(self):
        """Test setting up the multi-language debugger."""
        registry = setup_multi_language_debugger()
        
        # Should have at least Python registered
        assert registry.has_debugger('python')
        
        # Should return a DebuggerRegistry instance
        assert isinstance(registry, DebuggerRegistry)
        
        # Should have multiple languages
        languages = registry.list_supported_languages()
        assert len(languages) >= 1
        assert 'python' in languages
    
    def test_list_supported_languages(self):
        """Test listing all supported languages."""
        languages = list_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) >= 1
        assert 'python' in languages
    
    def test_list_available_languages(self):
        """Test listing languages with valid environments."""
        available = list_available_languages()
        
        assert isinstance(available, list)
        # Python should always be available since we're running in Python
        assert 'python' in available
    
    def test_get_language_info_python(self):
        """Test getting information about Python debugger."""
        info = get_language_info('python')
        
        assert info['language'] == 'python'
        assert info['debugger_type'] == 'PythonDebugger'
        assert info['language_name'] == 'python'
        assert 'environment_valid' in info
    
    def test_get_language_info_unsupported(self):
        """Test getting info for unsupported language."""
        info = get_language_info('nonexistent')
        
        assert not info['supported']
        assert 'error' in info


class TestDAPDebugger:
    """Test the DAP debugger implementation."""
    
    def test_dap_debugger_creation(self):
        """Test creating a DAP debugger for supported language."""
        # Mock an adapter config to avoid dependency on actual tools
        mock_config = AdapterConfig(
            language='mock',
            command=['echo', 'test'],
            transport='stdio',
            launch_type='test',
            file_extensions=['.mock']
        )
        
        with patch('smart_debugger.languages.dap.debugger.get_adapter_config', return_value=mock_config):
            debugger = DAPDebugger('mock')
            
            assert debugger.get_language_name() == 'mock'
            assert debugger.language == 'mock'
            assert debugger.adapter_config == mock_config
    
    def test_dap_debugger_unsupported_language(self):
        """Test creating DAP debugger for unsupported language."""
        with patch('smart_debugger.languages.dap.debugger.get_adapter_config', return_value=None):
            with pytest.raises(ValueError, match="No adapter configuration found"):
                DAPDebugger('unsupported')
    
    def test_dap_debugger_supports_file(self):
        """Test file support checking."""
        mock_config = AdapterConfig(
            language='mock',
            command=['echo'],
            transport='stdio',
            launch_type='test',
            file_extensions=['.mock', '.test']
        )
        
        with patch('smart_debugger.languages.dap.debugger.get_adapter_config', return_value=mock_config):
            debugger = DAPDebugger('mock')
            
            assert debugger.supports_file('test.mock')
            assert debugger.supports_file('file.test')
            assert not debugger.supports_file('file.py')
            assert not debugger.supports_file('file.js')
    
    def test_dap_debugger_validate_environment(self):
        """Test environment validation."""
        mock_config = Mock()
        mock_config.validate_command.return_value = True
        
        with patch('smart_debugger.languages.dap.debugger.get_adapter_config', return_value=mock_config):
            debugger = DAPDebugger('mock')
            assert debugger.validate_environment()
        
        mock_config.validate_command.return_value = False
        with patch('smart_debugger.languages.dap.debugger.get_adapter_config', return_value=mock_config):
            debugger = DAPDebugger('mock')
            assert not debugger.validate_environment()


class TestAdapterConfigs:
    """Test adapter configuration functionality."""
    
    def test_adapter_config_creation(self):
        """Test creating adapter configurations."""
        config = AdapterConfig(
            language='test',
            command=['test-debugger', '--dap'],
            transport='stdio',
            launch_type='test',
            file_extensions=['.test']
        )
        
        assert config.language == 'test'
        assert config.command == ['test-debugger', '--dap']
        assert config.transport == 'stdio'
        assert config.file_extensions == ['.test']
    
    def test_adapter_config_validation(self):
        """Test adapter configuration validation."""
        # Valid config
        config = AdapterConfig(
            language='test',
            command=['echo'],  # echo should be available
            transport='stdio',
            launch_type='test',
            file_extensions=['.test']
        )
        
        assert config.validate_command()
        
        # Invalid config
        config_invalid = AdapterConfig(
            language='test',
            command=['nonexistent-command'],
            transport='stdio',
            launch_type='test',
            file_extensions=['.test']
        )
        
        assert not config_invalid.validate_command()
    
    def test_get_adapter_config(self):
        """Test getting predefined adapter configs."""
        python_config = get_adapter_config('python')
        assert python_config is not None
        assert python_config.language == 'python'
        assert '.py' in python_config.file_extensions
        
        # Non-existent language
        invalid_config = get_adapter_config('nonexistent')
        assert invalid_config is None


class TestLanguageDetection:
    """Test language detection in multi-language context."""
    
    def test_detect_python_file(self):
        """Test detecting Python files."""
        detector = LanguageDetector()
        
        assert detector.detect_language('test.py') == 'python'
        assert detector.detect_language('script.pyw') == 'python'
    
    def test_detect_csharp_file(self):
        """Test detecting C# files."""
        detector = LanguageDetector()
        
        assert detector.detect_language('Program.cs') == 'csharp'
        assert detector.detect_language('script.csx') == 'csharp'
    
    def test_detect_javascript_file(self):
        """Test detecting JavaScript files."""
        detector = LanguageDetector()
        
        assert detector.detect_language('app.js') == 'javascript'
        assert detector.detect_language('module.mjs') == 'javascript'
        assert detector.detect_language('component.jsx') == 'javascript'
    
    def test_detect_typescript_file(self):
        """Test detecting TypeScript files."""
        detector = LanguageDetector()
        
        assert detector.detect_language('app.ts') == 'typescript'
        assert detector.detect_language('component.tsx') == 'typescript'


class TestDebugFileFunction:
    """Test the main debug_file function."""
    
    def test_debug_file_with_language_override(self):
        """Test debugging with explicit language specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 42\ny = 10\nresult = x + y")
            f.flush()
            test_file = f.name
        
        try:
            # Mock the actual debugging to avoid complexity
            with patch('smart_debugger.languages.python.PythonDebugger.debug') as mock_debug:
                mock_debug.return_value = DebugResult(
                    success=True,
                    result="52",
                    output="",
                    language="python"
                )
                
                result = debug_file(
                    file_path=test_file,
                    line_number=3,
                    expression="result",
                    language="python",
                    quiet_mode=True
                )
                
                assert result.success
                assert result.language == "python"
                assert result.result == "52"
                
        finally:
            os.unlink(test_file)
    
    def test_debug_file_auto_detection(self):
        """Test debugging with automatic language detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("value = 'hello world'")
            f.flush()
            test_file = f.name
        
        try:
            with patch('smart_debugger.languages.python.PythonDebugger.debug') as mock_debug:
                mock_debug.return_value = DebugResult(
                    success=True,
                    result="hello world",
                    output="",
                    language="python"
                )
                
                result = debug_file(
                    file_path=test_file,
                    line_number=1,
                    expression="value",
                    quiet_mode=True
                )
                
                assert result.success
                assert result.language == "python"
                
        finally:
            os.unlink(test_file)
    
    def test_debug_file_nonexistent(self):
        """Test debugging non-existent file."""
        result = debug_file(
            file_path="/path/to/nonexistent/file.py",
            line_number=1,
            expression="x",
            quiet_mode=True
        )
        
        assert not result.success
        assert ("not found" in result.error.lower() or 
                "no such file" in result.error.lower() or
                "traceback" in result.error.lower())
    
    def test_debug_file_unsupported_language(self):
        """Test debugging with unsupported language."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.unknown', delete=False) as f:
            f.write("some content")
            f.flush()
            test_file = f.name
        
        try:
            result = debug_file(
                file_path=test_file,
                line_number=1,
                expression="x",
                language="unsupported_lang",
                quiet_mode=True
            )
            
            assert not result.success
            assert "No debugger available" in result.error
            
        finally:
            os.unlink(test_file)
    
    def test_debug_file_invalid_environment(self):
        """Test debugging when environment is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 42")
            f.flush()
            test_file = f.name
        
        try:
            # Mock environment validation to fail
            with patch('smart_debugger.core.registry.DebuggerRegistry.is_environment_valid', return_value=False):
                result = debug_file(
                    file_path=test_file,
                    line_number=1,
                    expression="x",
                    language="python",
                    quiet_mode=True
                )
                
                assert not result.success
                assert "Environment validation failed" in result.error
                
        finally:
            os.unlink(test_file)


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_python_debugger_integration(self):
        """Test full Python debugging integration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_function():
    x = 42
    y = 10
    return x + y

if __name__ == "__main__":
    result = test_function()
    print(result)
""")
            f.flush()
            test_file = f.name
        
        try:
            # Test that we can create a debugger and it supports the file
            registry = setup_multi_language_debugger()
            debugger = registry.get_debugger('python')
            
            assert debugger.supports_file(test_file)
            assert debugger.validate_environment()
            assert debugger.get_language_name() == 'python'
            
        finally:
            os.unlink(test_file)
    
    def test_registry_plugin_architecture(self):
        """Test that the plugin architecture works correctly."""
        registry = setup_multi_language_debugger()
        
        # Should have multiple debuggers registered
        languages = registry.list_supported_languages()
        assert len(languages) >= 1
        
        # Should be able to get debugger info for each language
        for language in languages:
            info = registry.get_debugger_info(language)
            assert 'debugger_type' in info
            assert 'language' in info
            
        # Should be able to get debugger instances
        python_debugger = registry.get_debugger('python')
        assert isinstance(python_debugger, PythonDebugger)
    
    def test_language_detection_integration(self):
        """Test language detection integration with debugger selection."""
        detector = LanguageDetector()
        registry = setup_multi_language_debugger()
        
        # Test various file types
        test_cases = [
            ('test.py', 'python'),
            ('app.js', 'javascript'),
            ('script.ts', 'typescript'),
        ]
        
        for filename, expected_lang in test_cases:
            detected_lang = detector.detect_language(filename)
            assert detected_lang == expected_lang
            
            # If language is supported, should be able to get debugger
            if registry.has_debugger(detected_lang):
                debugger = registry.get_debugger(detected_lang)
                assert debugger.supports_file(filename)


# Run tests using Smart Debugger patterns
class TestSmartDebuggerUsage:
    """Test using Smart Debugger for debugging our multi-language implementation."""
    
    def test_debug_multi_language_setup_with_smart_debugger(self):
        """Use Smart Debugger to debug the multi-language setup process."""
        # This test demonstrates how to use Smart Debugger to debug our own code
        
        # Create a test script that uses our multi-language debugger
        test_script = """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from smart_debugger.multi_language import setup_multi_language_debugger

def test_setup():
    registry = setup_multi_language_debugger()
    languages = registry.list_supported_languages()
    return len(languages)

if __name__ == "__main__":
    count = test_setup()
    print(f"Registered {count} languages")
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            f.flush()
            script_path = f.name
        
        try:
            # We would use the Smart Debugger like this:
            # pydebug-stdin --quiet -f scratch/debug_setup.py script_path 8 -- -v
            
            # For unit testing, we just verify the script would work
            import subprocess
            import sys
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0
            assert "Registered" in result.stdout
            
        finally:
            os.unlink(script_path)


# Run with: python -m pytest tests/test_multi_language_debugger.py -v