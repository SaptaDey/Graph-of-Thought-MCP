#!/usr/bin/env python3
"""
Test tools/list functionality of MCP server
"""

import json
import subprocess
import sys
import os

def test_tools_list():
    """Test the tools/list functionality."""
    
    # Change to the correct directory
    os.chdir("/Users/derekvitrano/Developer/Work/tools/Graph-of-Thought-MCP")
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = "/Users/derekvitrano/Developer/Work/tools/Graph-of-Thought-MCP/src"
    env["LOG_LEVEL"] = "INFO"
    
    # Create the tools/list message
    message = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }
    
    # Convert to JSON and create proper message
    json_content = json.dumps(message)
    content_length = len(json_content.encode('utf-8'))
    full_message = f"Content-Length: {content_length}\r\n\r\n{json_content}"
    
    print(f"Testing tools/list with message:")
    print(f"Content-Length: {content_length}")
    print(f"JSON: {json_content}")
    print()
    
    try:
        # Start the MCP server
        process = subprocess.Popen(
            ["/Users/derekvitrano/Developer/Work/tools/Graph-of-Thought-MCP/venv/bin/python",
             "/Users/derekvitrano/Developer/Work/tools/Graph-of-Thought-MCP/mcp-wrapper/mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd="/Users/derekvitrano/Developer/Work/tools/Graph-of-Thought-MCP"
        )
        
        # Send the message and get response
        stdout, stderr = process.communicate(input=full_message, timeout=10)
        
        print(f"Return code: {process.returncode}")
        print(f"STDERR:\n{stderr}")
        print(f"STDOUT:\n{stdout}")
        
        # Try to parse the response
        if stdout.strip():
            lines = stdout.strip().split('\n')
            for i, line in enumerate(lines):
                if line.startswith('Content-Length:'):
                    content_length = int(line.split(':')[1].strip())
                    # The JSON should be after the empty line
                    if i + 2 < len(lines):
                        json_response = '\n'.join(lines[i+2:])
                        try:
                            response = json.loads(json_response)
                            print(f"Parsed response: {json.dumps(response, indent=2)}")
                            
                            # Check if tools are listed
                            tools = response.get("result", {}).get("tools", [])
                            print(f"\nFound {len(tools)} tools:")
                            for tool in tools:
                                print(f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                                
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse response JSON: {e}")
                            print(f"Raw JSON: {repr(json_response)}")
                    break
        
    except subprocess.TimeoutExpired:
        print("Process timed out!")
        process.kill()
        stdout, stderr = process.communicate()
        print(f"STDERR: {stderr}")
        print(f"STDOUT: {stdout}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tools_list()
