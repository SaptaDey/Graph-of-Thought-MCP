#!/usr/bin/env python3
"""
ASR-GoT MCP Server for Claude Desktop Integration

This is a standalone Model Context Protocol (MCP) server that integrates
the Advanced Scientific Reasoning Graph-of-Thoughts (ASR-GoT) framework
directly with Claude Desktop.

The server communicates via stdio and implements the MCP specification
for tools, resources, and prompts.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Add the src directory to the Python path to import ASR-GoT modules
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# Lazy import ASR-GoT modules to speed up startup
ASRGoTProcessor = None
ASRGoTGraph = None

def _import_asr_got():
    """
    Performs a lazy import of ASR-GoT modules, assigning them to global variables.
    
    Raises:
        ImportError: If the ASR-GoT modules cannot be imported.
    """
    global ASRGoTProcessor, ASRGoTGraph
    if ASRGoTProcessor is None:
        try:
            from asr_got.core import ASRGoTProcessor as _ASRGoTProcessor
            from asr_got.models.graph import ASRGoTGraph as _ASRGoTGraph
            ASRGoTProcessor = _ASRGoTProcessor
            ASRGoTGraph = _ASRGoTGraph
        except ImportError as e:
            logger.error(f"Error importing ASR-GoT modules: {e}")
            raise

# Configure logging for faster startup (stderr only initially)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ],
)
logger = logging.getLogger("asr-got-mcp-server")

# MCP Protocol constants
MCP_VERSION = "2024-11-05"
SERVER_NAME = "asr-got"
SERVER_VERSION = "1.0.0"

class MCPTools:
    """Define MCP tools for ASR-GoT functionality."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """
        Returns the list of available MCP tools supported by the server.
        
        Each tool is described with its name, purpose, and input schema, including
        required and optional parameters for tool invocation.
        """
        return [
            {
                "name": "asr_got_query",
                "description": "Process a query using the Advanced Scientific Reasoning Graph-of-Thoughts framework",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or problem to analyze using ASR-GoT"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for the query",
                            "properties": {
                                "domain": {"type": "string", "description": "Scientific domain or field"},
                                "complexity": {"type": "string", "enum": ["low", "medium", "high"], "description": "Expected complexity level"},
                                "session_id": {"type": "string", "description": "Session ID for continuing previous reasoning"}
                            }
                        },
                        "options": {
                            "type": "object",
                            "description": "Processing options",
                            "properties": {
                                "max_nodes": {"type": "integer", "minimum": 5, "maximum": 50, "default": 20},
                                "confidence_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.7},
                                "include_reasoning_trace": {"type": "boolean", "default": True},
                                "include_graph_state": {"type": "boolean", "default": True}
                            }
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_graph_state",
                "description": "Retrieve the current state of a reasoning graph",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID of the graph to retrieve"
                        }
                    },
                    "required": ["session_id"]
                }
            }
        ]

class ASRGoTMCPServer:
    """
    Model Context Protocol server for ASR-GoT application.
    Handles MCP protocol communication with Claude Desktop and processes
    queries directly using the embedded ASR-GoT engine.
    """

    def __init__(self):
        """
        Initializes the ASR-GoT MCP server instance.
        
        Sets up the server state, including initialization flag, tool definitions, and prepares for lazy processor loading. Logs server startup and prints readiness to standard error.
        """
        self.initialized = False
        self.processor = None  # Initialize lazily
        self.tools = MCPTools()

        # Log that we're starting the server
        logger.info("ASR-GoT MCP Server started")
        print("ASR-GoT MCP Server ready", file=sys.stderr)

    def _get_processor(self):
        """
        Returns the ASR-GoT processor instance, initializing it on first access.
        
        If the processor has not been created yet, this method performs a lazy import
        of the required ASR-GoT modules and instantiates the processor before returning it.
        """
        if self.processor is None:
            logger.info("LAZY LOADING: Initializing ASR-GoT processor now...")
            import traceback
            logger.info(f"LAZY LOADING: Called from: {traceback.format_stack()}")
            _import_asr_got()  # Lazy import when actually needed
            self.processor = ASRGoTProcessor()
            logger.info("LAZY LOADING: ASR-GoT processor initialized successfully")
        return self.processor

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handles an incoming MCP protocol message and dispatches it to the appropriate handler.
        
        Depending on the message's `method`, this function processes initialization, shutdown, tool listing, tool invocation, or notification messages. Returns a response dictionary for requests that require a reply, or None for notifications. If the message format is invalid or an error occurs, returns an MCP-compliant error response.
        """
        try:
            if not isinstance(message, dict):
                logger.error(f"Invalid message format: {message}")
                return self._create_error_response(-32700, "Parse error", 0)

            method = message.get("method")
            params = message.get("params", {})
            msg_id = message.get("id")

            logger.info(f"Received message with method: {method}, id: {msg_id}")

            if method == "initialize":
                return await self._handle_initialize(params, msg_id)
            elif method == "shutdown":
                return await self._handle_shutdown(params, msg_id)
            elif method == "tools/list":
                return await self._handle_tools_list(params, msg_id)
            elif method == "tools/call":
                return await self._handle_tools_call(params, msg_id)
            elif method == "notifications/cancelled":
                # Just acknowledge this notification
                logger.info(f"Received cancellation notification: {params}")
                return None
            elif method == "notifications/initialized":
                # Handle initialized notification
                logger.info("Received initialized notification")
                return None
            else:
                logger.warning(f"Unknown method: {method}")
                return self._create_error_response(-32601, f"Method not found: {method}", msg_id)

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(traceback.format_exc())
            return self._create_error_response(-32603, f"Internal error: {str(e)}", msg_id if 'msg_id' in locals() else 0)

    async def _handle_initialize(self, params: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Handles the MCP initialize request from the client.
        
        Sets protocol and client information, marks the server as initialized, and returns a response indicating supported capabilities and server details.
        """
        logger.info(f"Handling initialize request from client: {params.get('clientInfo', {}).get('name', 'unknown')}")
        self.protocol_version = params.get("protocolVersion")
        self.client_info = params.get("clientInfo", {})

        # Mark as initialized immediately for fast response
        self.initialized = True

        logger.info("Returning initialize response immediately")

        # Return response immediately without any heavy operations
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": MCP_VERSION,
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    },
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION
                }
            }
        }

        logger.info("Initialize response ready")
        return response

    async def _handle_shutdown(self, params: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Handles a shutdown request by marking the server as uninitialized and returning a response indicating successful shutdown.
        """
        logger.info("Handling shutdown request")
        self.initialized = False

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": None
        }

    async def _handle_tools_list(self, params: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Handles the MCP tools/list request by returning the list of available tools.
        
        Args:
            params: The parameters of the tools/list request.
            msg_id: The unique identifier for the MCP message.
        
        Returns:
            A dictionary containing the MCP response with the list of supported tools.
        """
        logger.info("Handling tools/list request")

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": self.tools.get_tools()
            }
        }

    async def _handle_tools_call(self, params: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Handles a tools/call MCP request by dispatching to the appropriate ASR-GoT tool.
        
        If the server is not initialized, returns an error response. Dispatches the call to either the ASR-GoT query processor or the graph state retriever based on the requested tool name. Returns an error response for unknown tools or if an exception occurs during execution.
        """
        if not self.initialized:
            return self._create_error_response(-32002, "Server not initialized", msg_id)

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        logger.info(f"Handling tools/call request for tool: {tool_name}")

        try:
            if tool_name == "asr_got_query":
                return await self._execute_asr_got_query(arguments, msg_id)
            elif tool_name == "get_graph_state":
                return await self._execute_get_graph_state(arguments, msg_id)
            else:
                return self._create_error_response(-32601, f"Unknown tool: {tool_name}", msg_id)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return self._create_error_response(-32603, f"Tool execution error: {str(e)}", msg_id)

    async def _execute_asr_got_query(self, arguments: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Executes an ASR-GoT query using the provided arguments and returns the analysis result.
        
        Processes a scientific reasoning query through the ASR-GoT engine, incorporating optional context and parameters. Returns a structured MCP response containing the final answer, formatted reasoning trace, confidence scores, graph state, session ID, and relevant metadata. If the required query argument is missing or an error occurs during processing, returns an MCP-compliant error response.
        """
        query = arguments.get("query")
        if not query:
            return self._create_error_response(-32602, "Missing required argument: query", msg_id)

        context = arguments.get("context", {})
        options = arguments.get("options", {})

        logger.info(f"Executing ASR-GoT query: {query[:100]}...")

        try:
            # Process the query using the ASR-GoT processor
            processor = self._get_processor()
            logger.info(f"Processing query with context: {context}, options: {options}")
            result = processor.process_query(
                query=query,
                context=context,
                parameters=options
            )
            logger.info(f"ASR-GoT result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")

            # Format the response for MCP
            graph_state = result.get("graph_state", {})
            formatted_result = {
                "answer": self._extract_final_answer(result),
                "reasoning_trace": self._format_reasoning_trace(result.get("reasoning_trace", [])),
                "confidence_scores": result.get("confidence", [0.0, 0.0, 0.0, 0.0]),
                "graph_state": graph_state,
                "session_id": context.get("session_id", "new-session"),
                "metadata": {
                    "processing_time": result.get("processing_time"),
                    "node_count": len(graph_state.get("nodes", [])),
                    "edge_count": len(graph_state.get("edges", []))
                }
            }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"**ASR-GoT Analysis Result:**\n\n{formatted_result['answer']}\n\n**Reasoning Trace:**\n{formatted_result['reasoning_trace']}"
                        }
                    ],
                    "isError": False
                }
            }

        except Exception as e:
            logger.error(f"Error processing ASR-GoT query: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error processing query: {str(e)}"
                        }
                    ],
                    "isError": True
                }
            }

    async def _execute_get_graph_state(self, arguments: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieves and summarizes the current state of the reasoning graph for a given session.
        
        If a graph exists for the specified session ID, returns a summary including node, edge, and layer counts, along with details of the most recent nodes. If no graph is found, returns a message indicating its absence. On error, returns an error message in the response.
        
        Args:
            arguments: Dictionary containing the required "session_id" key.
            msg_id: The MCP message ID for correlating the response.
        
        Returns:
            An MCP-compliant response dictionary containing a textual summary of the graph state or an error message.
        """
        session_id = arguments.get("session_id")
        if not session_id:
            return self._create_error_response(-32602, "Missing required argument: session_id", msg_id)

        try:
            # Get graph state from processor
            processor = self._get_processor()
            graph_state = processor.get_graph_state(session_id)

            if graph_state is None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"No graph found for session ID: {session_id}"
                            }
                        ],
                        "isError": False
                    }
                }

            # Format graph state for display
            node_count = len(graph_state.get("nodes", []))
            edge_count = len(graph_state.get("edges", []))
            layer_count = len(graph_state.get("layers", {}))

            graph_summary = f"**Graph State for Session {session_id}:**\n\n"
            graph_summary += f"- Nodes: {node_count}\n"
            graph_summary += f"- Edges: {edge_count}\n"
            graph_summary += f"- Layers: {layer_count}\n\n"

            if graph_state.get("nodes"):
                graph_summary += "**Recent Nodes:**\n"
                for node in graph_state["nodes"][-5:]:  # Show last 5 nodes
                    graph_summary += f"- {node.get('label', 'Unknown')}: {node.get('node_type', 'unknown')}\n"

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": graph_summary
                        }
                    ],
                    "isError": False
                }
            }

        except Exception as e:
            logger.error(f"Error getting graph state: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error retrieving graph state: {str(e)}"
                        }
                    ],
                    "isError": True
                }
            }

    def _extract_final_answer(self, result: Dict[str, Any]) -> str:
        """
        Extracts the final answer string from an ASR-GoT result dictionary.
        
        If a "final_answer" is present in the result, returns it. Otherwise, summarizes the last stage of the reasoning trace if available, or returns a default completion message if not.
        """
        # The ASR-GoT processor returns a dict with "result", "reasoning_trace", "confidence", "graph_state"
        if isinstance(result, dict):
            # Try to get a final answer from the composition result
            composition_result = result.get("result", {})
            if isinstance(composition_result, dict):
                final_answer = composition_result.get("final_answer")
                if final_answer:
                    return final_answer

            # If no final answer, create a summary from the reasoning trace
            reasoning_trace = result.get("reasoning_trace", [])
            if reasoning_trace:
                last_stage = reasoning_trace[-1] if reasoning_trace else {}
                summary = last_stage.get("summary", "Processing completed through ASR-GoT reasoning pipeline.")
                return f"ASR-GoT Analysis Complete: {summary}"

            return "ASR-GoT processing completed successfully."

        return "Processing completed, but result format was unexpected."

    def _format_reasoning_trace(self, trace: List[Dict[str, Any]]) -> str:
        """
        Formats a reasoning trace into a readable string for display.
        
        Each stage in the trace is presented with its stage number, name, and summary. Returns a default message if the trace is empty.
        """
        if not trace:
            return "No reasoning trace available."

        formatted_lines = []
        for stage in trace:
            stage_num = stage.get("stage", "?")
            stage_name = stage.get("name", "Unknown Stage")
            summary = stage.get("summary", "No summary available.")

            formatted_lines.append(f"**Stage {stage_num}: {stage_name}**")
            formatted_lines.append(summary)
            formatted_lines.append("")  # Empty line for spacing

        return "\n".join(formatted_lines)

    def _create_error_response(self, code: int, message: str, msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Constructs an MCP-compliant error response message.
        
        Args:
            code: The MCP error code.
            message: The error message to include in the response.
            msg_id: The ID of the message that triggered the error.
        
        Returns:
            A dictionary representing the MCP error response.
        """
        logger.error(f"Creating error response: {code} - {message}")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }

async def read_message(reader: asyncio.StreamReader) -> Optional[Dict[str, Any]]:
    """
    Asynchronously reads and parses a Language Server Protocol (LSP) message from a stream reader.
    
    Reads headers to determine the content length, then reads and decodes the message body as JSON. Returns the parsed message as a dictionary, or None if parsing fails or the Content-Length header is missing.
    """
    # Read the header
    header = b""
    content_length = None

    while True:
        line = await reader.readline()
        if not line or line == b"\r\n":
            break
        header += line
        header_line = line.decode("utf-8").strip()
        if header_line.startswith("Content-Length: "):
            content_length = int(header_line[16:])

    if content_length is None:
        logger.error("No Content-Length header found")
        return None

    # Read the content
    content = await reader.readexactly(content_length)

    try:
        return json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON message: {e}")
        return None

async def write_message(writer: asyncio.StreamWriter, message: Dict[str, Any]) -> None:
    """
    Asynchronously writes a JSON-RPC (LSP) message to the provided stream writer.
    
    The message is serialized to JSON, framed with a Content-Length header, and sent over the stream.
    """
    content = json.dumps(message)
    content_bytes = content.encode("utf-8")
    header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
    header_bytes = header.encode("utf-8")

    writer.write(header_bytes + content_bytes)
    await writer.drain()

def main():
    """
    Runs the ASR-GoT MCP server main loop, processing MCP messages from stdin and writing responses to stdout.
    
    Returns:
        int: Exit code 0 on normal exit, 1 on unexpected errors.
    """
    try:
        server = ASRGoTMCPServer()

        # Main message processing loop using stdio
        while True:
            try:
                # Read message from stdin
                message = read_message_sync()
                if message is None:
                    logger.info("No more messages, exiting")
                    break

                # Process the message
                response = asyncio.run(server.process_message(message))

                # Send the response if any
                if response:
                    write_message_sync(response)

                # Exit on shutdown
                if message.get("method") == "shutdown":
                    logger.info("Shutdown requested, exiting")
                    break

            except (EOFError, KeyboardInterrupt):
                logger.info("Input stream closed, exiting")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

    return 0

def read_message_sync() -> Optional[Dict[str, Any]]:
    """
    Reads and parses a single MCP message from standard input synchronously.
    
    Returns:
        The parsed message as a dictionary if successful, or None if input is incomplete,
        malformed, or an error occurs.
    """
    try:
        # Read headers
        content_length = None
        while True:
            line = sys.stdin.readline()
            if not line:
                return None

            line = line.strip()
            if not line:
                break

            if line.startswith("Content-Length: "):
                content_length = int(line[16:])

        if content_length is None:
            logger.error("No Content-Length header found")
            return None

        # Read content
        content = sys.stdin.read(content_length)
        if not content:
            return None

        message = json.loads(content)
        logger.info(f"Received message: {message.get('method', 'unknown')}")
        return message

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON message: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading message: {e}")
        return None

def write_message_sync(message: Dict[str, Any]) -> None:
    """
    Serializes and writes a JSON message to stdout using the LSP Content-Length protocol.
    
    The message is encoded as UTF-8 and immediately flushed to ensure delivery.
    """
    try:
        content = json.dumps(message)
        content_bytes = content.encode("utf-8")
        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"

        sys.stdout.write(header)
        sys.stdout.write(content)
        sys.stdout.flush()

        logger.info(f"Sent response for method: {message.get('result', {}).get('method', 'unknown')}")

    except Exception as e:
        logger.error(f"Error writing message: {e}")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("ASR-GoT MCP server terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)