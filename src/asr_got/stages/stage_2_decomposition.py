import logging
import datetime
from typing import Dict, Any, List

from asr_got.models.graph import ASRGoTGraph
from asr_got.models.node import Node
from asr_got.models.edge import Edge
from asr_got.utils.metadata_utils import generate_id

logger = logging.getLogger("asr-got-stage2")

class DecompositionStage:
    """
    Stage 2: Decomposition
    
    Breaks down the task into dimensions for structured analysis.
    """
    
    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the decomposition stage.
        
        Args:
            graph: The ASR-GoT graph
            context: Context from previous stages and initialization
        
        Returns:
            Dictionary with decomposition results
        """
        logger.info("Executing Decomposition Stage")
        
        # Get root node ID from initialization
        root_node_id = context.get("root_node_id")
        if not root_node_id or root_node_id not in graph.graph:
            logger.error("Root node not found")
            return {
                "summary": "Decomposition failed: Root node not found",
                "metrics": {}
            }
        
        query = context.get("query", "")
        parameters = context.get("parameters", {})
        
        # Define default dimensions as per P1.2
        default_dimensions = [
            {
                "label": "Scope",
                "description": "Define the boundaries of the research question"
            },
            {
                "label": "Objectives",
                "description": "Specific goals to be achieved"
            },
            {
                "label": "Constraints",
                "description": "Limitations and boundaries of the analysis"
            },
            {
                "label": "Data Needs",
                "description": "Information required to address the question"
            },
            {
                "label": "Use Cases",
                "description": "Practical applications of findings"
            },
            {
                "label": "Potential Biases",  # As per P1.17
                "description": "Sources of cognitive or methodological bias"
            },
            {
                "label": "Knowledge Gaps",  # As per P1.15
                "description": "Areas of uncertainty or missing information"
            }
        ]
        
        # Override with custom dimensions if provided
        dimensions = parameters.get("dimensions", default_dimensions)
        
        # Create dimension nodes
        dimension_nodes = []
        for i, dim in enumerate(dimensions):
            dim_id = f"dim_{i+1}"
            
            # Initial confidence vector per P1.2
            confidence = parameters.get("dimension_confidence", [0.8, 0.8, 0.8, 0.8])
            
            dimension_node = Node(
                node_id=dim_id,
                label=dim["label"],
                node_type="dimension",
                confidence=confidence,
                metadata={
                    "description": dim.get("description", ""),
                    "timestamp": str(datetime.datetime.now()),
                    "provenance": "Task decomposition",
                    "disciplinary_tags": context.get("disciplinary_tags", []),
                    "layer_id": parameters.get("dimension_layer", "root")
                }
            )
            
            # Add the dimension node to the graph
            graph.add_node(dimension_node)
            
            # Connect dimension to root node
            edge = Edge(
                edge_id=f"e_root_dim_{i+1}",
                source=root_node_id,
                target=dim_id,
                edge_type="decomposition",
                confidence=0.9,
                metadata={
                    "timestamp": str(datetime.datetime.now()),
                    "edge_subtype": "dimension"
                }
            )
            
            graph.add_edge(edge)
            dimension_nodes.append(dimension_node)
        
        logger.info(f"Decomposition complete: Created {len(dimension_nodes)} dimension nodes")
        
        return {
            "dimension_nodes": [node.node_id for node in dimension_nodes],
            "summary": f"Decomposed task into {len(dimension_nodes)} dimensions",
            "metrics": {
                "dimension_count": len(dimension_nodes)
            }
        }