import math
import numpy as np
from typing import List, Dict, Any
import datetime

def bayesian_update(prior_confidence: List[float], evidence_confidence: List[float], 
                   statistical_power: float, edge_type: str) -> List[float]:
    """
    Update confidence vector using Bayesian methods (P1.14).
    
    Args:
        prior_confidence: Current confidence vector [empirical, theoretical, methodological, consensus]
        evidence_confidence: Evidence confidence vector
        statistical_power: Statistical power of the evidence (0-1)
        edge_type: Type of relationship between evidence and hypothesis
    
    Returns:
        Updated confidence vector
    """
    # Adjust update strength based on edge type
    edge_type_weights = {
        "supportive": 1.0,
        "causal": 1.2,      # Causal connections have stronger impact
        "correlative": 0.6,  # Correlative connections have weaker impact
        "contradictory": -0.8 # Contradictory evidence reduces confidence
    }
    
    weight = edge_type_weights.get(edge_type, 0.5) * statistical_power
    
    # Apply weighted update to each dimension of confidence
    updated_confidence = []
    for i, (prior, evid) in enumerate(zip(prior_confidence, evidence_confidence)):
        # Simple weighted average (could be replaced with actual Bayesian update)
        update = prior + weight * (evid - prior)
        # Ensure values stay in [0, 1] range
        update = max(0.0, min(1.0, update))
        updated_confidence.append(update)
    
    return updated_confidence

def calculate_entropy(distribution: List[float]) -> float:
    """
    Calculate entropy of a probability distribution (P1.27).
    
    Args:
        distribution: List of probability values that sum to 1
    
    Returns:
        Entropy value
    """
    # Normalize if not already a proper distribution
    total = sum(distribution)
    if total == 0:
        return 0
    
    normalized = [p / total for p in distribution]
    
    # Calculate entropy: -sum(p_i * log(p_i))
    entropy = 0
    for p in normalized:
        if p > 0:  # Avoid log(0)
            entropy -= p * math.log2(p)
    
    return entropy

def calculate_kl_divergence(p: List[float], q: List[float]) -> float:
    """
    Calculate KL divergence between two distributions (P1.27).
    
    Args:
        p: First distribution
        q: Second distribution (reference)
    
    Returns:
        KL divergence value
    """
    # Normalize
    p_sum = sum(p)
    q_sum = sum(q)
    
    if p_sum == 0 or q_sum == 0:
        return float('inf')
    
    p_norm = [p_i / p_sum for p_i in p]
    q_norm = [q_i / q_sum for q_i in q]
    
    # Calculate KL divergence: sum(p_i * log(p_i / q_i))
    kl_div = 0
    for p_i, q_i in zip(p_norm, q_norm):
        if p_i > 0 and q_i > 0:  # Avoid division by zero
            kl_div += p_i * math.log2(p_i / q_i)
    
    return kl_div

def calculate_info_gain(graph, node_id: str, evidence_result: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate information gain metrics for a node (P1.27).
    
    Args:
        graph: The ASR-GoT graph
        node_id: ID of the node to calculate metrics for
        evidence_result: Evidence integration results
    
    Returns:
        Dictionary of information-theoretic metrics
    """
    # Check if node exists
    if node_id not in graph.graph:
        return {}
    
    # Get node confidence
    node = graph.graph.nodes[node_id]
    confidence = node.get("confidence", [0.5, 0.5, 0.5, 0.5])
    
    # Calculate entropy of the confidence distribution
    entropy = calculate_entropy(confidence)
    
    # Calculate relative confidence change
    old_confidence = node.get("old_confidence", [0.5, 0.5, 0.5, 0.5])
    kl_div = calculate_kl_divergence(confidence, old_confidence)
    
    # Simplified minimum description length
    mdl_complexity = len(list(graph.graph.neighbors(node_id))) * 0.1
    
    return {
        "entropy": entropy,
        "kl_divergence": kl_div,
        "mdl_complexity": mdl_complexity,
        "timestamp": str(datetime.datetime.now())
    }