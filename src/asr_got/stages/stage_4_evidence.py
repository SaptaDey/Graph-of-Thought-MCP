import logging
import random
from typing import Dict, Any, List, Tuple, Set
import datetime

from asr_got.models.graph import ASRGoTGraph
from asr_got.models.node import Node
from asr_got.models.edge import Edge
from asr_got.models.hyperedge import Hyperedge
from asr_got.utils.math_utils import bayesian_update, calculate_info_gain

logger = logging.getLogger("asr-got-stage4")

class EvidenceStage:
    """
    Stage 4: Evidence Integration

    Manages the iterative process of selecting hypotheses, gathering/analyzing evidence,
    and updating the graph structure and confidence values.
    """

    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrates evidence into the hypothesis graph, updating confidence and graph structure.
        
        This method iteratively selects hypotheses, generates and adds evidence nodes, creates and types edges, updates hypothesis confidence, and adapts the graph by adding interdisciplinary bridge nodes and hyperedges as needed. It also applies placeholder logic for temporal decay, pattern detection, topology adaptation, and bias detection. Returns a summary of the integration process and key metrics.
         
        Args:
            graph: The hypothesis graph to update.
            context: Dictionary containing hypotheses, parameters, and other stage context.
        
        Returns:
            A dictionary summarizing the evidence integration process and reporting metrics such as the number of evidence nodes, interdisciplinary bridge nodes, hyperedges created, and confidence updates performed.
        """
        logger.info("Executing Evidence Integration Stage")

        # Extract hypotheses generated in Stage 3
        hypotheses = context.get("hypotheses", [])
        if not hypotheses:
            logger.warning("No hypotheses found from Stage 3")
            return {
                "summary": "Evidence integration skipped: No hypotheses available",
                "metrics": {}
            }

        # Parameters for evidence integration
        parameters = context.get("parameters", {})
        max_iterations = parameters.get("evidence_max_iterations", 5)

        # Track metrics
        evidence_nodes_created = 0
        ibns_created = 0
        hyperedges_created = 0
        confidence_updates = 0

        # Execute the adaptive evidence integration loop (P1.4)
        for iteration in range(max_iterations):
            logger.info(f"Evidence integration iteration {iteration+1}/{max_iterations}")

            # Select the next hypothesis to evaluate based on confidence and impact (P1.5, P1.28)
            h_star, h_star_id = self._select_next_hypothesis(graph, hypotheses, parameters)
            if not h_star:
                logger.info("No more hypotheses to evaluate")
                break

            # Execute the plan associated with the hypothesis
            evidence_result = self._execute_plan(graph, h_star, parameters)

            # Create evidence nodes
            for e_data in evidence_result.get("evidence", []):
                evidence_node = self._create_evidence_node(e_data, h_star_id)
                graph.add_node(evidence_node)

                # Connect evidence to hypothesis with typed edge (P1.10, P1.24, P1.25)
                edge_type = self._determine_edge_type(evidence_node, h_star)

                edge = Edge(
                    edge_id=f"e_{evidence_node.node_id}_{h_star_id}",
                    source=evidence_node.node_id,
                    target=h_star_id,
                    edge_type=edge_type["type"],
                    confidence=evidence_node.confidence[0],  # Use empirical support as edge confidence
                    metadata={
                        "edge_subtype": edge_type.get("subtype", ""),
                        "causal_metadata": edge_type.get("causal_metadata", {}),
                        "temporal_metadata": edge_type.get("temporal_metadata", {})
                    }
                )

                graph.add_edge(edge)
                evidence_nodes_created += 1

                # Update hypothesis confidence using Bayesian methods (P1.14)
                old_confidence = h_star["confidence"]
                new_confidence = bayesian_update(
                    old_confidence,
                    evidence_node.confidence,
                    evidence_node.metadata.get("statistical_power", 0.5),
                    edge_type["type"]
                )

                graph.update_node_confidence(h_star_id, new_confidence)
                confidence_updates += 1

                # Check for interdisciplinary bridge opportunities (P1.8)
                if self._should_create_ibn(evidence_node, h_star):
                    ibn_id = graph.create_interdisciplinary_bridge(evidence_node.node_id, h_star_id)
                    if ibn_id:
                        ibns_created += 1

            # Check for hyperedge opportunities (P1.9)
            potential_hyperedges = self._identify_potential_hyperedges(graph, evidence_result.get("evidence", []), h_star_id)
            for h_edge_data in potential_hyperedges:
                hyperedge = Hyperedge(
                    edge_id=f"hyper_{h_star_id}_{len(graph.hyperedges)}",
                    nodes=h_edge_data["nodes"],
                    confidence=h_edge_data["confidence"],
                    metadata=h_edge_data["metadata"]
                )

                graph.add_hyperedge(hyperedge)
                hyperedges_created += 1

            # Apply temporal decay to older evidence (P1.18)
            self._apply_temporal_decay(graph)

            # Detect and encode temporal patterns (P1.25)
            temporal_patterns = self._detect_temporal_patterns(graph, h_star_id)
            for pattern in temporal_patterns:
                # Update edge metadata with temporal pattern info
                edge_id = pattern["edge_id"]
                temporal_metadata = pattern["temporal_metadata"]

                # Find and update the edge
                for u, v, data in graph.graph.edges(data=True):
                    if data.get("edge_id") == edge_id:
                        if "temporal_metadata" not in data:
                            data["temporal_metadata"] = {}

                        data["temporal_metadata"].update(temporal_metadata)

            # Dynamically adapt graph topology (P1.22)
            self._adapt_topology(graph, h_star_id)

            # Check for biases (P1.17)
            bias_flags = self._detect_biases(graph, h_star_id, evidence_result)
            for bias in bias_flags:
                # Update node with bias flag
                if bias["node_id"] in graph.graph:
                    if "bias_flags" not in graph.graph.nodes[bias["node_id"]]:
                        graph.graph.nodes[bias["node_id"]]["bias_flags"] = []

                    graph.graph.nodes[bias["node_id"]]["bias_flags"].append(bias["flag"])

            # Update information metrics (P1.27)
            info_metrics = calculate_info_gain(graph, h_star_id, evidence_result)
            if h_star_id in graph.graph:
                graph.graph.nodes[h_star_id]["info_metrics"] = info_metrics

        # Calculate final topology metrics
        graph.calculate_topology_metrics()

        logger.info(f"Evidence integration complete: {evidence_nodes_created} evidence nodes, {ibns_created} IBNs, {hyperedges_created} hyperedges")

        return {
            "summary": f"Integrated evidence nodes into the graph, updating hypothesis confidence and structure",
            "metrics": {
                "evidence_nodes_created": evidence_nodes_created,
                "ibns_created": ibns_created,
                "hyperedges_created": hyperedges_created,
                "confidence_updates": confidence_updates
            }
        }

    def _select_next_hypothesis(self, graph, hypotheses, parameters):
        """
        Selects the next hypothesis to evaluate based on impact, confidence uncertainty, and computational cost.
        
        Returns:
            A tuple containing the selected hypothesis node and its ID, or (None, None) if no suitable hypothesis is found.
        """
        if not hypotheses:
            return None, None

        best_score = -1
        best_h = None
        best_h_id = None

        for h_id in hypotheses:
            if h_id not in graph.graph:
                continue

            h = graph.graph.nodes[h_id]

            # Calculate confidence-to-cost ratio
            confidence = h.get("confidence", [0.5, 0.5, 0.5, 0.5])
            impact = h.get("impact_score", 0.5)
            cost = h.get("metadata", {}).get("computational_cost", 1.0)

            # Higher score for higher confidence uncertainty and higher impact
            confidence_variance = sum((c - 0.5)**2 for c in confidence) / len(confidence)
            score = (impact * (1 - confidence_variance)) / cost

            if score > best_score:
                best_score = score
                best_h = h
                best_h_id = h_id

        return best_h, best_h_id

    def _execute_plan(self, graph, hypothesis, parameters):
        """
        Simulates execution of a hypothesis plan and generates synthetic evidence.
        
        Depending on the plan type specified in the hypothesis metadata, creates a list of synthetic evidence items with associated confidence scores, sources, disciplinary tags, and statistical power. Returns the generated evidence and a success flag.
        """
        # Simplified: generate some synthetic evidence
        plan = hypothesis.get("metadata", {}).get("plan", {})

        # Handle case where plan might be a string or dict
        if isinstance(plan, str):
            plan_type = "search"  # Default for string plans
        elif isinstance(plan, dict):
            plan_type = plan.get("type", "search")
        else:
            plan_type = "search"  # Default fallback

        evidence = []

        if plan_type == "search":
            # Simulate search evidence
            evidence.append({
                "content": f"Search result supporting hypothesis",
                "source": "simulated_search",
                "confidence": [0.7, 0.6, 0.8, 0.5],
                "disciplinary_tags": hypothesis.get("disciplinary_tags", []),
                "statistical_power": 0.6
            })
        elif plan_type == "experiment":
            # Simulate experimental evidence
            evidence.append({
                "content": f"Experimental result partially supporting hypothesis",
                "source": "simulated_experiment",
                "confidence": [0.8, 0.7, 0.9, 0.6],
                "disciplinary_tags": ["experimental_biology"],
                "statistical_power": 0.8
            })
        else:
            # Default evidence
            evidence.append({
                "content": f"Generic evidence for hypothesis",
                "source": "simulated_generic",
                "confidence": [0.6, 0.6, 0.6, 0.6],
                "disciplinary_tags": [],
                "statistical_power": 0.5
            })

        return {
            "evidence": evidence,
            "execution_success": True
        }

    def _create_evidence_node(self, evidence_data, hypothesis_id):
        """
        Creates a new evidence node associated with a given hypothesis.
        
        The node includes a unique identifier, label, type, confidence values, and metadata such as source, timestamp, disciplinary tags, statistical power, and the related hypothesis ID.
        """
        node_id = f"e_{hypothesis_id}_{random.randint(1000, 9999)}"

        return Node(
            node_id=node_id,
            label=evidence_data.get("content", "Evidence"),
            node_type="evidence",
            confidence=evidence_data.get("confidence", [0.7, 0.7, 0.7, 0.7]),
            metadata={
                "source": evidence_data.get("source", "unknown"),
                "timestamp": str(datetime.datetime.now()),
                "disciplinary_tags": evidence_data.get("disciplinary_tags", []),
                "statistical_power": evidence_data.get("statistical_power", 0.5),
                "related_hypothesis": hypothesis_id
            }
        )

    def _determine_edge_type(self, evidence_node, hypothesis):
        """
        Determines the type of relationship edge to connect an evidence node to a hypothesis.
        
        Randomly assigns the edge as supportive, correlative, causal (with subtype and causal metadata), or temporal (with subtype and temporal metadata) for demonstration purposes.
        
        Returns:
            A dictionary specifying the edge type, subtype, and any associated metadata.
        """
        # Default to supportive
        edge_type = {
            "type": "supportive",
            "subtype": None,
            "causal_metadata": {},
            "temporal_metadata": {}
        }

        # In a real implementation, this would analyze the evidence and hypothesis content
        # to determine the appropriate relationship type

        # Randomly assign different edge types for demonstration
        r = random.random()

        if r < 0.3:
            edge_type["type"] = "correlative"
        elif r < 0.5:
            edge_type["type"] = "causal"
            edge_type["subtype"] = "direct"
            edge_type["causal_metadata"] = {
                "confounders": [],
                "mechanism": "unknown"
            }
        elif r < 0.7:
            edge_type["type"] = "temporal"
            edge_type["subtype"] = "precedence"
            edge_type["temporal_metadata"] = {
                "delay": "unknown",
                "pattern": "linear"
            }

        return edge_type

    def _should_create_ibn(self, evidence_node, hypothesis):
        """
        Determines whether to create an Interdisciplinary Bridge Node based on disciplinary tag overlap.
        
        Returns:
            True if the evidence and hypothesis have non-overlapping disciplinary tags and each has at least one tag; otherwise, False.
        """
        evidence_tags = set(evidence_node.metadata.get("disciplinary_tags", []))
        hypothesis_tags = set(hypothesis.get("disciplinary_tags", []))

        # Create IBN if no overlap in disciplines and at least one tag in each
        return (len(evidence_tags) > 0 and
                len(hypothesis_tags) > 0 and
                len(evidence_tags.intersection(hypothesis_tags)) == 0)

    def _identify_potential_hyperedges(self, graph, evidence_data, hypothesis_id):
        """
        Identifies opportunities to create hyperedges connecting multiple evidence nodes to a hypothesis.
        
        If multiple pieces of evidence exist for the same hypothesis, returns a list containing a hyperedge that represents joint support among these nodes.
        """
        # Very simplified implementation
        hyperedges = []

        # If we have multiple evidence nodes that support the same hypothesis
        # and have related content, create a hyperedge
        if len(evidence_data) >= 2:
            hyperedges.append({
                "nodes": [hypothesis_id] + [f"e_{hypothesis_id}_{random.randint(1000, 9999)}" for _ in range(2)],
                "confidence": 0.7,
                "metadata": {
                    "relationship": "joint_support",
                    "timestamp": str(datetime.datetime.now())
                }
            })

        return hyperedges

    def _apply_temporal_decay(self, graph):
        """
        Placeholder for applying temporal decay to the influence of older evidence in the graph.
        
        Intended to reduce the impact of evidence nodes as they age, typically by adjusting edge weights or related metrics.
        """
        # In a real implementation, this would adjust edge weights
        # based on the age of the evidence
        pass

    def _detect_temporal_patterns(self, graph, hypothesis_id):
        """
        Detects temporal patterns related to a hypothesis in the graph.
        
        Currently returns an empty list; intended for future implementation of temporal pattern analysis between evidence nodes.
        """
        # Simplified implementation
        patterns = []

        # In a real implementation, this would analyze the temporal
        # relationships between evidence nodes

        return patterns

    def _adapt_topology(self, graph, hypothesis_id):
        """
        Dynamically adapts the graph topology in response to evidence patterns for a given hypothesis.
        
        Intended for future implementation to support operations such as merging similar nodes or creating community structures based on evolving evidence.
        """
        # In a real implementation, this might merge similar nodes,
        # create community structures, etc.
        pass

    def _detect_biases(self, graph, hypothesis_id, evidence_result):
        """
        Detects potential biases in the given evidence and hypothesis.
        
        Returns:
            A list of detected biases. Currently always returns an empty list as this is a placeholder.
        """
        # Simplified implementation
        biases = []

        # In a real implementation, this would check for various
        # cognitive and methodological biases

        return biases