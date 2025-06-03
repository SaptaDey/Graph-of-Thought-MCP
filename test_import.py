import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath("src"))

from asr_got.models.graph import ASRGoTGraph

print("Import successful!")
graph = ASRGoTGraph()
print("Graph initialized successfully!")