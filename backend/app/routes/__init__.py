"""
Routes package initialization.
"""

from .health import health_bp
from .chat import chat_bp
from .voice import voice_bp

__all__ = ['health_bp', 'chat_bp', 'voice_bp']
