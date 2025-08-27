"""
MCP Text-to-Speech Package
Provides offline and online text-to-speech capabilities for MCP (Model Context Protocol)
"""

__version__ = "1.0.0"
__author__ = "MCP TTS Developer"
__description__ = "Local and online text-to-speech MCP server with multi-engine support"

# Import main components
try:
    from .server import OfflineTextToSpeechServer
except ImportError:
    OfflineTextToSpeechServer = None

try:
    from .server_online import OnlineTextToSpeechServer
except ImportError:
    OnlineTextToSpeechServer = None

__all__ = [
    "OfflineTextToSpeechServer",
    "OnlineTextToSpeechServer",
]
