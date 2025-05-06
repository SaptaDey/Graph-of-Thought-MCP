import logging
from typing import Dict, Any, List
import datetime

from asr_got.models.graph import ASRGoTGraph
from asr_got.models.node import Node

logger = logging.getLogger("asr-got-stage1")

class InitializationStage:
    """
    Stage 1: Initialization
    
    Creates the root node (n₀) of the graph with initial high confidence.
    """
    
    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the initialization stage.
        """
        logger.info("Executing Initialization Stage")
        
        query = context.get("query", "")
        parameters = context.get("parameters", {})
        
        # Create the root node with task understanding
        root_node = Node(
            node_id="n0",
            label="Task Understanding",
            node_type="root",
            confidence=[0.9, 0.9, 0.9, 0.9],  # High initial confidence per P1.5
            metadata={
                "query": query,
                "timestamp": str(datetime.datetime.now()),
                "provenance": "User query",
                "epistemic_status": "Initial",
                "disciplinary_tags": self._extract_disciplines(query, parameters),
                "layer_id": parameters.get("initial_layer", "root")
            }
        )
        
        # Add the root node to the graph
        graph.add_node(root_node)
        
        # Setup multi-layer structure if specified in parameters (P1.23)
        if "layers" in parameters:
            for layer_id, layer_info in parameters["layers"].items():
                graph.layers[layer_id] = set()
        
        logger.info(f"Initialization complete: Root node created with ID {root_node.node_id}")
        
        return {
            "root_node_id": root_node.node_id,
            "summary": "Initialized graph with root node based on query understanding",
            "metrics": {
                "initial_confidence": root_node.confidence
            }
        }
    
    def _extract_disciplines(self, query: str, parameters: Dict[str, Any]) -> List[str]:
        """
        Extract relevant disciplinary tags from the query and parameters.
        Uses K3.3 and K3.4 from user profile for context.
        """
        # Default disciplines from Dr. Dey's profile (K3.3, K3.4)
        default_disciplines = [
            "skin_immunology", 
            "dermatology", 
            "cutaneous_malignancies",
            "ctcl",
            "chromosomal_instability",
            "skin_microbiome",
            "cancer_progression",
            "therapeutic_targets",
            "genomics",
            "molecular_biology",
            "machine_learning",
            "biomedical_llms"
        ]
        
        # Use specified disciplines if provided in parameters
        if "disciplines" in parameters:
            return parameters["disciplines"]
        
        # TODO: Implement more sophisticated discipline extraction based on query
        # This would use NLP techniques to identify relevant fields
        
        # For now, return the default disciplines
        return default_disciplines