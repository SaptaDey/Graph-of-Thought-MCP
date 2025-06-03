import logging
import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
import json
import datetime

from asr_got.models.node import Node
from asr_got.models.edge import Edge
from asr_got.models.hyperedge import Hyperedge

logger = logging.getLogger("asr-got-graph")

class ASRGoTGraph:
    """
    Core graph data structure for ASR-GoT.
    Implements the mathematical formalism from P1.11.
    """

    def __init__(self):
        # Initialize the main graph structure
        """
        Initializes an empty ASR-GoT graph with structures for nodes, edges, hyperedges, layers, and interdisciplinary bridge nodes.
        """
        self.graph = nx.DiGraph()

        # Separate structure for hyperedges
        self.hyperedges = {}

        # Layer structure (P1.23)
        self.layers = {}

        # Tracking for Interdisciplinary Bridge Nodes (P1.8)
        self.ibns = set()

        logger.info("ASR-GoT Graph initialized")

    def add_node(self, node: Node) -> None:
        """
        Adds a node to the graph, including all associated metadata.
        
        If the node specifies a `layer_id` in its metadata, the node is also tracked within the corresponding layer.
        """
        node_data = node.to_dict()

        # Add to the graph
        self.graph.add_node(node.node_id, **node_data)

        # Track in layers if layer_id is specified
        if node.metadata.get("layer_id"):
            layer_id = node.metadata["layer_id"]
            if layer_id not in self.layers:
                self.layers[layer_id] = set()
            self.layers[layer_id].add(node.node_id)

        logger.debug(f"Added node {node.node_id} to graph")

    def add_edge(self, edge: Edge) -> None:
        """
        Adds a typed edge between two nodes in the graph with associated metadata.
        """
        edge_data = edge.to_dict()

        # Add to the graph
        self.graph.add_edge(edge.source, edge.target, key=edge.edge_id, **edge_data)

        logger.debug(f"Added edge {edge.edge_id} to graph")

    def add_hyperedge(self, hyperedge: Hyperedge) -> None:
        """
        Adds a hyperedge connecting multiple nodes and creates virtual bidirectional edges between all node pairs for visualization and algorithmic purposes.
        
        The hyperedge is stored in the internal hyperedges dictionary, and each pair of nodes in the hyperedge is connected by virtual edges marked as part of the hyperedge.
        """
        # Store the hyperedge
        self.hyperedges[hyperedge.edge_id] = hyperedge

        # For visualization and some algorithms, add a clique of regular edges
        for i, source in enumerate(hyperedge.nodes):
            for target in hyperedge.nodes[i+1:]:
                # Create a virtual edge ID
                virtual_edge_id = f"{hyperedge.edge_id}_virtual_{source}_{target}"

                # Add a bidirectional edge for the hyperedge
                self.graph.add_edge(
                    source,
                    target,
                    key=virtual_edge_id,
                    edge_id=virtual_edge_id,
                    edge_type="hyperedge_virtual",
                    hyperedge_id=hyperedge.edge_id,
                    confidence=hyperedge.confidence,
                    is_virtual=True
                )

                self.graph.add_edge(
                    target,
                    source,
                    key=virtual_edge_id + "_rev",
                    edge_id=virtual_edge_id + "_rev",
                    edge_type="hyperedge_virtual",
                    hyperedge_id=hyperedge.edge_id,
                    confidence=hyperedge.confidence,
                    is_virtual=True
                )

        logger.debug(f"Added hyperedge {hyperedge.edge_id} connecting {len(hyperedge.nodes)} nodes")

    def create_interdisciplinary_bridge(self, source_node_id: str, target_node_id: str) -> str:
        """
        Creates an Interdisciplinary Bridge Node (IBN) connecting two nodes from different disciplines.
        
        If the source and target nodes have no overlapping disciplinary tags, a new IBN node is created with combined disciplinary metadata and initial confidence values. The IBN is added to the graph, and edges are created from the source node to the IBN and from the IBN to the target node. The IBN is tracked for future reference.
        
        Args:
            source_node_id: The ID of the source node.
            target_node_id: The ID of the target node.
        
        Returns:
            The ID of the created IBN node, or None if the source and target nodes share disciplines.
        
        Raises:
            ValueError: If either the source or target node does not exist in the graph.
        """
        if source_node_id not in self.graph or target_node_id not in self.graph:
            raise ValueError("Both source and target nodes must exist in the graph")

        # Get the disciplines from both nodes
        source_tags = set(self.graph.nodes[source_node_id].get("disciplinary_tags", []))
        target_tags = set(self.graph.nodes[target_node_id].get("disciplinary_tags", []))

        # Proceed only if there's no overlap in disciplines
        if source_tags.intersection(target_tags):
            logger.debug(f"Not creating IBN: nodes share disciplines {source_tags.intersection(target_tags)}")
            return None

        # Create a new IBN
        ibn_id = f"ibn_{source_node_id}_{target_node_id}"

        # Create a new node with combined disciplines
        ibn_node = Node(
            node_id=ibn_id,
            label=f"IBN: {self.graph.nodes[source_node_id].get('label', 'Unknown')} <-> {self.graph.nodes[target_node_id].get('label', 'Unknown')}",
            node_type="interdisciplinary_bridge",
            confidence=[0.6, 0.6, 0.6, 0.6],  # Initial confidence for IBN
            metadata={
                "disciplinary_tags": list(source_tags.union(target_tags)),
                "source_disciplines": list(source_tags),
                "target_disciplines": list(target_tags),
                "provenance": "Interdisciplinary bridge creation (P1.8)",
                "creation_timestamp": str(datetime.datetime.now())
            }
        )

        # Add the IBN to the graph
        self.add_node(ibn_node)

        # Connect the IBN to source and target nodes
        source_edge = Edge(
            edge_id=f"{ibn_id}_source",
            source=source_node_id,
            target=ibn_id,
            edge_type="ibn_source",
            confidence=0.8,
            metadata={"provenance": "IBN connection"}
        )

        target_edge = Edge(
            edge_id=f"{ibn_id}_target",
            source=ibn_id,
            target=target_node_id,
            edge_type="ibn_target",
            confidence=0.8,
            metadata={"provenance": "IBN connection"}
        )

        self.add_edge(source_edge)
        self.add_edge(target_edge)

        # Track this IBN
        self.ibns.add(ibn_id)

        logger.info(f"Created Interdisciplinary Bridge Node {ibn_id} connecting disciplines {source_tags} and {target_tags}")
        return ibn_id

    def update_node_confidence(self, node_id: str, new_confidence: List[float]) -> None:
        """
        Updates the confidence vector of the specified node.
        
        Raises:
            ValueError: If the node with the given ID does not exist in the graph.
        """
        if node_id not in self.graph:
            raise ValueError(f"Node {node_id} not found in graph")

        self.graph.nodes[node_id]["confidence"] = new_confidence
        logger.debug(f"Updated confidence for node {node_id}: {new_confidence}")

    def update_edge_confidence(self, edge_id: str, new_confidence: float) -> None:
        """
        Updates the confidence value of an edge or hyperedge identified by its edge ID.
        
        Raises:
            ValueError: If the specified edge or hyperedge does not exist in the graph.
        """
        # Find the edge
        for u, v, data in self.graph.edges(data=True):
            if data.get("edge_id") == edge_id:
                data["confidence"] = new_confidence
                logger.debug(f"Updated confidence for edge {edge_id}: {new_confidence}")
                return

        # Check hyperedges
        if edge_id in self.hyperedges:
            self.hyperedges[edge_id].confidence = new_confidence
            logger.debug(f"Updated confidence for hyperedge {edge_id}: {new_confidence}")
            return

        raise ValueError(f"Edge {edge_id} not found in graph")

    def calculate_topology_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Computes and stores topology metrics for all nodes in the graph.
        
        Calculates degree centrality, betweenness centrality, closeness centrality, and clustering coefficient for each node. The computed metrics are added to each node's metadata and returned as a dictionary keyed by node ID.
        
        Returns:
            A dictionary mapping node IDs to their topology metrics.
        """
        topology_metrics = {}

        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        closeness_centrality = nx.closeness_centrality(self.graph)

        # Calculate clustering coefficient
        clustering = nx.clustering(self.graph.to_undirected())

        # Store metrics for each node
        for node_id in self.graph.nodes:
            topology_metrics[node_id] = {
                "degree_centrality": degree_centrality.get(node_id, 0),
                "betweenness_centrality": betweenness_centrality.get(node_id, 0),
                "closeness_centrality": closeness_centrality.get(node_id, 0),
                "clustering_coefficient": clustering.get(node_id, 0)
            }

            # Update node metadata with topology metrics
            self.graph.nodes[node_id]["topology_metrics"] = topology_metrics[node_id]

        logger.info(f"Calculated topology metrics for {len(topology_metrics)} nodes")
        return topology_metrics

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the entire ASR-GoT graph structure into a dictionary suitable for serialization.
        
        The output includes lists of nodes, edges (excluding virtual edges from hyperedges), hyperedges, layers, and summary metadata such as counts of nodes, edges, hyperedges, layers, and interdisciplinary bridge nodes (IBNs).
         
        Returns:
            A dictionary representation of the graph, including nodes, edges, hyperedges, layers, and metadata.
        """
        # Convert nodes
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "node_id": node_id,
                "label": data.get("label", ""),
                "type": data.get("node_type", ""),
                "confidence": data.get("confidence", []),
                "metadata": {k: v for k, v in data.items() if k not in ["node_id", "label", "node_type", "confidence"]}
            })

        # Convert edges
        edges = []
        for u, v, data in self.graph.edges(data=True):
            if not data.get("is_virtual", False):  # Skip virtual edges from hyperedges
                edge_id = data.get("edge_id", f"{u}-{v}")
                edges.append({
                    "edge_id": edge_id,
                    "source": u,
                    "target": v,
                    "edge_type": data.get("edge_type", ""),
                    "confidence": data.get("confidence", 0.0),
                    "metadata": {key: val for key, val in data.items()
                                if key not in ["edge_id", "source", "target", "edge_type", "confidence", "is_virtual"]}
                })

        # Convert hyperedges
        hyperedges = []
        for edge_id, hyperedge in self.hyperedges.items():
            hyperedges.append({
                "edge_id": edge_id,
                "nodes": hyperedge.nodes,
                "confidence": hyperedge.confidence,
                "metadata": hyperedge.metadata
            })

        # Convert layers
        layers_dict = {layer_id: list(nodes) for layer_id, nodes in self.layers.items()}

        return {
            "nodes": nodes,
            "edges": edges,
            "hyperedges": hyperedges,
            "layers": layers_dict,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "hyperedge_count": len(hyperedges),
                "layer_count": len(layers_dict),
                "ibn_count": len(self.ibns)
            }
        }