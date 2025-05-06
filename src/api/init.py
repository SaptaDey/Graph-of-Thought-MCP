# src/api/__init__.py
"""
ASR-GoT MCP Server: API Module

This module provides the API routes and schemas for interacting with 
the ASR-GoT MCP server and Claude integration.
"""

from src.api.routes import router
from src.api.schema import (
    QueryRequest, 
    QueryResponse, 
    Node, 
    Edge, 
    Hyperedge,
    GraphState,
    ClaudeRequest
)