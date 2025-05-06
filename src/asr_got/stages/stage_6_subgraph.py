import logging
import networkx as nx
from typing import Dict, Any, List, Set, Tuple

from asr_got.models.graph import ASRGoTGraph

logger = logging.getLogger("asr-got-stage6")

class SubgraphStage:
    """
    Stage 6: Subgraph Extraction
    
    Extracts relevant subgraphs for final analysis and output.
    """
    
    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the subgraph extraction stage.
        
        Args:
            graph: The ASR-GoT graph
            context: Context from previous stages and initialization
        
        Returns:
            Dictionary with subgraph extraction results
        """
        logger.info("Executing Subgraph Extraction Stage")
        
        parameters = context.get("parameters", {})
        
        # Define extraction criteria based on P1.6
        extraction_criteria = parameters.get("extraction_criteria", {})
        
        # Default criteria if not specified
        min_confidence = extraction_criteria.get("min_confidence", 0.6)
        min_impact = extraction_criteria.get("min_impact", 0.5)
        focus_disciplines = extraction_criteria.get("focus_disciplines", [])
        temporal_recency = extraction_criteria.get("temporal_recency", 0)  # Days
        edge_patterns = extraction_criteria.get("edge_patterns", [])
        focus_layers = extraction_criteria.get("focus_layers", [])
        
        # Track extracted subgraphs
        extracted_subgraphs = []
        
        # 1. Extract high-confidence subgraph
        high_confidence_nodes = []
        for node_id, data in graph.graph.nodes(data=True):
            # Get confidence vector
            confidence = data.get("confidence", [])
            if not confidence:
                continue
            
            # Calculate average confidence
            avg_confidence = sum(confidence) / len(confidence)
            
            # Check if above threshold
            if avg_confidence >= min_confidence:
                high_confidence_nodes.append(node_id)
        
        # Extract subgraph
        high_confidence_subgraph = graph.graph.subgraph(high_confidence_nodes)
        if high_confidence_subgraph.number_of_nodes() > 0:
            extracted_subgraphs.append({
                "name": "high_confidence",
                "description": f"Subgraph containing nodes with confidence >= {min_confidence}",
                "nodes": list(high_confidence_subgraph.nodes()),
                "edges": list(high_confidence_subgraph.edges()),
                "metrics": {
                    "node_count": high_confidence_subgraph.number_of_nodes(),
                    "edge_count": high_confidence_subgraph.number_of_edges()
                }
            })
        
        # 2. Extract high-impact subgraph
        high_impact_nodes = []
        for node_id, data in graph.graph.nodes(data=True):
            # Get impact score
            impact = data.get("impact_score", 0)
            
            # Check if above threshold
            if impact >= min_impact:
                high_impact_nodes.append(node_id)
        
        # Extract subgraph
        high_impact_subgraph = graph.graph.subgraph(high_impact_nodes)
        if high_impact_subgraph.number_of_nodes() > 0:
            extracted_subgraphs.append({
                "name": "high_impact",
                "description": f"Subgraph containing nodes with impact >= {min_impact}",
                "nodes": list(high_impact_subgraph.nodes()),
                "edges": list(high_impact_subgraph.edges()),
                "metrics": {
                    "node_count": high_impact_subgraph.number_of_nodes(),
                    "edge_count": high_impact_subgraph.number_of_edges()
                }
            })
        
        # 3. Extract discipline-focused subgraph if specified
        if focus_disciplines:
            discipline_nodes = []
            for node_id, data in graph.graph.nodes(data=True):
                # Get disciplinary tags
                tags = data.get("disciplinary_tags", [])
                
                # Check if any tag matches focus
                if any(tag in focus_disciplines for tag in tags):
                    discipline_nodes.append(node_id)
            
            # Extract subgraph
            discipline_subgraph = graph.graph.subgraph(discipline_nodes)
            if discipline_subgraph.number_of_nodes() > 0:
                extracted_subgraphs.append({
                    "name": "discipline_focus",
                    "description": f"Subgraph focused on disciplines: {', '.join(focus_disciplines)}",
                    "nodes": list(discipline_subgraph.nodes()),
                    "edges": list(discipline_subgraph.edges()),
                    "metrics": {
                        "node_count": discipline_subgraph.number_of_nodes(),
                        "edge_count": discipline_subgraph.number_of_edges()
                    }
                })
        
        # 4. Extract layer-focused subgraph if specified
        if focus_layers and graph.layers:
            layer_nodes = []
            for layer_id in focus_layers:
                if layer_id in graph.layers:
                    layer_nodes.extend(graph.layers[layer_id])
            
            # Extract subgraph
            layer_subgraph = graph.graph.subgraph(layer_nodes)
            if layer_subgraph.number_of_nodes() > 0:
                extracted_subgraphs.append({
                    "name": "layer_focus",
                    "description": f"Subgraph focused on layers: {', '.join(focus_layers)}",
                    "nodes": list(layer_subgraph.nodes()),
                    "edges": list(layer_subgraph.edges()),
                    "metrics": {
                        "node_count": layer_subgraph.number_of_nodes(),
                        "edge_count": layer_subgraph.number_of_edges()
                    }
                })
        
        # 5. Extract edge pattern subgraph if specified
        if edge_patterns:
            pattern_nodes = set()
            for u, v, data in graph.graph.edges(data=True):
                # Get edge type
                edge_type = data.get("edge_type", "")
                edge_subtype = data.get("edge_subtype", "")
                
                # Check if type matches any pattern
                if edge_type in edge_patterns or edge_subtype in edge_patterns:
                    pattern_nodes.add(u)
                    pattern_nodes.add(v)
            
            # Extract subgraph
            pattern_subgraph = graph.graph.subgraph(pattern_nodes)
            if pattern_subgraph.number_of_nodes() > 0:
                extracted_subgraphs.append({
                    "name": "edge_pattern",
                    "description": f"Subgraph containing edge patterns: {', '.join(edge_patterns)}",
                    "nodes": list(pattern_subgraph.nodes()),
                    "edges": list(pattern_subgraph.edges()),
                    "metrics": {
                        "node_count": pattern_subgraph.number_of_nodes(),
                        "edge_count": pattern_subgraph.number_of_edges()
                    }
                })
        
        # 6. Extract interdisciplinary bridge subgraph if IBNs exist
        if graph.ibns:
            ibn_nodes = set(graph.ibns)
            
            # Add connected nodes
            for ibn_id in graph.ibns:
                if ibn_id in graph.graph:
                    ibn_nodes.update(graph.graph.predecessors(ibn_id))
                    ibn_nodes.update(graph.graph.successors(ibn_id))
            
            # Extract subgraph
            ibn_subgraph = graph.graph.subgraph(ibn_nodes)
            if ibn_subgraph.number_of_nodes() > 0:
                extracted_subgraphs.append({
                    "name": "interdisciplinary",
                    "description": "Subgraph highlighting interdisciplinary connections",
                    "nodes": list(ibn_subgraph.nodes()),
                    "edges": list(ibn_subgraph.edges()),
                    "metrics": {
                        "node_count": ibn_subgraph.number_of_nodes(),
                        "edge_count": ibn_subgraph.number_of_edges(),
                        "ibn_count": len(graph.ibns)
                    }
                })
        
        logger.info(f"Subgraph extraction complete: Extracted {len(extracted_subgraphs)} subgraphs")
        
        return {
            "subgraphs": extracted_subgraphs,
            "summary": f"Extracted {len(extracted_subgraphs)} focused subgraphs for analysis",
            "metrics": {
                "subgraph_count": len(extracted_subgraphs)
            }
        }