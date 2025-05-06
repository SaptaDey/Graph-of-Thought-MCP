from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., description="The research query to process")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context for processing")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Custom parameters for the ASR-GoT process")

class Node(BaseModel):
    node_id: str
    label: str
    type: str
    confidence: List[float]
    metadata: Dict[str, Any]

class Edge(BaseModel):
    edge_id: str
    source: str
    target: str
    edge_type: str
    confidence: float
    metadata: Dict[str, Any]

class Hyperedge(BaseModel):
    edge_id: str
    nodes: List[str]
    confidence: float
    metadata: Dict[str, Any]

class GraphState(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    hyperedges: List[Hyperedge]
    layers: Optional[Dict[str, List[str]]] = None
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    result: Dict[str, Any]
    reasoning_trace: List[Dict[str, Any]]
    confidence: List[float]
    graph_state: GraphState

class ClaudeRequest(BaseModel):
    query: str = Field(..., description="The query to send to Claude")
    session_id: Optional[str] = Field(None, description="Optional session ID for continuing a conversation")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for Claude")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Custom parameters for processing")
    process_response: bool = Field(True, description="Whether to process Claude's response through ASR-GoT")