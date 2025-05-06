import datetime
from typing import List, Dict, Any, Optional

class Node:
    """
    Node class representing a vertex in the ASR-GoT graph.
    
    Implements the node structure defined in P1.12 metadata schema.
    """
    
    def __init__(self, 
                 node_id: str, 
                 label: str, 
                 node_type: str, 
                 confidence: List[float], 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a node with its attributes.
        
        Args:
            node_id: Unique identifier for the node
            label: Human-readable label
            node_type: Type of node (e.g., 'root', 'dimension', 'hypothesis', 'evidence')
            confidence: Multi-dimensional confidence vector [empirical, theoretical, methodological, consensus]
            metadata: Additional metadata as per P1.12
        """
        self.node_id = node_id
        self.label = label
        self.node_type = node_type
        self.confidence = confidence
        
        # Initialize with default metadata if not provided
        self.metadata = metadata or {}
        
        # Ensure minimum required metadata is present
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = str(datetime.datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node to a dictionary representation.
        """
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "confidence": self.confidence,
            **self.metadata  # Include all metadata fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """
        Create a Node instance from a dictionary.
        """
        node_id = data.pop("node_id")
        label = data.pop("label")
        node_type = data.pop("node_type")
        confidence = data.pop("confidence")
        
        # All remaining fields become metadata
        metadata = data
        
        return cls(node_id, label, node_type, confidence, metadata)