import logging
import uuid
from typing import Dict, Any, List, Optional

from .stages.stage_1_initialization import InitializationStage
from .stages.stage_2_decomposition import DecompositionStage
from .stages.stage_3_hypothesis import HypothesisStage
from .stages.stage_4_evidence import EvidenceStage
from .stages.stage_5_pruning import PruningStage
from .stages.stage_6_subgraph import SubgraphStage
from .stages.stage_7_composition import CompositionStage
from .stages.stage_8_reflection import ReflectionStage
from .models.graph import ASRGoTGraph

logger = logging.getLogger("asr-got-core")

class ASRGoTProcessor:
    """
    Main processor implementing the ASR-GoT 8-stage reasoning pipeline.
    """
    
    def __init__(self):
        self.session_graphs = {}
        
        # Initialize the stages
        self.stages = [
            InitializationStage(),
            DecompositionStage(),
            HypothesisStage(),
            EvidenceStage(),
            PruningStage(),
            SubgraphStage(),
            CompositionStage(),
            ReflectionStage()
        ]
        
        logger.info("ASR-GoT Processor initialized with 8 stages")
    
    def process_query(self, query: str, context: Dict[str, Any] = None, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query through the full 8-stage ASR-GoT pipeline.
        """
        logger.info(f"Processing query: {query[:50]}...")
        
        # Create a new session ID
        session_id = str(uuid.uuid4())
        
        # Initialize context and parameters if not provided
        context = context or {}
        parameters = parameters or {}
        
        # Create a new graph for this session
        graph = ASRGoTGraph()
        self.session_graphs[session_id] = graph
        
        # Initialize reasoning trace
        reasoning_trace = []
        
        # Execute each stage sequentially
        stage_context = {
            "query": query,
            "context": context,
            "parameters": parameters,
            "session_id": session_id
        }
        
        for i, stage in enumerate(self.stages):
            logger.info(f"Executing Stage {i+1}: {stage.__class__.__name__}")
            
            # Execute the stage
            result = stage.execute(graph, stage_context)
            
            # Append to reasoning trace
            reasoning_trace.append({
                "stage": i+1,
                "name": stage.__class__.__name__,
                "summary": result.get("summary", ""),
                "metrics": result.get("metrics", {})
            })
            
            # Update context with stage results
            stage_context.update(result)
        
        # Final result from the composition and reflection stages
        final_confidence = stage_context.get("final_confidence") # Get confidence from reflection stage
        if final_confidence is None:
            logger.warning("Final confidence not found in stage context after Reflection stage. Defaulting.")
            # Provide a more neutral or indicative default, e.g., average confidence or None
            final_confidence = [0.5, 0.5, 0.5, 0.5] 
            # Alternatively, could be set to None if the consumer handles it:
            # final_confidence = None 

        final_result = {
            "result": stage_context.get("composition_result", {}),
            "reasoning_trace": reasoning_trace,
            "confidence": final_confidence, # Use the retrieved or default value
            "graph_state": self.get_graph_state(session_id)
        }
        
        logger.info(f"Query processing completed for session {session_id}")
        return final_result
    
    def get_graph_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current state of the graph for a session.
        """
        if session_id not in self.session_graphs:
            raise ValueError(f"Session {session_id} not found")
        
        graph = self.session_graphs[session_id]
        return graph.to_dict()
    
    def incorporate_feedback(self, session_id: str, feedback: Dict[str, Any]) -> None:
        """
        Incorporate user feedback to refine the graph.
        """
        if session_id not in self.session_graphs:
            raise ValueError(f"Session {session_id} not found")
        
        graph = self.session_graphs[session_id]
        
        # Apply feedback to the graph
        # This might involve updating node confidences, adding/removing nodes, etc.
        node_id = feedback.get("node_id")
        edge_id = feedback.get("edge_id")
        feedback_type = feedback.get("type")
        feedback_value = feedback.get("value")
        
        if node_id and feedback_type == "confidence":
            graph.update_node_confidence(node_id, feedback_value)
        elif edge_id and feedback_type == "confidence":
            graph.update_edge_confidence(edge_id, feedback_value)
        
        logger.info(f"Feedback incorporated for session {session_id}")