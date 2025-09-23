"""Expertise MCP server for discipline evaluation."""

from .server import main, server
from .tools import evaluate, vote

__version__ = "0.1.0"
__all__ = ["main", "server", "evaluate", "vote"]