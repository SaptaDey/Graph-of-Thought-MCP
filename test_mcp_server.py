#!/usr/bin/env python3
"""
Test script for the ASR-GoT MCP Server.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

def send_mcp_message(process, message):
    """Send an MCP message to the process."""
    content = json.dumps(message)
    content_bytes = content.encode('utf-8')
    header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
    
    full_message = header + content
    process.stdin.write(full_message.encode('utf-8'))
    process.stdin.flush()

def read_mcp_response(process):
    """Read an MCP response from the process."""
    # Read headers
    content_length = None
    while True:
        line = process.stdout.readline().decode('utf-8')
        if not line or line.strip() == "":
            break
        if line.startswith("Content-Length: "):
            content_length = int(line[16:].strip())
    
    if content_length is None:
        return None
    
    # Read content
    content = process.stdout.read(content_length).decode('utf-8')
    return json.loads(content)

def test_mcp_server():
    """Test the MCP server functionality."""
    print("Testing ASR-GoT MCP Server...")
    
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    venv_python = current_dir / "venv" / "bin" / "python"
    mcp_server = current_dir / "mcp-wrapper" / "mcp_server.py"
    
    # Start the MCP server
    process = subprocess.Popen(
        [str(venv_python), str(mcp_server)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=current_dir
    )
    
    try:
        # Test 1: Initialize
        print("1. Testing initialize...")
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        send_mcp_message(process, init_message)
        response = read_mcp_response(process)
        
        if response and response.get("result"):
            print("✓ Initialize successful")
            print(f"  Server: {response['result']['serverInfo']['name']} v{response['result']['serverInfo']['version']}")
        else:
            print("✗ Initialize failed")
            return False
        
        # Test 2: List tools
        print("2. Testing tools/list...")
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        send_mcp_message(process, tools_message)
        response = read_mcp_response(process)
        
        if response and response.get("result") and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✓ Tools list successful - {len(tools)} tools available:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print("✗ Tools list failed")
            return False
        
        # Test 3: Simple ASR-GoT query
        print("3. Testing asr_got_query tool...")
        query_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "asr_got_query",
                "arguments": {
                    "query": "What is 2+2?",
                    "context": {"complexity": "low"},
                    "options": {"max_nodes": 5}
                }
            }
        }
        
        send_mcp_message(process, query_message)
        
        # Give it more time for processing
        time.sleep(2)
        
        response = read_mcp_response(process)
        
        if response and response.get("result"):
            print("✓ ASR-GoT query successful")
            if "content" in response["result"]:
                content = response["result"]["content"][0]["text"]
                print(f"  Response preview: {content[:100]}...")
        else:
            print("✗ ASR-GoT query failed")
            if response and "error" in response:
                print(f"  Error: {response['error']}")
            return False
        
        # Test 4: Shutdown
        print("4. Testing shutdown...")
        shutdown_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "shutdown",
            "params": {}
        }
        
        send_mcp_message(process, shutdown_message)
        response = read_mcp_response(process)
        
        if response and response.get("result") is None:
            print("✓ Shutdown successful")
        else:
            print("✗ Shutdown failed")
            return False
        
        print("\n🎉 All tests passed! MCP server is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
