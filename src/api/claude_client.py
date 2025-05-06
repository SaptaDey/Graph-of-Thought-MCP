import logging
import httpx
import os
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("asr-got-claude-client")

class ClaudeClient:
    """
    Client to interface with Claude Desktop application.
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize the Claude client with configurations.
        """
        self.config = self._load_config(config_path)
        self.base_url = self.config["claude"]["api_endpoint"]
        self.api_key = self.config["claude"]["api_key"] or os.environ.get("CLAUDE_API_KEY", "")
        self.model = self.config["claude"]["model"]
        
        logger.info(f"Claude client initialized for model: {self.model}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from the specified path.
        """
        try:
            # Try to open config file with absolute path if relative path fails
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except FileNotFoundError:
                # Try in the parent directory
                with open(os.path.join("..", config_path), "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            # Return default fallback configuration
            return {
                "claude": {
                    "api_endpoint": "http://localhost:8082/api/claude",
                    "api_key": "",
                    "model": "claude-3-7-sonnet-20250219"
                }
            }
    
    async def query_claude(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a query to Claude and get a response.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # Add context if provided
        if context:
            payload["context"] = context
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error querying Claude: {str(e)}")
            return {"error": str(e)}
    
    async def format_asr_got_query(self, query: str, graph_state: Dict[str, Any] = None) -> str:
        """
        Format a query to include ASR-GoT context for Claude.
        """
        # Create a prompt that instructs Claude to use ASR-GoT framework
        asr_got_prompt = (
            "Please analyze the following query using the Advanced Scientific Reasoning "
            "Graph-of-Thoughts (ASR-GoT) framework:\n\n"
            f"QUERY: {query}\n\n"
        )
        
        # Add graph state if available
        if graph_state:
            asr_got_prompt += (
                "Current ASR-GoT Graph State:\n"
                f"{json.dumps(graph_state, indent=2)}\n\n"
            )
        
        # Add instructions to follow the ASR-GoT stages
        asr_got_prompt += (
            "Please follow the 8-stage ASR-GoT process:\n"
            "1. Initialization\n"
            "2. Decomposition\n"
            "3. Hypothesis/Planning\n"
            "4. Evidence Integration\n"
            "5. Pruning/Merging\n"
            "6. Subgraph Extraction\n"
            "7. Composition\n"
            "8. Reflection\n\n"
            "Provide your analysis structured according to these stages."
        )
        
        return asr_got_prompt