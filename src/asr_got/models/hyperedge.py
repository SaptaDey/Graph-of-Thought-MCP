import datetime
from typing import List, Dict, Any, Optional

class Hyperedge:
    """
    Hyperedge class representing a multi-node connection in the ASR-GoT graph.
    
    Implements the hyperedge structure defined in P1.9.
    """
    
    def __init__(self, 
                 edge_id: str, 
                 nodes: List[str], 
                 confidence: float, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a hyperedge with its attributes.
        
        Args:
            edge_id: Unique identifier for the hyperedge
            nodes: List of node IDs connected by this hyperedge
            confidence: Hyperedge confidence value
            metadata: Additional metadata
        """
        self.edge_id = edge_id
        self.nodes = nodes
        self.confidence = confidence
        
        # Initialize with default metadata if not provided
        self.metadata = metadata or {}
        
        # Ensure minimum required metadata is present
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = str(datetime.datetime.now())
        
        # Validate that a hyperedge connects at least 3 nodes
        if len(nodes) < 3:
            raise ValueError("A hyperedge must connect at least 3 nodes")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the hyperedge to a dictionary representation.
        """
        return {
            "edge_id": self.edge_id,
            "nodes": self.nodes,
            "confidence": self.confidence,
            **self.metadata  # Include all metadata fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hyperedge':
        """
        Create a Hyperedge instance from a dictionary.
        """
        edge_id = data.pop("edge_id")
        nodes = data.pop("nodes")
        confidence = data.pop("confidence")
        
        # All remaining fields become metadata
        metadata = data
        
        return cls(edge_id, nodes, confidence, metadata)