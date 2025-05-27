import logging
import datetime
from typing import Dict, Any, List, Set

from asr_got.models.graph import ASRGoTGraph
from asr_got.utils.metadata_utils import calculate_semantic_overlap

logger = logging.getLogger("asr-got-stage5")

class PruningStage:
    """
    Stage 5: Pruning/Merging

    Simplifies the graph by removing low-confidence or redundant nodes.
    """

    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the pruning and merging stage.

        Args:
            graph: The ASR-GoT graph
            context: Context from previous stages and initialization

        Returns:
            Dictionary with pruning/merging results
        """
        logger.info("Executing Pruning/Merging Stage")

        parameters = context.get("parameters", {})

        # Pruning threshold from P1.5
        pruning_threshold = parameters.get("pruning_threshold", 0.2)

        # Impact score threshold from P1.28
        impact_threshold = parameters.get("impact_threshold", 0.3)

        # Merging threshold from P1.5
        merging_threshold = parameters.get("merging_threshold", 0.8)

        # Track metrics
        pruned_nodes = 0
        merged_nodes = 0

        # 1. Pruning low-confidence nodes
        nodes_to_prune = set()
        for node_id, node_data in graph.graph.nodes(data=True):
            # Skip root and dimension nodes
            if node_data.get("node_type") in ["root", "dimension"]:
                continue

            # Get confidence vector
            confidence = node_data.get("confidence", [])
            if not confidence:
                continue

            # Calculate minimum confidence
            min_confidence = min(confidence)

            # Get impact score
            impact_score = node_data.get("impact_score", 0.5)

            # Check if below thresholds
            if min_confidence < pruning_threshold and impact_score < impact_threshold:
                nodes_to_prune.add(node_id)
                logger.debug(f"Marked node {node_id} for pruning: confidence={min_confidence}, impact={impact_score}")

        # 2. Merging similar nodes
        nodes_to_merge = {}  # Maps node_id -> node_id to merge into

        # Group nodes by type
        node_types = {}
        for node_id, node_data in graph.graph.nodes(data=True):
            node_type = node_data.get("node_type")
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node_id)

        # Check each group for similar nodes
        for node_type, nodes in node_types.items():
            # Skip types with only one node
            if len(nodes) <= 1:
                continue

            # Check all pairs
            for i, node1_id in enumerate(nodes):
                # Skip if marked for pruning
                if node1_id in nodes_to_prune:
                    continue

                for j, node2_id in enumerate(nodes[i+1:], i+1):
                    # Skip if marked for pruning or already merging
                    if node2_id in nodes_to_prune or node2_id in nodes_to_merge:
                        continue

                    # Get node data
                    node1_data = graph.graph.nodes[node1_id]
                    node2_data = graph.graph.nodes[node2_id]

                    # Calculate semantic overlap
                    overlap = calculate_semantic_overlap(node1_data, node2_data)

                    # If above threshold, mark for merging
                    if overlap >= merging_threshold:
                        # Choose higher confidence/impact node as target
                        conf1 = sum(node1_data.get("confidence", [0.5])) / len(node1_data.get("confidence", [0.5]))
                        conf2 = sum(node2_data.get("confidence", [0.5])) / len(node2_data.get("confidence", [0.5]))

                        impact1 = node1_data.get("impact_score", 0.5)
                        impact2 = node2_data.get("impact_score", 0.5)

                        score1 = conf1 * impact1
                        score2 = conf2 * impact2

                        if score1 >= score2:
                            nodes_to_merge[node2_id] = node1_id
                        else:
                            nodes_to_merge[node1_id] = node2_id

                        logger.debug(f"Marked nodes {node1_id} and {node2_id} for merging: overlap={overlap}")

        # 3. Execute pruning
        for node_id in nodes_to_prune:
            # Ensure node hasn't been removed as part of another operation
            if node_id in graph.graph:
                graph.graph.remove_node(node_id)
                pruned_nodes += 1

        # 4. Execute merging
        for source_id, target_id in nodes_to_merge.items():
            # Ensure nodes haven't been removed
            if source_id in graph.graph and target_id in graph.graph:
                # Transfer edges from source to target
                # Get all edges connected to the source node
                edges_to_transfer = []

                # Get outgoing edges
                for u, v, data in graph.graph.edges(source_id, data=True):
                    edges_to_transfer.append((u, v, data, 'out'))

                # Get incoming edges
                for u, v, data in graph.graph.in_edges(source_id, data=True):
                    edges_to_transfer.append((u, v, data, 'in'))

                # Transfer the edges
                for u, v, data, direction in edges_to_transfer:
                    if direction == 'out':
                        # Out-edge: Create new edge from target to v
                        graph.graph.add_edge(target_id, v, **data)
                    else:
                        # In-edge: Create new edge from u to target
                        graph.graph.add_edge(u, target_id, **data)

                # Update target node with merged metadata
                source_data = graph.graph.nodes[source_id]
                target_data = graph.graph.nodes[target_id]

                # Merge disciplinary tags
                if "disciplinary_tags" in source_data and "disciplinary_tags" in target_data:
                    target_data["disciplinary_tags"] = list(set(
                        target_data["disciplinary_tags"] + source_data["disciplinary_tags"]
                    ))

                # Merge bias flags
                if "bias_flags" in source_data and "bias_flags" in target_data:
                    target_data["bias_flags"] = target_data["bias_flags"] + source_data["bias_flags"]

                # Add merge note to revision history
                if "revision_history" not in target_data:
                    target_data["revision_history"] = []

                target_data["revision_history"].append({
                    "timestamp": str(datetime.datetime.now()),
                    "action": "merge",
                    "source_node": source_id,
                    "description": f"Merged with node {source_id} (overlap >= {merging_threshold})"
                })

                # Remove source node
                graph.graph.remove_node(source_id)
                merged_nodes += 1

        logger.info(f"Pruning/Merging complete: Pruned {pruned_nodes} nodes, merged {merged_nodes} nodes")

        return {
            "summary": f"Simplified graph by pruning {pruned_nodes} low-confidence nodes and merging {merged_nodes} similar nodes",
            "metrics": {
                "pruned_nodes": pruned_nodes,
                "merged_nodes": merged_nodes,
                "remaining_nodes": graph.graph.number_of_nodes(),
                "remaining_edges": graph.graph.number_of_edges()
            }
        }