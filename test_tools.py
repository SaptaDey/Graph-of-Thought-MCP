#!/usr/bin/env python3
"""
Test the MCP server tools functionality.
"""

import json
import subprocess
import sys
import time

def send_message(process, message):
    """Send a message to the MCP server."""
    message_json = json.dumps(message)
    message_with_header = f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"
    
    process.stdin.write(message_with_header)
    process.stdin.flush()

def test_tools():
    """Test the MCP server tools."""
    
    # Start the MCP server
    print("Starting MCP server...")
    process = subprocess.Popen(
        [sys.executable, "mcp-wrapper/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(1)
    
    try:
        # 1. Initialize
        print("1. Testing initialization...")
        init_message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            },
            "id": 1
        }
        send_message(process, init_message)
        
        # 2. List tools
        print("2. Testing tools/list...")
        tools_message = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        send_message(process, tools_message)
        
        # 3. Send shutdown
        print("3. Sending shutdown...")
        shutdown_message = {
            "jsonrpc": "2.0",
            "method": "shutdown",
            "params": {},
            "id": 3
        }
        send_message(process, shutdown_message)
        
        # Wait for responses
        time.sleep(3)
        
        # Get output
        stdout, stderr = process.communicate(timeout=5)
        
        print("=== STDOUT ===")
        print(stdout)
        print("\n=== STDERR ===")
        print(stderr)
        print(f"\nReturn code: {process.returncode}")
        
    except Exception as e:
        print(f"Error: {e}")
        process.kill()

if __name__ == "__main__":
    test_tools()
