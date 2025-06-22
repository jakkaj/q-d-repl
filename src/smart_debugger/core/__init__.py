"""Core components for the multi-language Smart Debugger."""

from .interface import DebuggerInterface, DebugResult
from .detector import LanguageDetector
from .registry import DebuggerRegistry

__all__ = [
    'DebuggerInterface',
    'DebugResult',
    'LanguageDetector',
    'DebuggerRegistry',
]