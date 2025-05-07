import logging
import httpx
import os
import json
import subprocess
import sys
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
        self.use_desktop_app = self.config["claude"].get("use_desktop_app", True)
        self.desktop_app_path = self.config["claude"].get("desktop_app_path", "")
        
        # Fallback to API if desktop app is not enabled
        self.base_url = self.config["claude"]["api_endpoint"]
        self.api_key = self.config["claude"]["api_key"] or os.environ.get("CLAUDE_API_KEY", "")
        self.model = self.config["claude"]["model"]
        
        if self.use_desktop_app:
            logger.info(f"Claude client initialized to use desktop application")
        else:
            logger.info(f"Claude client initialized for API model: {self.model}")
    
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
                    "model": "claude-3-7-sonnet-20250219",
                    "use_desktop_app": True,
                    "desktop_app_path": ""
                }
            }
    
    async def query_claude(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a query to Claude and get a response.
        """
        if self.use_desktop_app:
            return await self._query_claude_desktop(message, context)
        else:
            return await self._query_claude_api(message, context)
    
    async def _query_claude_desktop(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a query to Claude desktop application.
        
        This implementation creates a temporary file with the query and opens it with the 
        Claude desktop application. The user would then interact with Claude directly.
        """
        try:
            # Create formatted prompt
            prompt = message
            if context:
                prompt = f"{prompt}\n\nContext: {json.dumps(context, indent=2)}"
            
            # Create a temporary HTML file to open Claude with the prompt
            temp_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                         "temp_claude_prompt.html")
            
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>ASR-GoT Query for Claude</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .prompt {{ white-space: pre-wrap; background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                        .instructions {{ margin-bottom: 20px; color: #555; }}
                    </style>
                </head>
                <body>
                    <h1>ASR-GoT Query for Claude</h1>
                    <div class="instructions">
                        <p>Copy the following prompt into your Claude desktop application:</p>
                    </div>
                    <div class="prompt">{prompt}</div>
                </body>
                </html>
                """)
            
            # Open the file in the default browser
            if sys.platform == "win32":
                os.startfile(temp_file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", temp_file_path], check=True)
            else:
                subprocess.run(["xdg-open", temp_file_path], check=True)
                
            # Return a message indicating the query was opened in Claude desktop
            return {
                "success": True,
                "message": "Query has been opened for the Claude desktop application. Please check your browser.",
                "desktop_mode": True
            }
            
        except Exception as e:
            logger.error(f"Error using Claude desktop: {str(e)}")
            return {"error": str(e), "desktop_mode": True}
    
    async def _query_claude_api(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a query to Claude API and get a response.
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
            logger.error(f"Error querying Claude API: {str(e)}")
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