import logging
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Set, Tuple
import json
import io
import base64

from src.asr_got.models.graph import ASRGoTGraph

logger = logging.getLogger("asr-got-graph-utils")

def detect_communities(graph: ASRGoTGraph) -> Dict[str, int]:
    """
    Detect communities in the graph using Louvain algorithm.
    
    Args:
        graph: ASRGoTGraph instance
    
    Returns:
        Dictionary mapping node IDs to community numbers
    """
    # Convert to undirected graph for community detection
    undirected = graph.graph.to_undirected()
    
    # Run community detection
    try:
        import community as community_louvain
        communities = community_louvain.best_partition(undirected)
        return communities
    except ImportError:
        logger.warning("python-louvain package not found, using connected components instead")
        communities = {}
        for i, component in enumerate(nx.connected_components(undirected)):
            for node in component:
                communities[node] = i
        return communities

def calculate_path_centrality(graph: ASRGoTGraph, source_types: List[str], target_types: List[str]) -> Dict[str, float]:
    """
    Calculate path centrality for nodes that connect source_types to target_types.
    
    Args:
        graph: ASRGoTGraph instance
        source_types: List of node types to consider as sources
        target_types: List of node types to consider as targets
    
    Returns:
        Dictionary mapping node IDs to path centrality scores
    """
    # Find source and target nodes
    sources = [n for n, d in graph.graph.nodes(data=True) if d.get("node_type") in source_types]
    targets = [n for n, d in graph.graph.nodes(data=True) if d.get("node_type") in target_types]
    
    # Calculate all shortest paths
    path_counts = {node: 0 for node in graph.graph.nodes()}
    
    for source in sources:
        for target in targets:
            try:
                paths = list(nx.shortest_simple_paths(graph.graph, source, target))
                # Count top 3 shortest paths
                for i, path in enumerate(paths[:3]):
                    for node in path:
                        path_counts[node] += 1.0 / (i + 1)  # Weight by path rank
            except nx.NetworkXNoPath:
                continue
    
    # Normalize
    if path_counts:
        max_count = max(path_counts.values())
        if max_count > 0:
            path_centrality = {node: count / max_count for node, count in path_counts.items()}
        else:
            path_centrality = path_counts
    else:
        path_centrality = path_counts
    
    return path_centrality

def visualize_graph(graph: ASRGoTGraph, 
                    highlight_nodes: Optional[List[str]] = None, 
                    community_colors: bool = True) -> str:
    """
    Create a visualization of the graph and return it as a base64 encoded string.
    
    Args:
        graph: ASRGoTGraph instance
        highlight_nodes: List of node IDs to highlight
        community_colors: Whether to color nodes by community
    
    Returns:
        Base64 encoded PNG image of the graph
    """
    plt.figure(figsize=(12, 8))
    
    # Get the networkx graph
    G = graph.graph
    
    # Determine node colors
    node_colors = []
    if community_colors:
        communities = detect_communities(graph)
        color_map = plt.cm.get_cmap('tab20', max(communities.values()) + 1)
        node_colors = [color_map(communities.get(node, 0)) for node in G.nodes()]
    else:
        # Color by node type
        type_colors = {
            'root': 'red',
            'dimension': 'blue',
            'hypothesis': 'green',
            'evidence': 'orange',
            'interdisciplinary_bridge': 'purple',
            'placeholder_gap': 'gray'
        }
        node_colors = [type_colors.get(G.nodes[node].get('node_type', ''), 'black') for node in G.nodes()]
    
    # Determine node sizes based on confidence
    node_sizes = []
    for node in G.nodes():
        confidence = G.nodes[node].get('confidence', [0.5])
        if isinstance(confidence, list):
            avg_confidence = sum(confidence) / len(confidence)
        else:
            avg_confidence = confidence
        node_sizes.append(100 + 500 * avg_confidence)
    
    # Determine edge colors based on edge type
    edge_colors = []
    for u, v, data in G.edges(data=True):
        edge_type = data.get('edge_type', '')
        if 'causal' in edge_type:
            edge_colors.append('red')
        elif 'temporal' in edge_type:
            edge_colors.append('blue')
        elif 'supportive' in edge_type:
            edge_colors.append('green')
        elif 'contradictory' in edge_type:
            edge_colors.append('orange')
        else:
            edge_colors.append('gray')
    
    # Create the layout
    if G.number_of_nodes() < 50:
        pos = nx.spring_layout(G, k=0.3, iterations=50)
    else:
        pos = nx.kamada_kawai_layout(G)
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)
    
    # Highlight specific nodes if requested
    if highlight_nodes:
        highlight_nodes_set = set(highlight_nodes).intersection(set(G.nodes()))  # Only existing nodes
        if highlight_nodes_set:
            nx.draw_networkx_nodes(G, pos, 
                                nodelist=list(highlight_nodes_set),
                                node_color='yellow', 
                                node_size=[node_sizes[list(G.nodes()).index(n)] * 1.2 for n in highlight_nodes_set],
                                alpha=1.0)
    
    # Draw edges and labels
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, alpha=0.6, arrows=True)
    
    # Draw labels only for important nodes
    important_nodes = [n for n, d in G.nodes(data=True) 
                    if d.get('node_type') in ['root', 'dimension', 'hypothesis'] 
                    or n in (highlight_nodes or [])]
    
    labels = {n: G.nodes[n].get('label', n) for n in important_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    
    # Remove axis
    plt.axis('off')
    
    # Save to a byte buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Encode as base64
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return img_str