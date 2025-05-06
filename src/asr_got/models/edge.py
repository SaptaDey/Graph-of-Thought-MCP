import datetime
from typing import Dict, Any, Optional

class Edge:
    """
    Edge class representing a directed connection between nodes in the ASR-GoT graph.
    
    Implements the edge structure defined in P1.10 and extended in P1.24, P1.25.
    """
    
    def __init__(self, 
                 edge_id: str, 
                 source: str, 
                 target: str, 
                 edge_type: str, 
                 confidence: float, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an edge with its attributes.
        
        Args:
            edge_id: Unique identifier for the edge
            source: ID of the source node
            target: ID of the target node
            edge_type: Type of edge (e.g., 'supportive', 'contradictory', 'causal', 'temporal')
            confidence: Edge confidence value
            metadata: Additional metadata including causal and temporal metadata
        """
        self.edge_id = edge_id
        self.source = source
        self.target = target
        self.edge_type = edge_type
        self.confidence = confidence
        
        # Initialize with default metadata if not provided
        self.metadata = metadata or {}
        
        # Ensure minimum required metadata is present
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = str(datetime.datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the edge to a dictionary representation.
        """
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type,
            "confidence": self.confidence,
            **self.metadata  # Include all metadata fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """
        Create an Edge instance from a dictionary.
        """
        edge_id = data.pop("edge_id")
        source = data.pop("source")
        target = data.pop("target")
        edge_type = data.pop("edge_type")
        confidence = data.pop("confidence")
        
        # All remaining fields become metadata
        metadata = data
        
        return cls(edge_id, source, target, edge_type, confidence, metadata)