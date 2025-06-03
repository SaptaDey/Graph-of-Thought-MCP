import logging
from typing import Dict, Any, List

from asr_got.models.graph import ASRGoTGraph

logger = logging.getLogger("asr-got-stage8")

class ReflectionStage:
    """
    Stage 8: Reflection

    Performs self-audit of the analysis process and results.
    """

    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the reflection stage.

        Args:
            graph: The ASR-GoT graph
            context: Context from previous stages and initialization

        Returns:
            Dictionary with reflection results
        """
        logger.info("Executing Reflection Stage")

        parameters = context.get("parameters", {})
        composition_result = context.get("composition_result", {})

        # Initialize audit results
        audit_results = {
            "passed": [],
            "warnings": [],
            "failures": []
        }

        # 1. Check high-confidence/high-impact node coverage
        high_conf_impact_check = self._check_high_confidence_impact_coverage(graph)
        if high_conf_impact_check["status"] == "pass":
            audit_results["passed"].append(high_conf_impact_check)
        elif high_conf_impact_check["status"] == "warning":
            audit_results["warnings"].append(high_conf_impact_check)
        else:
            audit_results["failures"].append(high_conf_impact_check)

        # 2. Check bias flags
        bias_check = self._check_bias_flags(graph)
        if bias_check["status"] == "pass":
            audit_results["passed"].append(bias_check)
        elif bias_check["status"] == "warning":
            audit_results["warnings"].append(bias_check)
        else:
            audit_results["failures"].append(bias_check)

        # 3. Check knowledge gaps addressed
        gaps_check = self._check_knowledge_gaps_addressed(graph, composition_result)
        if gaps_check["status"] == "pass":
            audit_results["passed"].append(gaps_check)
        elif gaps_check["status"] == "warning":
            audit_results["warnings"].append(gaps_check)
        else:
            audit_results["failures"].append(gaps_check)

        # 4. Check falsifiability criteria
        falsifiability_check = self._check_falsifiability(graph)
        if falsifiability_check["status"] == "pass":
            audit_results["passed"].append(falsifiability_check)
        elif falsifiability_check["status"] == "warning":
            audit_results["warnings"].append(falsifiability_check)
        else:
            audit_results["failures"].append(falsifiability_check)

        # 5. Check causal claim validity
        causal_check = self._check_causal_claims(graph)
        if causal_check["status"] == "pass":
            audit_results["passed"].append(causal_check)
        elif causal_check["status"] == "warning":
            audit_results["warnings"].append(causal_check)
        else:
            audit_results["failures"].append(causal_check)

        # 6. Check temporal consistency
        temporal_check = self._check_temporal_consistency(graph)
        if temporal_check["status"] == "pass":
            audit_results["passed"].append(temporal_check)
        elif temporal_check["status"] == "warning":
            audit_results["warnings"].append(temporal_check)
        else:
            audit_results["failures"].append(temporal_check)

        # 7. Check statistical rigor
        statistical_check = self._check_statistical_rigor(graph)
        if statistical_check["status"] == "pass":
            audit_results["passed"].append(statistical_check)
        elif statistical_check["status"] == "warning":
            audit_results["warnings"].append(statistical_check)
        else:
            audit_results["failures"].append(statistical_check)

        # 8. Check collaboration attributions
        attribution_check = self._check_collaboration_attributions(graph)
        if attribution_check["status"] == "pass":
            audit_results["passed"].append(attribution_check)
        elif attribution_check["status"] == "warning":
            audit_results["warnings"].append(attribution_check)
        else:
            audit_results["failures"].append(attribution_check)

        # Calculate final confidence based on audit
        passed_count = len(audit_results["passed"])
        warning_count = len(audit_results["warnings"])
        failure_count = len(audit_results["failures"])

        total_checks = passed_count + warning_count + failure_count

        # Calculate empirical support based on statistical checks
        empirical = 0.9 if statistical_check["status"] == "pass" else (0.6 if statistical_check["status"] == "warning" else 0.3)

        # Calculate theoretical basis based on causal checks
        theoretical = 0.9 if causal_check["status"] == "pass" else (0.6 if causal_check["status"] == "warning" else 0.3)

        # Calculate methodological rigor based on falsifiability and bias checks
        methodology_scores = []
        for check in [falsifiability_check, bias_check]:
            if check["status"] == "pass":
                methodology_scores.append(0.9)
            elif check["status"] == "warning":
                methodology_scores.append(0.6)
            else:
                methodology_scores.append(0.3)
        methodological = sum(methodology_scores) / len(methodology_scores)

        # Calculate consensus alignment based on attribution checks
        consensus = 0.9 if attribution_check["status"] == "pass" else (0.6 if attribution_check["status"] == "warning" else 0.3)

        # Final confidence vector
        final_confidence = [empirical, theoretical, methodological, consensus]

        # Summary based on failures and warnings
        if failure_count > 0:
            reflection_summary = "Analysis has significant weaknesses that should be addressed."
        elif warning_count > 0:
            reflection_summary = "Analysis has some areas that could be improved."
        else:
            reflection_summary = "Analysis appears robust across all audit dimensions."

        logger.info(f"Reflection complete: {passed_count} passed, {warning_count} warnings, {failure_count} failures")

        return {
            "audit_results": audit_results,
            "final_confidence": final_confidence,
            "reflection_summary": reflection_summary,
            "summary": f"Completed self-audit with {passed_count} passed, {warning_count} warnings, {failure_count} failures",
            "metrics": {
                "passed_checks": passed_count,
                "warning_checks": warning_count,
                "failed_checks": failure_count,
                "total_checks": total_checks
            }
        }

    def _check_high_confidence_impact_coverage(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check if high-confidence and high-impact nodes are well-represented in the graph."""
        # Count high-confidence nodes
        high_conf_count = 0
        high_impact_count = 0

        for _, data in graph.graph.nodes(data=True):
            # Check confidence
            confidence = data.get("confidence", [])
            if confidence and sum(confidence) / len(confidence) >= 0.7:
                high_conf_count += 1

            # Check impact
            impact = data.get("impact_score", 0)
            if impact >= 0.7:
                high_impact_count += 1

        # Calculate percentage
        total_nodes = graph.graph.number_of_nodes()
        if total_nodes == 0:
            return {
                "test": "high_confidence_impact_coverage",
                "status": "failure",
                "message": "Graph contains no nodes."
            }

        conf_percentage = high_conf_count / total_nodes
        impact_percentage = high_impact_count / total_nodes

        # Evaluate
        if conf_percentage >= 0.3 and impact_percentage >= 0.2:
            return {
                "test": "high_confidence_impact_coverage",
                "status": "pass",
                "message": f"Good coverage of high-confidence ({conf_percentage:.1%}) and high-impact ({impact_percentage:.1%}) nodes."
            }
        elif conf_percentage >= 0.1 and impact_percentage >= 0.1:
            return {
                "test": "high_confidence_impact_coverage",
                "status": "warning",
                "message": f"Limited coverage of high-confidence ({conf_percentage:.1%}) and high-impact ({impact_percentage:.1%}) nodes."
            }
        else:
            return {
                "test": "high_confidence_impact_coverage",
                "status": "failure",
                "message": f"Poor coverage of high-confidence ({conf_percentage:.1%}) and high-impact ({impact_percentage:.1%}) nodes."
            }

    def _check_bias_flags(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check if biases have been properly assessed and mitigated."""
        # Count nodes with bias flags
        flagged_nodes = 0
        serious_bias_nodes = 0

        for _, data in graph.graph.nodes(data=True):
            # Check for bias flags
            bias_flags = data.get("bias_flags", [])
            if bias_flags:
                flagged_nodes += 1

                # Check severity
                for bias in bias_flags:
                    if isinstance(bias, dict) and bias.get("severity") == "high":
                        serious_bias_nodes += 1

        # Evaluate
        if serious_bias_nodes > 0:
            return {
                "test": "bias_flags",
                "status": "warning",
                "message": f"Found {serious_bias_nodes} nodes with serious bias flags that may affect results."
            }
        elif flagged_nodes > 0:
            return {
                "test": "bias_flags",
                "status": "pass",
                "message": f"Detected and acknowledged {flagged_nodes} potential biases, none serious."
            }
        else:
            # No bias flags could mean either no biases or insufficient checking
            total_nodes = graph.graph.number_of_nodes()
            if total_nodes > 20:  # Arbitrary threshold
                return {
                    "test": "bias_flags",
                    "status": "warning",
                    "message": "No bias flags detected in a large graph, suggesting insufficient bias assessment."
                }
            else:
                return {
                    "test": "bias_flags",
                    "status": "pass",
                    "message": "No bias flags detected."
                }

    def _check_knowledge_gaps_addressed(self, graph: ASRGoTGraph, composition_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if knowledge gaps are acknowledged and addressed."""
        # Count knowledge gap nodes
        gap_nodes = 0

        for _, data in graph.graph.nodes(data=True):
            if data.get("node_type") == "placeholder_gap":
                gap_nodes += 1

        # Check if gaps are addressed in composition
        gaps_addressed = False
        for section in composition_result.get("sections", []):
            if "gap" in section.get("title", "").lower() or "gap" in section.get("type", "").lower():
                gaps_addressed = True
                break

        # Evaluate
        if gap_nodes > 0 and gaps_addressed:
            return {
                "test": "knowledge_gaps_addressed",
                "status": "pass",
                "message": f"Identified {gap_nodes} knowledge gaps and addressed them in the output."
            }
        elif gap_nodes > 0 and not gaps_addressed:
            return {
                "test": "knowledge_gaps_addressed",
                "status": "warning",
                "message": f"Identified {gap_nodes} knowledge gaps but did not adequately address them in the output."
            }
        else:
            return {
                "test": "knowledge_gaps_addressed",
                "status": "pass",
                "message": "No significant knowledge gaps identified."
            }

    def _check_falsifiability(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check if hypotheses have appropriate falsifiability criteria."""
        # Count hypothesis nodes
        hypothesis_nodes = 0
        falsifiable_nodes = 0

        for _, data in graph.graph.nodes(data=True):
            if data.get("node_type") == "hypothesis":
                hypothesis_nodes += 1

                # Check for falsification criteria
                if "falsification_criteria" in data and data["falsification_criteria"]:
                    falsifiable_nodes += 1

        # Evaluate
        if hypothesis_nodes == 0:
            return {
                "test": "falsifiability",
                "status": "warning",
                "message": "No hypothesis nodes found to evaluate falsifiability."
            }

        falsifiable_percentage = falsifiable_nodes / hypothesis_nodes

        if falsifiable_percentage >= 0.8:
            return {
                "test": "falsifiability",
                "status": "pass",
                "message": f"Good falsifiability: {falsifiable_percentage:.1%} of hypotheses have falsification criteria."
            }
        elif falsifiable_percentage >= 0.5:
            return {
                "test": "falsifiability",
                "status": "warning",
                "message": f"Limited falsifiability: only {falsifiable_percentage:.1%} of hypotheses have falsification criteria."
            }
        else:
            return {
                "test": "falsifiability",
                "status": "failure",
                "message": f"Poor falsifiability: only {falsifiable_percentage:.1%} of hypotheses have falsification criteria."
            }

    def _check_causal_claims(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check if causal claims are properly substantiated."""
        # Count causal edges
        causal_edges = 0
        well_supported_causal = 0

        for _, _, data in graph.graph.edges(data=True):
            if data.get("edge_type") == "causal":
                causal_edges += 1

                # Check for causal metadata
                if "causal_metadata" in data and data["causal_metadata"]:
                    # Check if confounders are addressed
                    if "confounders" in data["causal_metadata"]:
                        well_supported_causal += 1

        # Evaluate
        if causal_edges == 0:
            return {
                "test": "causal_claims",
                "status": "pass",
                "message": "No causal claims made in the analysis."
            }

        supported_percentage = well_supported_causal / causal_edges

        if supported_percentage >= 0.8:
            return {
                "test": "causal_claims",
                "status": "pass",
                "message": f"Strong causal validity: {supported_percentage:.1%} of causal claims are well-supported."
            }
        elif supported_percentage >= 0.5:
            return {
                "test": "causal_claims",
                "status": "warning",
                "message": f"Moderate causal validity: only {supported_percentage:.1%} of causal claims are well-supported."
            }
        else:
            return {
                "test": "causal_claims",
                "status": "failure",
                "message": f"Weak causal validity: only {supported_percentage:.1%} of causal claims are well-supported."
            }

    def _check_temporal_consistency(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check for temporal consistency in the graph."""
        # Count temporal edges
        temporal_edges = 0
        consistent_temporal = 0

        for _, _, data in graph.graph.edges(data=True):
            edge_subtype = data.get("edge_subtype") or ""
            if data.get("edge_type") == "temporal" or "temporal" in edge_subtype:
                temporal_edges += 1

                # Check for temporal metadata
                if "temporal_metadata" in data and data["temporal_metadata"]:
                    consistent_temporal += 1

        # Evaluate
        if temporal_edges == 0:
            return {
                "test": "temporal_consistency",
                "status": "pass",
                "message": "No temporal claims made in the analysis."
            }

        consistent_percentage = consistent_temporal / temporal_edges

        if consistent_percentage >= 0.8:
            return {
                "test": "temporal_consistency",
                "status": "pass",
                "message": f"Good temporal consistency: {consistent_percentage:.1%} of temporal relationships are well-defined."
            }
        elif consistent_percentage >= 0.5:
            return {
                "test": "temporal_consistency",
                "status": "warning",
                "message": f"Moderate temporal consistency: only {consistent_percentage:.1%} of temporal relationships are well-defined."
            }
        else:
            return {
                "test": "temporal_consistency",
                "status": "failure",
                "message": f"Poor temporal consistency: only {consistent_percentage:.1%} of temporal relationships are well-defined."
            }

    def _check_statistical_rigor(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check statistical rigor of evidence nodes."""
        # Count evidence nodes
        evidence_nodes = 0
        powered_nodes = 0

        for _, data in graph.graph.nodes(data=True):
            if data.get("node_type") == "evidence":
                evidence_nodes += 1

                # Check for statistical power
                if "statistical_power" in data and data["statistical_power"] >= 0.7:
                    powered_nodes += 1

        # Evaluate
        if evidence_nodes == 0:
            return {
                "test": "statistical_rigor",
                "status": "warning",
                "message": "No evidence nodes found to evaluate statistical rigor."
            }

        powered_percentage = powered_nodes / evidence_nodes

        if powered_percentage >= 0.8:
            return {
                "test": "statistical_rigor",
                "status": "pass",
                "message": f"Good statistical rigor: {powered_percentage:.1%} of evidence has adequate statistical power."
            }
        elif powered_percentage >= 0.5:
            return {
                "test": "statistical_rigor",
                "status": "warning",
                "message": f"Moderate statistical rigor: only {powered_percentage:.1%} of evidence has adequate statistical power."
            }
        else:
            return {
                "test": "statistical_rigor",
                "status": "failure",
                "message": f"Poor statistical rigor: only {powered_percentage:.1%} of evidence has adequate statistical power."
            }

    def _check_collaboration_attributions(self, graph: ASRGoTGraph) -> Dict[str, Any]:
        """Check if attributions are properly maintained."""
        # Count nodes with attribution metadata
        attributed_nodes = 0

        for _, data in graph.graph.nodes(data=True):
            if "attribution" in data and data["attribution"]:
                attributed_nodes += 1

        # Simple check - in a real implementation, would be more complex
        if attributed_nodes > 0:
            return {
                "test": "collaboration_attributions",
                "status": "pass",
                "message": f"Found {attributed_nodes} nodes with proper attribution metadata."
            }
        else:
            return {
                "test": "collaboration_attributions",
                "status": "pass",
                "message": "No collaboration attributions found, which may be appropriate if single-author analysis."
            }