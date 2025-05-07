import logging
import os
import uvicorn
from fastapi import FastAPI, Request
from api.routes import router  # Changed from src.api.routes to api.routes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, JSONResponse
import httpx
import os.path
import json
import asyncio
from pydantic import BaseModel
from typing import Any, Dict, Optional, Union

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("asr-got-mcp")

# Initialize FastAPI app
app = FastAPI(
    title="ASR-GoT MCP Server",
    description="Model Context Protocol server implementing Advanced Scientific Reasoning Graph-of-Thoughts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai", "http://localhost:8082", "http://127.0.0.1:8082"],  # Claude Desktop origin and local dev
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# MCP Protocol constants
MCP_VERSION = "2024-11-05"

# Define MCP request model
class MCPRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = {}
    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None

# Define the client container service name or IP
CLIENT_CONTAINER_HOST = os.getenv("CLIENT_CONTAINER_HOST", "js-client")  # Docker service name or IP
CLIENT_CONTAINER_PORT = int(os.getenv("CLIENT_CONTAINER_PORT", 80))

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """
    Handle MCP protocol requests.
    """
    try:
        logger.info(f"MCP request received: {request.method}")
        
        # Handle initialization request
        if request.method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {
                    "name": "ASR-GoT",
                    "version": "0.1.0",
                    "vendor": "Anthropic",
                    "capabilities": {
                        "asr_got.query": {
                            "description": "Use ASR-GoT to solve complex reasoning problems"
                        }
                    },
                    "status": "ready",
                    "display": {
                        "name": "ASR-GoT",
                        "description": "ASR-GoT is an Anthropic Research Graph-of-Thought reasoner."
                    }
                }
            }
        
        # Handle shutdown request
        elif request.method == "shutdown":
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": None
            }
        
        # Handle ASR-GoT query request
        elif request.method == "asr_got.query":
            # Get context parameters
            context = request.params.get("context", {})
            query = context.get("query")
            conversation_id = context.get("conversation_id")
            history = context.get("history")
            
            # Get options parameters
            options = request.params.get("options", {})
            include_reasoning_trace = options.get("include_reasoning_trace", True)
            include_graph_state = options.get("include_graph_state", True)
            max_nodes = options.get("max_nodes", 20)
            confidence_threshold = options.get("confidence_threshold", 0.7)
            
            # Validate required parameters
            if not query:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {
                        "code": -32602,
                        "message": "Missing query in context"
                    }
                }
            
            # Authenticate client (optional, based on your requirements)
            client_id = request.params.get("client_id")
            
            # Log the received request details
            logger.info(f"Processing ASR-GoT query: '{query}'")
            logger.info(f"Options: include_reasoning_trace={include_reasoning_trace}, include_graph_state={include_graph_state}")
            
            # Here we would normally process the query through ASR-GoT
            # For now, return a sample response with the expected structure
            start_time = asyncio.get_event_loop().time()
            
            # Simulate processing time
            await asyncio.sleep(0.5)
            
            # Calculate elapsed time
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {
                    "answer": "Sample response - simulated ASR-GoT reasoning result",
                    "reasoning_trace": [
                        {
                            "stage": 1,
                            "name": "Initialization",
                            "summary": "Problem scoped and initialized.",
                            "metrics": {"time": elapsed_time, "nodes_created": 1}
                        },
                        {
                            "stage": 2,
                            "name": "Decomposition",
                            "summary": "Problem broken down into components.",
                            "metrics": {"time": elapsed_time, "nodes_created": 3}
                        }
                    ],
                    "confidence": [0.85, 0.82, 0.79, 0.90],
                    "execution_time": elapsed_time,
                    "graph_state": {
                        "nodes": [
                            {
                                "node_id": "root",
                                "label": "Query Root",
                                "type": "root",
                                "confidence": [0.85]
                            }
                        ],
                        "edges": []
                    }
                }
            }
        
        # Handle unsupported methods
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
            }
            
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": request.id if hasattr(request, 'id') else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }

@app.get("/")
async def read_root():
    """
    Return a simple message for the root endpoint.
    """
    return {"message": "ASR-GoT MCP Server is running"}

if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)