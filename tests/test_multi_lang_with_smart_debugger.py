"""Test multi-language debugger using Smart Debugger itself."""

import pytest
import tempfile
import os
from pathlib import Path


class TestMultiLanguageWithSmartDebugger:
    """Test the multi-language debugger by using Smart Debugger to debug it."""
    
    def test_debug_registry_setup_process(self):
        """Use Smart Debugger to inspect registry setup process."""
        # Create a test script that sets up the multi-language debugger
        test_script = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from smart_debugger.multi_language import setup_multi_language_debugger
from smart_debugger.core import LanguageDetector

def setup_and_inspect():
    # This is where we want to set a breakpoint to inspect the process
    registry = setup_multi_language_debugger()
    detector = LanguageDetector()
    
    # Return some info for verification
    return {
        'registry_languages': registry.list_supported_languages(),
        'available_languages': registry.list_available_languages(),
        'detector_extensions': len(detector.get_supported_extensions())
    }

if __name__ == "__main__":
    result = setup_and_inspect()
    print(f"Setup complete: {result}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            f.flush()
            test_file = f.name
        
        try:
            # This demonstrates how to use Smart Debugger to debug our own code
            # We would run: pydebug-stdin --quiet -f scratch/debug_multi_lang_registry.py test_file 9 -- -v
            
            # For the unit test, verify the script works
            import subprocess
            import sys
            
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            assert result.returncode == 0
            assert "Setup complete" in result.stdout
            assert "registry_languages" in result.stdout
            
        finally:
            os.unlink(test_file)
    
    def test_debug_language_detection_process(self):
        """Use Smart Debugger to inspect language detection process."""
        test_script = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from smart_debugger.core import LanguageDetector

def test_language_detection():
    detector = LanguageDetector()
    
    # Test various file types - set breakpoint here to inspect detector state
    test_files = ['app.py', 'Program.cs', 'script.js', 'component.ts']
    results = {}
    
    for filename in test_files:
        try:
            language = detector.detect_language(filename)
            results[filename] = language
        except Exception as e:
            results[filename] = f"Error: {e}"
    
    return results

if __name__ == "__main__":
    results = test_language_detection()
    for filename, language in results.items():
        print(f"{filename} -> {language}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            f.flush()
            test_file = f.name
        
        try:
            # This shows how to debug the language detection process
            # Command: pydebug-stdin --quiet -f scratch/debug_multi_lang_registry.py test_file 12 -- -v
            
            import subprocess
            import sys
            
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0
            assert "app.py -> python" in result.stdout
            assert "Program.cs -> csharp" in result.stdout
            assert "script.js -> javascript" in result.stdout
            assert "component.ts -> typescript" in result.stdout
            
        finally:
            os.unlink(test_file)
    
    def test_debug_debugger_factory_creation(self):
        """Use Smart Debugger to inspect debugger factory creation."""
        test_script = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from smart_debugger.core import DebuggerRegistry
from smart_debugger.languages.python import PythonDebugger
from smart_debugger.languages.dap import DAPDebugger

def test_debugger_creation():
    registry = DebuggerRegistry()
    
    # Register Python debugger
    registry.register_debugger('python', PythonDebugger, validate_environment=False)
    
    # Create a mock DAP debugger factory
    def create_mock_dap():
        # This is where we could set a breakpoint to inspect creation
        return type('MockDAPDebugger', (), {
            'get_language_name': lambda: 'mock',
            'supports_file': lambda x: True,
            'validate_environment': lambda: True
        })()
    
    registry.register_debugger('mock', create_mock_dap, validate_environment=False)
    
    # Test getting debuggers
    python_debugger = registry.get_debugger('python')
    mock_debugger = registry.get_debugger('mock')
    
    return {
        'python_type': type(python_debugger).__name__,
        'mock_type': type(mock_debugger).__name__,
        'registry_size': len(registry.list_supported_languages())
    }

if __name__ == "__main__":
    result = test_debugger_creation()
    print(f"Debugger creation test: {result}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            f.flush()
            test_file = f.name
        
        try:
            # This demonstrates debugging the debugger factory pattern
            # Command: pydebug-stdin --quiet -f scratch/debug_multi_lang_registry.py test_file 17 -- -v
            
            import subprocess
            import sys
            
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0
            assert "PythonDebugger" in result.stdout
            assert "registry_size" in result.stdout
            
        finally:
            os.unlink(test_file)


# To run these tests with actual Smart Debugger debugging:
# 
# 1. Test registry setup:
#    echo "print(f'Registry languages: {registry.list_supported_languages()}')" > scratch/debug_setup.py
#    pydebug-stdin --quiet -f scratch/debug_setup.py tests/test_multi_lang_with_smart_debugger.py 20 -- -v
#
# 2. Test language detection:
#    echo "print(f'Detector extensions: {list(detector.get_supported_extensions())[:5]}')" > scratch/debug_detection.py  
#    pydebug-stdin --quiet -f scratch/debug_detection.py tests/test_multi_lang_with_smart_debugger.py 55 -- -v
#
# 3. Test debugger creation:
#    echo "print(f'Creating debugger for: {create_mock_dap}')" > scratch/debug_creation.py
#    pydebug-stdin --quiet -f scratch/debug_creation.py tests/test_multi_lang_with_smart_debugger.py 100 -- -v