import logging
import datetime
from typing import Dict, Any, List, Set

from asr_got.models.graph import ASRGoTGraph

logger = logging.getLogger("asr-got-stage7")

class CompositionStage:
    """
    Stage 7: Composition
    
    Assembles the final output based on extracted subgraphs.
    """
    
    def execute(self, graph: ASRGoTGraph, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the composition stage.
        
        Args:
            graph: The ASR-GoT graph
            context: Context from previous stages and initialization
        
        Returns:
            Dictionary with composition results
        """
        logger.info("Executing Composition Stage")
        
        # Get subgraphs from previous stage
        subgraphs = context.get("subgraphs", [])
        if not subgraphs:
            logger.warning("No subgraphs found for composition")
            return {
                "summary": "Composition skipped: No subgraphs available",
                "metrics": {}
            }
        
        parameters = context.get("parameters", {})
        query = context.get("query", "")
        
        # Track output components
        output_sections = []
        citations = []
        
        # 1. Create executive summary
        executive_summary = self._generate_executive_summary(graph, subgraphs, query)
        output_sections.append({
            "title": "Executive Summary",
            "content": executive_summary,
            "type": "summary"
        })
        
        # 2. Process each subgraph into a section
        for subgraph_data in subgraphs:
            # Generate section content
            section_content = self._generate_section_from_subgraph(
                graph, 
                subgraph_data,
                citations
            )
            
            output_sections.append({
                "title": f"{subgraph_data.get('name', 'Unnamed').replace('_', ' ').title()} Analysis",
                "content": section_content,
                "type": "analysis",
                "subgraph": subgraph_data.get("name")
            })
        
        # 3. Create interdisciplinary insights section if IBNs exist
        if graph.ibns:
            ibn_insights = self._generate_interdisciplinary_insights(graph)
            output_sections.append({
                "title": "Interdisciplinary Insights",
                "content": ibn_insights,
                "type": "interdisciplinary"
            })
        
        # 4. Create knowledge gaps section
        knowledge_gaps = self._identify_knowledge_gaps(graph)
        if knowledge_gaps:
            output_sections.append({
                "title": "Knowledge Gaps and Research Opportunities",
                "content": knowledge_gaps,
                "type": "gaps"
            })
        
        # 5. Format citations in Vancouver style per K1.3
        formatted_citations = self._format_citations_vancouver(citations)
        
        # Assemble final result
        composition_result = {
            "title": f"ASR-GoT Analysis: {query[:50]}{'...' if len(query) > 50 else ''}",
            "timestamp": str(datetime.datetime.now()),
            "sections": output_sections,
            "citations": formatted_citations,
            "node_count": graph.graph.number_of_nodes(),
            "edge_count": graph.graph.number_of_edges(),
            "hyperedge_count": len(graph.hyperedges),
            "ibn_count": len(graph.ibns)
        }
        
        logger.info(f"Composition complete: Generated output with {len(output_sections)} sections")
        
        return {
            "composition_result": composition_result,
            "summary": f"Composed final output with {len(output_sections)} sections and {len(formatted_citations)} citations",
            "metrics": {
                "section_count": len(output_sections),
                "citation_count": len(formatted_citations)
            }
        }
    
    def _generate_executive_summary(self, graph: ASRGoTGraph, 
                                  subgraphs: List[Dict[str, Any]], 
                                  query: str) -> str:
        """
        Generate an executive summary of the analysis.
        
        This is a simplified implementation that would be more sophisticated
        in a real system, potentially using LLM-based summarization.
        """
        # Simplified placeholder implementation
        node_count = graph.graph.number_of_nodes()
        edge_count = graph.graph.number_of_edges()
        subgraph_count = len(subgraphs)
        
        summary = (
            f"This analysis explores the query: \"{query}\". "
            f"The ASR-GoT framework generated a knowledge graph with {node_count} nodes and {edge_count} edges, "
            f"from which {subgraph_count} focused subgraphs were extracted for analysis. "
            f"Key findings include insights from "
        )
        
        # Add subgraph names
        subgraph_names = [sg.get("name", "unnamed").replace("_", " ") for sg in subgraphs]
        if len(subgraph_names) > 1:
            summary += ", ".join(subgraph_names[:-1]) + " and " + subgraph_names[-1] + " perspectives. "
        else:
            summary += subgraph_names[0] + " perspective. "
        
        # Add information about interdisciplinary connections if present
        if graph.ibns:
            summary += f"The analysis identified {len(graph.ibns)} interdisciplinary bridge concepts connecting different domains. "
        
        summary += (
            f"Confidence in these findings is based on multi-dimensional evaluation across empirical, "
            f"theoretical, methodological, and consensus dimensions."
        )
        
        return summary
    
    def _generate_section_from_subgraph(self, graph: ASRGoTGraph, 
                                      subgraph_data: Dict[str, Any],
                                      citations: List[Dict[str, Any]]) -> str:
        """
        Generate content for a section based on a subgraph.
        
        This is a simplified implementation that would be more sophisticated
        in a real system, potentially using LLM-based content generation.
        """
        # Simplified placeholder implementation
        nodes = subgraph_data.get("nodes", [])
        description = subgraph_data.get("description", "")
        
        content = f"{description}\n\n"
        
        # Process high-confidence nodes first
        high_conf_nodes = []
        for node_id in nodes:
            if node_id in graph.graph:
                node_data = graph.graph.nodes[node_id]
                confidence = node_data.get("confidence", [])
                if confidence and sum(confidence) / len(confidence) >= 0.7:
                    high_conf_nodes.append((node_id, node_data))
        
        # Sort by confidence
        high_conf_nodes.sort(key=lambda x: -sum(x[1].get("confidence", [0])) / len(x[1].get("confidence", [1])))
        
        # Generate content from high-confidence nodes
        for node_id, node_data in high_conf_nodes[:5]:  # Limit to top 5
            label = node_data.get("label", "Unlabeled Node")
            node_type = node_data.get("node_type", "unknown")
            
            if node_type == "hypothesis":
                # Add citation
                citation_id = len(citations) + 1
                citations.append({
                    "id": citation_id,
                    "node_id": node_id,
                    "type": "node",
                    "label": label,
                    "node_type": node_type,
                    "timestamp": node_data.get("timestamp", "")
                })
                
                content += f"• {label} [Node {node_id}][{citation_id}]\n"
                
                # Add connected evidence
                evidence_nodes = []
                for u, v in graph.graph.in_edges(node_id):
                    if u in graph.graph and graph.graph.nodes[u].get("node_type") == "evidence":
                        evidence_nodes.append((u, graph.graph.nodes[u]))
                
                if evidence_nodes:
                    content += "  Supporting evidence:\n"
                    for ev_id, ev_data in evidence_nodes[:3]:  # Limit to top 3
                        ev_label = ev_data.get("label", "Unlabeled Evidence")
                        
                        # Add citation
                        ev_citation_id = len(citations) + 1
                        citations.append({
                            "id": ev_citation_id,
                            "node_id": ev_id,
                            "type": "node",
                            "label": ev_label,
                            "node_type": "evidence",
                            "timestamp": ev_data.get("timestamp", ""),
                            "source": ev_data.get("source", "")
                        })
                        
                        content += f"    - {ev_label} [{ev_citation_id}]\n"
        
        return content
    
    def _generate_interdisciplinary_insights(self, graph: ASRGoTGraph) -> str:
        """
        Generate insights based on interdisciplinary bridges.
        """
        # Simplified placeholder implementation
        if not graph.ibns:
            return "No interdisciplinary connections identified."
        
        content = f"Analysis identified {len(graph.ibns)} interdisciplinary bridge concepts:\n\n"
        
        for ibn_id in graph.ibns:
            if ibn_id in graph.graph:
                ibn_data = graph.graph.nodes[ibn_id]
                label = ibn_data.get("label", "Unlabeled Bridge")
                
                source_disciplines = ibn_data.get("source_disciplines", [])
                target_disciplines = ibn_data.get("target_disciplines", [])
                
                content += f"• {label} [Node {ibn_id}]\n"
                content += f"  Connects disciplines: {', '.join(source_disciplines)} ↔ {', '.join(target_disciplines)}\n"
        
        return content
    
    def _identify_knowledge_gaps(self, graph: ASRGoTGraph) -> str:
        """
        Identify knowledge gaps from the graph.
        """
        # Find placeholder gap nodes and nodes with high confidence variance
        gap_nodes = []
        
        for node_id, data in graph.graph.nodes(data=True):
            # Check for placeholder gap nodes
            if data.get("node_type") == "placeholder_gap":
                gap_nodes.append((node_id, data, "explicit"))
                continue
            
            # Check for high confidence variance
            confidence = data.get("confidence", [])
            if len(confidence) >= 2:
                variance = sum((c - sum(confidence)/len(confidence))**2 for c in confidence) / len(confidence)
                if variance > 0.1:  # High variance threshold
                    gap_nodes.append((node_id, data, "variance"))
        
        if not gap_nodes:
            return "No significant knowledge gaps identified."
        
        content = "The following knowledge gaps and research opportunities were identified:\n\n"
        
        for node_id, data, gap_type in gap_nodes:
            label = data.get("label", "Unlabeled Gap")
            
            if gap_type == "explicit":
                content += f"• {label} [Node {node_id}] - Explicit knowledge gap\n"
            else:
                content += f"• {label} [Node {node_id}] - High uncertainty (confidence variance)\n"
            
            # Add related research questions if available
            if "research_questions" in data:
                content += "  Suggested research questions:\n"
                for question in data["research_questions"]:
                    content += f"    - {question}\n"
        
        return content
    
    def _format_citations_vancouver(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format citations in Vancouver style per K1.3.
        """
        formatted = []
        
        for citation in citations:
            # Format based on type
            if citation.get("type") == "node":
                formatted.append({
                    "id": citation["id"],
                    "text": f"{citation.get('label', 'Unlabeled')}. ASR-GoT Node {citation.get('node_id', 'unknown')}. "
                           f"Type: {citation.get('node_type', 'unknown')}. "
                           f"Generated: {citation.get('timestamp', '')}."
                })
            else:
                # Generic format for other types
                formatted.append({
                    "id": citation["id"],
                    "text": f"{citation.get('label', 'Unlabeled')}. {citation.get('source', 'Unknown source')}. "
                           f"{citation.get('timestamp', '')}."
                })
        
        return formatted