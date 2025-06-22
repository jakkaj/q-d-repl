"""Multi-language debugger bootstrap and registry setup."""

import logging
from typing import Optional

from .core import DebuggerRegistry, LanguageDetector, DebugResult
from .core.registry import get_global_registry, register_debugger
from .languages.python import PythonDebugger
from .languages.dap import DAPDebugger
from .languages.adapters.configs import list_available_languages, get_adapter_config


logger = logging.getLogger(__name__)


def setup_multi_language_debugger() -> DebuggerRegistry:
    """
    Set up the multi-language debugger with all available language implementations.
    
    Returns:
        DebuggerRegistry instance with all supported debuggers registered
    """
    registry = get_global_registry()
    
    # Clear any existing registrations
    registry.clear()
    
    # Register Python debugger (uses sys.settrace)
    logger.info("Registering Python debugger")
    register_debugger('python', PythonDebugger, validate_environment=False)  # Don't validate yet
    
    # Import here to avoid circular dependency
    from .languages.adapters.configs import list_available_languages as get_available_dap_languages
    
    # Register DAP debuggers for available languages
    available_dap_languages = get_available_dap_languages()
    logger.info(f"Available DAP languages: {available_dap_languages}")
    
    for language in available_dap_languages:
        if language != 'python':  # Python already registered with native implementation
            logger.info(f"Registering DAP debugger for {language}")
            register_debugger(
                language, 
                lambda lang=language: DAPDebugger(lang),  # Capture language in closure
                validate_environment=False  # Don't validate yet
            )
    
    # Log registered languages
    registered = registry.list_supported_languages()
    
    logger.info(f"Registered languages: {registered}")
    
    return registry


def debug_file(
    file_path: str,
    line_number: int,
    expression: str,
    language: Optional[str] = None,
    args: Optional[list] = None,
    quiet_mode: bool = False
) -> DebugResult:
    """
    Debug a file using the appropriate language debugger.
    
    Args:
        file_path: Path to the file to debug
        line_number: Line number to set breakpoint at
        expression: Expression to evaluate at breakpoint
        language: Optional language override (auto-detected if None)
        args: Optional command-line arguments
        quiet_mode: Whether to minimize output
        
    Returns:
        DebugResult with evaluation result or error
    """
    # Set up debugger registry
    registry = setup_multi_language_debugger()
    
    try:
        # Detect language if not specified
        if language is None:
            detector = LanguageDetector()
            language = detector.detect_language(file_path)
            logger.info(f"Detected language: {language}")
        
        # Get debugger for language
        if not registry.has_debugger(language):
            return DebugResult(
                success=False,
                result=None,
                output="",
                error=f"No debugger available for language: {language}",
                language=language
            )
        
        # Check environment
        if not registry.is_environment_valid(language):
            adapter_config = get_adapter_config(language)
            missing_command = adapter_config.command[0] if adapter_config else "unknown"
            return DebugResult(
                success=False,
                result=None,
                output="",
                error=f"Environment validation failed for {language}. Missing: {missing_command}",
                language=language
            )
        
        # Get and use debugger
        debugger = registry.get_debugger(language)
        
        if not debugger.supports_file(file_path):
            return DebugResult(
                success=False,
                result=None,
                output="",
                error=f"File {file_path} not supported by {language} debugger",
                language=language
            )
        
        # Perform debugging
        logger.info(f"Debugging {file_path}:{line_number} with {language} debugger")
        result = debugger.debug(file_path, line_number, expression, args, quiet_mode)
        
        if result.success:
            logger.info(f"Debugging successful: {result.result}")
        else:
            logger.error(f"Debugging failed: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Multi-language debugging error: {e}")
        return DebugResult(
            success=False,
            result=None,
            output="",
            error=str(e),
            language=language or "unknown"
        )


def list_supported_languages() -> list:
    """Get list of all supported languages."""
    registry = setup_multi_language_debugger()
    return registry.list_supported_languages()


def list_available_languages() -> list:
    """Get list of languages with valid environments."""
    registry = setup_multi_language_debugger()
    return registry.list_available_languages()


def get_language_info(language: str) -> dict:
    """Get information about a specific language debugger."""
    registry = setup_multi_language_debugger()
    
    if not registry.has_debugger(language):
        return {'supported': False, 'error': f'Language {language} not supported'}
    
    try:
        info = registry.get_debugger_info(language)
        
        # Add adapter info for DAP debuggers
        if language != 'python':
            try:
                debugger = registry.get_debugger(language)
                if hasattr(debugger, 'get_adapter_info'):
                    info['adapter'] = debugger.get_adapter_info()
            except:
                pass
        
        return info
        
    except Exception as e:
        return {'supported': True, 'error': str(e)}


if __name__ == "__main__":
    # Quick test/demonstration
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("Multi-Language Smart Debugger")
    print("=" * 40)
    
    # Show supported languages
    supported = list_supported_languages()
    available = list_available_languages()
    
    print(f"Supported languages: {', '.join(supported)}")
    print(f"Available languages: {', '.join(available)}")
    print()
    
    # Show language details
    for lang in supported:
        info = get_language_info(lang)
        status = "✓" if lang in available else "✗"
        print(f"{status} {lang}: {info.get('debugger_type', 'Unknown')}")
        if 'adapter' in info:
            adapter_info = info['adapter']
            print(f"  Command: {adapter_info.get('command', 'N/A')}")
            print(f"  Transport: {adapter_info.get('transport', 'N/A')}")
        print()
    
    print(f"Multi-language debugger setup complete!")
    print(f"Use debug_file() function to debug files in any supported language.")