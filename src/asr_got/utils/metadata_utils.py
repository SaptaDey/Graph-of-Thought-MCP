import datetime
import hashlib
import json
from typing import Dict, Any, List, Optional, Set

def generate_id(prefix: str, content: str) -> str:
    """
    Generates a deterministic identifier by hashing the content and prefixing it.
    
    The function computes an MD5 hash of the input content, truncates it to 8 characters, and combines it with the specified prefix to form the ID.
    
    Args:
        prefix: String to prepend to the generated ID.
        content: Content to be hashed for ID generation.
    
    Returns:
        A string representing the generated identifier.
    """
    hash_object = hashlib.md5(content.encode())
    hash_hex = hash_object.hexdigest()[:8]
    return f"{prefix}_{hash_hex}"

def calculate_semantic_overlap(metadata1: Dict[str, Any], metadata2: Dict[str, Any],
                              keys_to_compare: Optional[List[str]] = None) -> float:
    """
                              Computes a semantic overlap score between two metadata dictionaries.
                              
                              The function compares values for each specified key (or all common keys, excluding IDs and timestamps, if none are specified) using type-appropriate similarity measures: Jaccard similarity for lists of hashable items, a Jaccard-like approach for lists with non-hashable items, relative proximity for numeric values, and equality checks for strings and other types. Returns the average overlap score across all compared keys, ranging from 0 (no overlap) to 1 (identical).
                               
                              Args:
                                  metadata1: First metadata dictionary to compare.
                                  metadata2: Second metadata dictionary to compare.
                                  keys_to_compare: Optional list of metadata keys to use for comparison. If not provided, all common keys except IDs and timestamps are used.
                              
                              Returns:
                                  A float representing the average semantic overlap score between the two metadata dictionaries, from 0 to 1.
                              """
    if not keys_to_compare:
        # Use all common keys except for IDs, timestamps, etc.
        exclusions = {'node_id', 'edge_id', 'timestamp', 'revision_history'}
        all_keys = set(metadata1.keys()).union(set(metadata2.keys()))
        keys_to_compare = list(all_keys - exclusions)

    if not keys_to_compare:
        return 0.0

    # Calculate overlap for each key
    overlaps = []
    for key in keys_to_compare:
        if key in metadata1 and key in metadata2:
            val1 = metadata1[key]
            val2 = metadata2[key]

            if isinstance(val1, list) and isinstance(val2, list):
                # For lists (e.g., tags), calculate Jaccard similarity
                try:
                    # Try to create sets (works for hashable items like strings, numbers)
                    set1 = set(val1)
                    set2 = set(val2)
                    if not set1 and not set2:
                        overlaps.append(1.0)  # Both empty = full overlap
                    elif not set1 or not set2:
                        overlaps.append(0.0)  # One empty = no overlap
                    else:
                        overlaps.append(len(set1.intersection(set2)) / len(set1.union(set2)))
                except TypeError:
                    # Handle lists with non-hashable items (like dicts)
                    # Use simple equality comparison for each item
                    common_items = 0
                    total_items = len(val1) + len(val2)

                    for item1 in val1:
                        if item1 in val2:
                            common_items += 1

                    if total_items == 0:
                        overlaps.append(1.0)  # Both empty = full overlap
                    else:
                        # Jaccard-like similarity for non-hashable items
                        overlaps.append((2 * common_items) / total_items)

            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # For numeric values, calculate proximity
                max_val = max(abs(val1), abs(val2))
                if max_val == 0:
                    overlaps.append(1.0)  # Both zero = full overlap
                else:
                    diff = abs(val1 - val2) / max_val
                    overlaps.append(max(0, 1 - diff))

            elif isinstance(val1, str) and isinstance(val2, str):
                # For strings, use simple equality check
                # Could be enhanced with NLP similarity metrics
                if val1 == val2:
                    overlaps.append(1.0)
                else:
                    overlaps.append(0.0)

            else:
                # For other types, use simple equality check
                if val1 == val2:
                    overlaps.append(1.0)
                else:
                    overlaps.append(0.0)

    # Return average overlap
    if overlaps:
        return sum(overlaps) / len(overlaps)
    return 0.0

def check_falsifiability(criteria: str) -> float:
    """
    Evaluates how well-defined a falsifiability criterion string is.
    
    Returns a score between 0 and 1 based on the presence of testability-related keywords and the length of the input string. This is a simplified assessment and does not perform deep linguistic analysis.
    """
    if not criteria:
        return 0.0

    # This is a simplified placeholder implementation
    # A real implementation would analyze the criteria more thoroughly

    # Check for key phrases that indicate testability
    testability_phrases = ['experiment', 'measurement', 'observation', 'predict',
                           'test', 'quantify', 'threshold', 'statistical',
                           'validate', 'verify', 'contradict']

    score = 0.0
    for phrase in testability_phrases:
        if phrase in criteria.lower():
            score += 0.1

    # Check length - longer criteria tend to be more specific
    if len(criteria) > 100:
        score += 0.2
    elif len(criteria) > 50:
        score += 0.1

    # Cap the score at 1.0
    return min(score, 1.0)

def detect_biases(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyzes metadata to identify potential biases and returns a list of detected bias descriptions.
    
    Checks for confirmation bias based on high average confidence values and for recency bias if historical sources are referenced. Returns a list of bias objects, each containing type, description, and severity.
    """
    biases = []

    # This is a simplified placeholder implementation
    # A real implementation would be much more sophisticated

    # Check for confirmation bias (overly high confidence)
    confidence = metadata.get('confidence', [])
    if isinstance(confidence, list) and confidence:
        avg_confidence = sum(confidence) / len(confidence)
        if avg_confidence > 0.9:
            biases.append({
                'type': 'confirmation_bias',
                'description': 'Unusually high confidence values may indicate confirmation bias',
                'severity': 'medium'
            })

    # Check for recency bias
    timestamp = metadata.get('timestamp', '')
    referenced_sources = metadata.get('provenance', '')
    if timestamp and 'historical' in referenced_sources.lower():
        # This is a simplistic check - would need to compare timestamps of evidence
        biases.append({
            'type': 'recency_bias',
            'description': 'Historical sources should be evaluated in their proper context',
            'severity': 'low'
        })

    # Many other bias types would be checked in a real implementation

    return biases