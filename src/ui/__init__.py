"""
UI package initialization.
Contains UI components and styles for the application.
"""
from .components import MessageBubble, ModelSelector, AuthScreen
from .styles import AppStyles

__all__ = [
    'MessageBubble',
    'ModelSelector',
    'AppStyles',
    'AuthScreen'
]
__version__ = '1.0.0'
