# src/asr_got/__init__.py
"""
ASR-GoT: Advanced Scientific Reasoning Graph-of-Thoughts

This package implements the ASR-GoT framework for advanced scientific reasoning
using a graph-based approach with multi-dimensional confidence assessment,
interdisciplinary connections, and structured thinking.

The framework follows an 8-stage process:
1. Initialization
2. Decomposition
3. Hypothesis/Planning
4. Evidence Integration
5. Pruning/Merging
6. Subgraph Extraction
7. Composition
8. Reflection
"""

from src.asr_got.core import ASRGoTProcessor
from src.asr_got.models import Node, Edge, Hyperedge, ASRGoTGraph