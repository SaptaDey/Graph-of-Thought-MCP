import unittest
import uuid
from unittest.mock import patch, MagicMock, call

# Assuming the ASRGoTProcessor is in 'asr_got.core'
# If it's elsewhere, adjust the import path in @patch decorators
from asr_got.core import ASRGoTProcessor
from asr_got.models.graph import ASRGoTGraph

# Mock the stage classes since we are testing the processor, not the stages themselves
# We use MagicMock to simulate the stage classes and their instances
MockInitializationStage = MagicMock(name="InitializationStage")
MockDecompositionStage = MagicMock(name="DecompositionStage")
MockHypothesisStage = MagicMock(name="HypothesisStage")
MockEvidenceStage = MagicMock(name="EvidenceStage")
MockPruningStage = MagicMock(name="PruningStage")
MockSubgraphStage = MagicMock(name="SubgraphStage")
MockCompositionStage = MagicMock(name="CompositionStage")
MockReflectionStage = MagicMock(name="ReflectionStage")

# Patch the stage imports within the 'asr_got.core' module's namespace where ASRGoTProcessor is defined.
# Adjust 'asr_got.core' if the processor class is in a different file.
@patch('asr_got.core.InitializationStage', MockInitializationStage)
@patch('asr_got.core.DecompositionStage', MockDecompositionStage)
@patch('asr_got.core.HypothesisStage', MockHypothesisStage)
@patch('asr_got.core.EvidenceStage', MockEvidenceStage)
@patch('asr_got.core.PruningStage', MockPruningStage)
@patch('asr_got.core.SubgraphStage', MockSubgraphStage)
@patch('asr_got.core.CompositionStage', MockCompositionStage)
@patch('asr_got.core.ReflectionStage', MockReflectionStage)
class TestASRGoTProcessor(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        # Reset mocks before each test to ensure isolation
        self.mock_stage_classes = [
            MockInitializationStage, MockDecompositionStage, MockHypothesisStage,
            MockEvidenceStage, MockPruningStage, MockSubgraphStage,
            MockCompositionStage, MockReflectionStage
        ]
        self.mock_stage_instances = []
        for i, MockStageCls in enumerate(self.mock_stage_classes):
            MockStageCls.reset_mock()
            mock_instance = MockStageCls.return_value
            mock_instance.reset_mock()
            # Configure mock execute to return a basic dict to allow context update
            # This simulates the stage returning some results
            mock_instance.execute.return_value = {
                "summary": f"Stage {i+1} summary",
                "metrics": {f"metric_{i+1}": i+1},
                f"stage_{i+1}_output": f"output_{i+1}"
            }
            # Set the class name correctly for logging/tracing if the processor uses it
            mock_instance.__class__.__name__ = f"MockStage{i+1}"
            self.mock_stage_instances.append(mock_instance)

        # Configure specific return values for stages that processor relies on for final output
        self.mock_stage_instances[6].execute.return_value = { # Composition Stage (index 6)
            "summary": "Composition summary", "metrics": {"comp": 1}, "composition_result": {"final": "data"}
        }
        self.mock_stage_instances[7].execute.return_value = { # Reflection Stage (index 7)
            "summary": "Reflection summary", "metrics": {"reflect": 1}, "final_confidence": [0.95, 0.92, 0.98, 0.90]
        }

        # Instantiate the processor - this will trigger the mocked stage constructors
        self.processor = ASRGoTProcessor()

    def test_initialization(self):
        """Test if the processor initializes correctly and creates stage instances."""
        self.assertEqual(len(self.processor.stages), 8)
        self.assertEqual(self.processor.session_graphs, {})
        # Check if stage constructors were called
        for MockStageCls in self.mock_stage_classes:
            MockStageCls.assert_called_once()

    @patch('asr_got.core.uuid.uuid4')
    @patch('asr_got.core.ASRGoTGraph') # Patch within the core module
    def test_process_query_full_pipeline(self, MockASRGoTGraph, mock_uuid4):
        """Test the full query processing pipeline orchestration."""
        # --- Arrange ---
        # Mock the graph instance and its methods
        mock_graph_instance = MockASRGoTGraph.return_value
        mock_graph_instance.to_dict.return_value = {"nodes": ["mock_node"], "edges": ["mock_edge"]}

        # Mock the session ID generation
        test_uuid = uuid.UUID('abcdef12-3456-7890-abcd-ef1234567890')
        mock_uuid4.return_value = test_uuid
        expected_session_id = str(test_uuid)

        query = "Analyze this audio transcript."
        initial_context = {"user_id": "user123"}
        parameters = {"language": "en-US"}

        # --- Act ---
        result = self.processor.process_query(query, initial_context, parameters)

        # --- Assert ---
        # 1. Session and Graph Creation
        mock_uuid4.assert_called_once()
        MockASRGoTGraph.assert_called_once()
        self.assertIn(expected_session_id, self.processor.session_graphs)
        self.assertEqual(self.processor.session_graphs[expected_session_id], mock_graph_instance)

        # 2. Stage Execution Order and Context Passing
        expected_context = {
            "query": query,
            "context": initial_context,
            "parameters": parameters,
            "session_id": expected_session_id
        }
        execute_calls = []
        for i, mock_stage_instance in enumerate(self.mock_stage_instances):
            # Check call arguments - graph instance and the context *before* this stage ran
            # Note: ANY comparison for context is simpler due to accumulation complexity
            mock_stage_instance.execute.assert_called_once_with(mock_graph_instance, unittest.mock.ANY)

            # Verify context accumulation (check the argument passed to the *next* stage if possible,
            # or check the final context if the processor stores it)
            # For simplicity here, we just check all stages were called.
            # A more rigorous test could capture the context passed to each call.

        # 3. Final Result Structure and Content
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertEqual(result["result"], {"final": "data"}) # From MockCompositionStage

        self.assertIn("reasoning_trace", result)
        self.assertEqual(len(result["reasoning_trace"]), 8)
        self.assertEqual(result["reasoning_trace"][0]["stage"], 1)
        self.assertEqual(result["reasoning_trace"][0]["name"], "MockStage1") # Check mock name
        self.assertEqual(result["reasoning_trace"][7]["stage"], 8)
        self.assertEqual(result["reasoning_trace"][7]["name"], "MockStage8")
        self.assertIn("summary", result["reasoning_trace"][0]) # Check summary presence

        self.assertIn("confidence", result)
        self.assertEqual(result["confidence"], [0.95, 0.92, 0.98, 0.90]) # From MockReflectionStage

        self.assertIn("graph_state", result)
        mock_graph_instance.to_dict.assert_called_once()
        self.assertEqual(result["graph_state"], {"nodes": ["mock_node"], "edges": ["mock_edge"]})

    def test_get_graph_state_success(self):
        """Test retrieving graph state for an existing session."""
        session_id = "existing-session"
        mock_graph = MagicMock(spec=ASRGoTGraph)
        mock_graph.to_dict.return_value = {"nodes": ["n1"], "edges": ["e1"]}
        self.processor.session_graphs[session_id] = mock_graph

        state = self.processor.get_graph_state(session_id)

        self.assertEqual(state, {"nodes": ["n1"], "edges": ["e1"]})
        mock_graph.to_dict.assert_called_once()

    def test_get_graph_state_not_found(self):
        """Test retrieving graph state for a non-existent session raises ValueError."""
        non_existent_session_id = "non-existent-session"
        with self.assertRaisesRegex(ValueError, f"Session {non_existent_session_id} not found"):
            self.processor.get_graph_state(non_existent_session_id)

    def test_incorporate_feedback_node_confidence(self):
        """Test incorporating feedback to update node confidence."""
        session_id = "feedback-session-node"
        mock_graph = MagicMock(spec=ASRGoTGraph)
        self.processor.session_graphs[session_id] = mock_graph

        feedback = {"node_id": "node-123", "type": "confidence", "value": 0.99}
        self.processor.incorporate_feedback(session_id, feedback)

        mock_graph.update_node_confidence.assert_called_once_with("node-123", 0.99)
        mock_graph.update_edge_confidence.assert_not_called() # Ensure only node method was called

    def test_incorporate_feedback_edge_confidence(self):
        """Test incorporating feedback to update edge confidence."""
        session_id = "feedback-session-edge"
        mock_graph = MagicMock(spec=ASRGoTGraph)
        self.processor.session_graphs[session_id] = mock_graph

        feedback = {"edge_id": "edge-abc", "type": "confidence", "value": 0.1}
        self.processor.incorporate_feedback(session_id, feedback)

        mock_graph.update_edge_confidence.assert_called_once_with("edge-abc", 0.1)
        mock_graph.update_node_confidence.assert_not_called() # Ensure only edge method was called

    def test_incorporate_feedback_session_not_found(self):
        """Test incorporating feedback for a non-existent session raises ValueError."""
        non_existent_session_id = "non-existent-feedback-session"
        feedback = {"node_id": "node-123", "type": "confidence", "value": 0.99}
        with self.assertRaisesRegex(ValueError, f"Session {non_existent_session_id} not found"):
            self.processor.incorporate_feedback(non_existent_session_id, feedback)

    def test_incorporate_feedback_invalid_type(self):
        """Test incorporating feedback with an unhandled type (should do nothing gracefully)."""
        session_id = "feedback-session-invalid"
        mock_graph = MagicMock(spec=ASRGoTGraph)
        self.processor.session_graphs[session_id] = mock_graph

        feedback = {"node_id": "node-123", "type": "unknown_action", "value": "test"}
        # Expect no error and no graph methods called
        self.processor.incorporate_feedback(session_id, feedback)
        mock_graph.update_node_confidence.assert_not_called()
        mock_graph.update_edge_confidence.assert_not_called()

if __name__ == '__main__':
    unittest.main()