#!/usr/bin/env python3
"""
Quick test script for the ASR-GoT MCP server.
"""

import json
import subprocess
import sys
import time

def test_mcp_server():
    """Test the MCP server with a simple initialize message."""
    
    # Start the MCP server
    print("Starting MCP server...")
    process = subprocess.Popen(
        [sys.executable, "mcp-wrapper/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it a moment to start
    time.sleep(1)
    
    # Send initialize message
    init_message = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        },
        "id": 1
    }
    
    message_json = json.dumps(init_message)
    message_with_header = f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"
    
    print(f"Sending message: {message_with_header}")
    
    try:
        # Send the message
        process.stdin.write(message_with_header)
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Read response
        stdout, stderr = process.communicate(timeout=5)
        
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        print(f"Return code: {process.returncode}")
        
    except subprocess.TimeoutExpired:
        print("Server response timed out")
        process.kill()
        stdout, stderr = process.communicate()
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
    
    except Exception as e:
        print(f"Error: {e}")
        process.kill()

if __name__ == "__main__":
    test_mcp_server()
