"""Registry for managing and discovering debugger implementations."""

from typing import Dict, List, Optional, Type, Callable, Union
from .interface import DebuggerInterface
import logging


logger = logging.getLogger(__name__)


class DebuggerRegistry:
    """Central registry for all debugger implementations."""
    
    def __init__(self):
        """Initialize the debugger registry."""
        self._debuggers: Dict[str, Union[Type[DebuggerInterface], Callable[[], DebuggerInterface]]] = {}
        self._instances: Dict[str, DebuggerInterface] = {}  # Cache for singleton instances
        self._environment_validated: Dict[str, bool] = {}  # Cache for environment validation
    
    def register_debugger(
        self, 
        language: str, 
        debugger_factory: Union[Type[DebuggerInterface], Callable[[], DebuggerInterface]],
        validate_environment: bool = True
    ) -> None:
        """
        Register a debugger for a specific language.
        
        Args:
            language: Language identifier (e.g., 'python', 'csharp')
            debugger_factory: Either a class or a factory function that returns a DebuggerInterface
            validate_environment: Whether to validate the environment when registering
        """
        if language in self._debuggers:
            logger.warning(f"Overwriting existing debugger for language: {language}")
        
        self._debuggers[language] = debugger_factory
        
        # Optionally validate environment on registration
        if validate_environment:
            try:
                debugger = self._create_instance(language)
                is_valid = debugger.validate_environment()
                self._environment_validated[language] = is_valid
                if not is_valid:
                    logger.warning(f"Environment validation failed for {language} debugger")
            except Exception as e:
                logger.error(f"Failed to validate environment for {language}: {e}")
                self._environment_validated[language] = False
    
    def unregister_debugger(self, language: str) -> None:
        """
        Unregister a debugger for a specific language.
        
        Args:
            language: Language identifier to unregister
        """
        if language in self._debuggers:
            del self._debuggers[language]
            if language in self._instances:
                del self._instances[language]
            if language in self._environment_validated:
                del self._environment_validated[language]
            logger.info(f"Unregistered debugger for language: {language}")
    
    def get_debugger(self, language: str, use_singleton: bool = False) -> DebuggerInterface:
        """
        Get a debugger instance for the specified language.
        
        Args:
            language: Language identifier
            use_singleton: Whether to reuse the same instance (useful for stateful debuggers)
            
        Returns:
            DebuggerInterface instance for the language
            
        Raises:
            ValueError: If no debugger is registered for the language
        """
        if language not in self._debuggers:
            available = self.list_supported_languages()
            raise ValueError(
                f"No debugger registered for language: {language}. "
                f"Available languages: {', '.join(available)}"
            )
        
        if use_singleton and language in self._instances:
            return self._instances[language]
        
        debugger = self._create_instance(language)
        
        if use_singleton:
            self._instances[language] = debugger
        
        return debugger
    
    def _create_instance(self, language: str) -> DebuggerInterface:
        """Create a new debugger instance for the language."""
        factory = self._debuggers[language]
        
        # Handle both class and factory function
        try:
            if isinstance(factory, type):
                return factory()
            elif callable(factory):
                return factory()
            else:
                raise TypeError(f"Invalid debugger factory for language {language}")
        except Exception as e:
            raise TypeError(f"Failed to create debugger instance for {language}: {e}")
    
    def has_debugger(self, language: str) -> bool:
        """
        Check if a debugger is registered for the language.
        
        Args:
            language: Language identifier
            
        Returns:
            True if a debugger is registered
        """
        return language in self._debuggers
    
    def is_environment_valid(self, language: str) -> bool:
        """
        Check if the environment is valid for the language debugger.
        
        Args:
            language: Language identifier
            
        Returns:
            True if environment is valid or unknown, False if validation failed
        """
        # Return cached result if available
        if language in self._environment_validated:
            return self._environment_validated[language]
        
        # If not cached, validate now
        if not self.has_debugger(language):
            return False
        
        try:
            debugger = self.get_debugger(language)
            is_valid = debugger.validate_environment()
            self._environment_validated[language] = is_valid
            return is_valid
        except Exception:
            return False
    
    def list_supported_languages(self) -> List[str]:
        """
        Get a list of all supported languages.
        
        Returns:
            List of language identifiers
        """
        return sorted(list(self._debuggers.keys()))
    
    def list_available_languages(self) -> List[str]:
        """
        Get a list of languages with valid environments.
        
        Returns:
            List of language identifiers that have valid environments
        """
        available = []
        for language in self.list_supported_languages():
            if self.is_environment_valid(language):
                available.append(language)
        return available
    
    def get_debugger_info(self, language: str) -> Dict[str, any]:
        """
        Get information about a registered debugger.
        
        Args:
            language: Language identifier
            
        Returns:
            Dictionary with debugger information
        """
        if not self.has_debugger(language):
            raise ValueError(f"No debugger registered for language: {language}")
        
        try:
            debugger = self.get_debugger(language)
            return {
                'language': language,
                'debugger_type': type(debugger).__name__,
                'environment_valid': self.is_environment_valid(language),
                'language_name': debugger.get_language_name(),
            }
        except Exception as e:
            return {
                'language': language,
                'error': str(e),
                'environment_valid': False,
            }
    
    def discover_debuggers(self) -> None:
        """
        Auto-discover and register available debuggers.
        This method should be overridden or extended by specific implementations.
        """
        logger.info("Discovering debuggers...")
        # This will be implemented when we have actual debugger implementations
        # For now, it's a placeholder for the plugin discovery mechanism
    
    def clear(self) -> None:
        """Clear all registered debuggers."""
        self._debuggers.clear()
        self._instances.clear()
        self._environment_validated.clear()
        logger.info("Cleared all registered debuggers")


# Global registry instance
_global_registry: Optional[DebuggerRegistry] = None


def get_global_registry() -> DebuggerRegistry:
    """Get the global debugger registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = DebuggerRegistry()
    return _global_registry


def register_debugger(
    language: str, 
    debugger_factory: Union[Type[DebuggerInterface], Callable[[], DebuggerInterface]],
    validate_environment: bool = True
) -> None:
    """
    Register a debugger in the global registry.
    
    Args:
        language: Language identifier
        debugger_factory: Debugger class or factory function
        validate_environment: Whether to validate the environment
    """
    registry = get_global_registry()
    registry.register_debugger(language, debugger_factory, validate_environment)