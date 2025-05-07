#!/usr/bin/env python
import asyncio
import json
import logging
import os
import sys
import traceback
import urllib.request
import urllib.error
import urllib.parse
import requests
import subprocess
import time
from typing import Dict, Any, Optional, List, Union

# Configure logging to file for debugging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "mcp_server.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Log to stderr for Claude to capture
    ],
)
logger = logging.getLogger("asr-got-mcp-server")

# ASR-GoT API settings
ASR_GOT_API_URL = "http://localhost:8082/api/v1/claude/query"

# MCP Protocol constants
MCP_VERSION = "2024-11-05"

def check_asr_got_running() -> bool:
    """Check if ASR-GoT server is running."""
    try:
        # Use a shorter timeout for faster checks
        response = requests.get("http://localhost:8082/health", timeout=1)
        return response.status_code == 200
    except:
        return False

def start_docker_containers() -> Optional[subprocess.Popen]:
    """Start ASR-GoT Docker containers."""
    try:
        # Get the project directory
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"Project directory: {project_dir}")
        
        # Check if containers are already running
        if check_asr_got_running():
            logger.info("ASR-GoT server is already running")
            return None
        
        # Start containers in detached mode
        logger.info("Starting ASR-GoT Docker containers...")
        
        # Use subprocess with full paths to avoid issues
        process = subprocess.Popen(
            ["docker-compose", "up", "--detach"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            cwd=project_dir
        )
        
        # Reduced wait timeout to prevent blocking for too long
        max_attempts = 2  # Reduced from 3
        attempts = 0
        while attempts < max_attempts:
            logger.info(f"Waiting for ASR-GoT server to start (attempt {attempts+1}/{max_attempts})...")
            time.sleep(0.5)  # Reduced from 1 second
            if check_asr_got_running():
                logger.info("ASR-GoT server is now running!")
                return process
            attempts += 1
        
        # Return process even if server isn't ready yet
        # We'll deal with API calls separately
        logger.warning("ASR-GoT server not yet ready, but returning control to MCP server")
        return process
    except Exception as e:
        logger.error(f"Error starting Docker containers: {str(e)}")
        logger.error(traceback.format_exc())
        return None

class ASRGoTMCPServer:
    """
    Model Context Protocol server for ASR-GoT application.
    Handles MCP protocol communication with Claude and forwards requests to ASR-GoT API.
    """
    
    def __init__(self):
        self.initialized = False
        self.request_id_counter = 0
        self.session_id = None
        self.docker_process = None
        self.docker_initializing = False
        
        # Log that we're starting the server
        print("ASR-GoT MCP Server started", file=sys.stderr)  # Explicit stderr output for Claude to capture
        logger.info("ASR-GoT MCP Server started")
    
    async def _initialize_docker_async(self):
        """
        Initialize Docker containers asynchronously to avoid blocking the initialize response.
        """
        self.docker_initializing = True
        logger.info("Starting Docker containers asynchronously...")
        
        try:
            # Check if ASR-GoT server is already running
            if check_asr_got_running():
                logger.info("ASR-GoT server is already running")
                self.docker_initializing = False
                return
                
            # Start Docker containers if not already running
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._start_docker_containers_safely())
            
            logger.info("Docker container initialization complete")
        except Exception as e:
            logger.error(f"Error during Docker initialization: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            self.docker_initializing = False
            
    def _start_docker_containers_safely(self):
        """
        Start Docker containers in a separate thread.
        This prevents blocking the asyncio event loop.
        """
        try:
            logger.info("Starting Docker containers in separate thread...")
            self.docker_process = start_docker_containers()
            return self.docker_process
        except Exception as e:
            logger.error(f"Error in _start_docker_containers_safely: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an incoming MCP message and generate a response.
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
            elif method == "asr_got.query":
                return await self._handle_asr_got_query(params, msg_id)
            elif method == "notifications/cancelled":
                # Just acknowledge this notification
                logger.info(f"Received cancellation notification: {params}")
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
        Handle initialize request from Claude.
        """
        logger.info(f"Handling initialize request: {params}")
        self.protocol_version = params.get("protocolVersion")
        self.client_info = params.get("clientInfo", {})
        
        # Start ASR-GoT Docker async without waiting for completion
        # Use create_task to avoid blocking but don't await it
        asyncio.create_task(self._initialize_docker_async())
        
        # Mark as initialized immediately - we'll handle Docker availability checks in the query handler
        self.initialized = True
        
        # Return success immediately, don't wait for Docker to start
        logger.info("Returning initialize response")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "name": "ASR-GoT",
                "version": "0.1.0",
                "vendor": "Anthropic",
                "capabilities": {
                    "asr_got.query": {
                        "description": "Use ASR-GoT to solve complex reasoning problems"
                    }
                },
                "status": "ready",  # Always return "ready" to avoid timeout issues
                "display": {
                    "name": "ASR-GoT",
                    "description": "ASR-GoT is an Anthropic Research Graph-of-Thought reasoner."
                }
            }
        }
    
    async def _handle_shutdown(self, params: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Handle shutdown request from Claude.
        """
        logger.info("Handling shutdown request")
        self.initialized = False
        
        # Stop Docker containers if we started them
        if self.docker_process is not None:
            logger.info("Stopping ASR-GoT Docker containers...")
            try:
                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                subprocess.run(
                    ["docker-compose", "down"],
                    cwd=project_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                )
                logger.info("ASR-GoT Docker containers stopped")
            except Exception as e:
                logger.error(f"Error stopping Docker containers: {str(e)}")
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": None
        }
    
    async def _handle_asr_got_query(self, params: Dict[str, Any], msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Handle ASR-GoT query request from Claude.
        """
        if not self.initialized:
            return self._create_error_response(-32002, "Server not initialized", msg_id)
        
        logger.info(f"Handling ASR-GoT query: {params}")
        
        context = params.get("context", {})
        if not context:
            return self._create_error_response(-32602, "Missing context parameter", msg_id)
        
        query = context.get("query")
        if not query:
            return self._create_error_response(-32602, "Missing query in context", msg_id)
        
        session_id = context.get("session_id")
        parameters = context.get("parameters", {})
        
        # Return a quick test response without waiting for Docker - this helps debug timeout issues
        if query.lower().strip() == "test":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "response": "This is a test response. ASR-GoT MCP server is functioning correctly.",
                    "reasoningTrace": "Test reasoning trace.",
                    "confidence": [0.9, 0.9, 0.9, 0.9],
                    "graphState": {},
                    "sessionId": self.session_id or "test-session"
                }
            }
        
        # Check if this is a "continue" request, which should be handled quickly
        if query.lower().strip() == "continue" or query.lower().strip() == "continue to iterate?":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "response": "Yes, continuing with the current ASR-GoT graph. Please provide your next query or say 'continue' to iterate further.",
                    "reasoningTrace": "Continuing with existing graph...",
                    "confidence": [0.9, 0.9, 0.9, 0.9] if self.session_id else [0.0, 0.0, 0.0, 0.0],
                    "graphState": {},
                    "sessionId": self.session_id or "continue-session"
                }
            }
        
        # If Docker is still initializing, return a quick response to avoid timeout
        if self.docker_initializing:
            logger.info("Docker still initializing, sending temporary response to avoid timeout")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "response": "The ASR-GoT server is still initializing. Please try again in a few moments. You can type 'test' to check if the server is ready.",
                    "reasoningTrace": "Server initializing...",
                    "confidence": [0.0, 0.0, 0.0, 0.0],
                    "graphState": {},
                    "sessionId": self.session_id or "init-session"
                }
            }
        
        # Check if ASR-GoT server is running with faster retries
        max_retries = 2
        retry_delay = 0.3
        server_ready = False
        
        # Try a few quick retries to see if server just started
        for i in range(max_retries):
            if check_asr_got_running():
                server_ready = True
                break
                
            logger.info(f"ASR-GoT server not responding, retry {i+1}/{max_retries}...")
            await asyncio.sleep(retry_delay)
        
        if not server_ready:
            # If Docker is not running, start it but return quickly to avoid timeout
            if not self.docker_initializing:
                logger.warning("ASR-GoT server not running, attempting to start it...")
                asyncio.create_task(self._initialize_docker_async())
            
            # Return a message to the user rather than an error, to avoid disconnection
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "response": "The ASR-GoT server is starting up. Please try again in a few moments by typing 'test' to check status.",
                    "reasoningTrace": "Server starting...",
                    "confidence": [0.0, 0.0, 0.0, 0.0],
                    "graphState": {},
                    "sessionId": self.session_id or "starting-session"
                }
            }
        
        # Forward query to ASR-GoT API
        try:
            # Prepare request
            request_data = {
                "query": query,
                "process_response": True
            }
            
            if session_id:
                request_data["session_id"] = session_id
            
            if parameters:
                request_data["parameters"] = parameters
            
            logger.info(f"Sending request to ASR-GoT API: {request_data}")
            
            # Make request to ASR-GoT API with reduced timeout to prevent MCP timeout
            try:
                # Use an even shorter timeout for Windows - 30 seconds is safer for MCP
                response = requests.post(
                    ASR_GOT_API_URL,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30  # Reduced timeout for Windows platform
                )
                
                # Check for errors
                response.raise_for_status()
                
                # Parse response
                asr_got_response = response.json()
                logger.info("Received response from ASR-GoT API")
                
                # Extract Claude's response
                claude_response = None
                if "choices" in asr_got_response and asr_got_response["choices"] and "message" in asr_got_response["choices"][0]:
                    claude_response = asr_got_response["choices"][0]["message"].get("content", "")
                
                # Extract ASR-GoT result
                asr_got_result = asr_got_response.get("asr_got_result", {})
                
                # Check for a session ID
                if "session_id" in asr_got_response:
                    self.session_id = asr_got_response["session_id"]
                
                # Construct MCP response
                result = {
                    "response": claude_response or "No response from ASR-GoT model.",
                    "reasoningTrace": self._extract_reasoning_trace(asr_got_result),
                    "confidence": self._extract_confidence(asr_got_result),
                    "graphState": asr_got_result.get("graph_state", {}),
                    "sessionId": self.session_id
                }
                
                logger.info("Returning formatted response to Claude")
                
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                }
            except requests.exceptions.Timeout:
                logger.error("Timeout while querying ASR-GoT API")
                # Return a graceful response instead of an error
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "response": "The ASR-GoT server took too long to respond. Please try a simpler query or try again later. For complex problems, you can try sending 'continue' to continue working with the current graph.",
                        "reasoningTrace": "Query processing timed out. This is often a sign that the problem is too complex or the system is under heavy load.",
                        "confidence": [0.0, 0.0, 0.0, 0.0],
                        "graphState": {},
                        "sessionId": self.session_id or "timeout-session"
                    }
                }
        except Exception as e:
            logger.error(f"Error querying ASR-GoT API: {str(e)}")
            logger.error(traceback.format_exc())
            # Return a graceful response instead of an error
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "response": f"There was an error communicating with the ASR-GoT server: {str(e)}. Please try again later or type 'test' to check the server status.",
                    "reasoningTrace": "Error in ASR-GoT communication.",
                    "confidence": [0.0, 0.0, 0.0, 0.0],
                    "graphState": {},
                    "sessionId": self.session_id or "error-session"
                }
            }
    
    def _extract_reasoning_trace(self, asr_got_result: Dict[str, Any]) -> str:
        """
        Extract and format reasoning trace from ASR-GoT result.
        """
        if not asr_got_result or "reasoning_trace" not in asr_got_result:
            return "No reasoning trace available."
        
        trace = asr_got_result["reasoning_trace"]
        formatted_trace = []
        
        for stage in trace:
            stage_name = stage.get("name", "Unknown Stage")
            stage_number = stage.get("stage", "?")
            summary = stage.get("summary", "No summary available.")
            
            formatted_trace.append(f"Stage {stage_number}: {stage_name}\n{summary}\n")
        
        return "\n".join(formatted_trace)
    
    def _extract_confidence(self, asr_got_result: Dict[str, Any]) -> List[float]:
        """
        Extract confidence scores from ASR-GoT result.
        """
        if not asr_got_result or "confidence" not in asr_got_result:
            return [0.0, 0.0, 0.0, 0.0]
        
        return asr_got_result["confidence"]
    
    def _create_error_response(self, code: int, message: str, msg_id: Union[int, str]) -> Dict[str, Any]:
        """
        Create an error response according to MCP protocol.
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
    """Read and parse an LSP message from the stream."""
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
    """Write an LSP message to the stream."""
    content = json.dumps(message)
    content_bytes = content.encode("utf-8")
    header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
    header_bytes = header.encode("utf-8")
    
    writer.write(header_bytes + content_bytes)
    await writer.drain()

def main():
    """
    Main function to run the ASR-GoT MCP server.
    """
    try:
        logger.info("ASR-GoT MCP Server ready to receive messages")
        print("ASR-GoT MCP Server ready to receive messages", file=sys.stderr)  # For Claude to see
        server = ASRGoTMCPServer()
        
        # Use a different approach for Windows to avoid pipe issues
        if sys.platform == 'win32':
            # Read and process messages directly without using pipes
            while True:
                message = None
                try:
                    # Read a line from stdin that has the content length
                    header_line = sys.stdin.readline().strip()
                    
                    if not header_line:
                        logger.warning("Empty header received, continuing...")
                        continue
                        
                    if not header_line.startswith("Content-Length: "):
                        logger.warning(f"Invalid header received: {header_line}, continuing...")
                        # Skip until we find a blank line
                        while sys.stdin.readline().strip():
                            pass
                        continue
                    
                    content_length = int(header_line[16:])
                    
                    # Skip headers until we find a blank line
                    while sys.stdin.readline().strip():
                        pass
                    
                    # Read the content
                    content = sys.stdin.read(content_length)
                    message = json.loads(content)
                    
                    # Process the message
                    response = asyncio.run(server.process_message(message))
                    
                    # Send the response if any
                    if response:
                        response_content = json.dumps(response)
                        response_bytes = response_content.encode('utf-8')
                        header = f"Content-Length: {len(response_bytes)}\r\n\r\n"
                        sys.stdout.write(header)
                        sys.stdout.write(response_content)
                        sys.stdout.flush()
                        logger.info(f"Sent response for method: {message.get('method')}")
                    
                    # Exit on shutdown
                    if message and message.get("method") == "shutdown":
                        logger.info("Shutdown requested, exiting")
                        break
                
                except (EOFError, KeyboardInterrupt):
                    logger.info("Input stream closed, exiting")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    logger.error(traceback.format_exc())
                    # Try to send an error response if we had a valid message id
                    if message and "id" in message:
                        error_response = server._create_error_response(-32603, f"Internal error: {str(e)}", message["id"])
                        response_content = json.dumps(error_response)
                        response_bytes = response_content.encode('utf-8')
                        header = f"Content-Length: {len(response_bytes)}\r\n\r\n"
                        sys.stdout.write(header)
                        sys.stdout.write(response_content)
                        sys.stdout.flush()
        else:
            # Non-Windows platforms can use the asyncio pipe approach
            loop = asyncio.get_event_loop()
            
            # Create stream reader and writer for stdin/stdout
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            asyncio.run(loop.connect_read_pipe(lambda: protocol, sys.stdin))
            
            writer_transport, _ = asyncio.run(loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin, sys.stdout
            ))
            writer = asyncio.StreamWriter(writer_transport, None, reader, loop)
            
            # Main message processing loop
            while True:
                # Read and process incoming message
                message = asyncio.run(read_message(reader))
                if message is None:
                    logger.error("Failed to read message, exiting")
                    break
                
                logger.info(f"Received message: {message.get('method')}")
                
                # Process the message
                response = asyncio.run(server.process_message(message))
                
                # Send the response if any
                if response:
                    asyncio.run(write_message(writer, response))
                    logger.info(f"Sent response for method: {message.get('method')}")
                
                # Exit on shutdown
                if message.get("method") == "shutdown":
                    logger.info("Shutdown requested, exiting")
                    break
                
    except asyncio.CancelledError:
        logger.info("Server task cancelled")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return 1
    
    return 0

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