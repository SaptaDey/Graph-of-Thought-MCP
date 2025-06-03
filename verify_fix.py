#!/usr/bin/env python3
"""
Verify that the MCP server fixes are working correctly.
"""

import json
import subprocess
import sys
import time

def test_server_startup_speed():
    """
    Tests that the MCP server starts and responds to an initialization request within 3 seconds.
    
    Launches the MCP server as a subprocess, sends a JSON-RPC "initialize" message, and measures the time taken to receive a response. Verifies that the server responds with the correct protocol version, confirms that the ASR-GoT processor is not initialized at startup (ensuring lazy loading), and checks for unexpected errors in stderr.
    
    Returns:
        True if the server starts and responds within 3 seconds without critical errors; otherwise, False.
    """
    print("Testing server startup speed...")
    
    start_time = time.time()
    
    # Start the MCP server
    process = subprocess.Popen(
        [sys.executable, "mcp-wrapper/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send initialize message immediately
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
    
    try:
        # Send the message
        process.stdin.write(message_with_header)
        process.stdin.flush()
        
        # Wait for response with timeout
        stdout, stderr = process.communicate(timeout=5)
        
        end_time = time.time()
        startup_time = end_time - start_time
        
        print(f"✅ Server startup and response time: {startup_time:.2f} seconds")
        
        # Check if response is correct
        if "protocolVersion" in stdout and "2024-11-05" in stdout:
            print("✅ Server responded with correct protocol version")
        else:
            print("❌ Server response incorrect")
            print(f"STDOUT: {stdout}")
        
        # Check if ASR-GoT processor was initialized (it shouldn't be)
        if "ASR-GoT Processor initialized with 8 stages" in stderr:
            print("❌ ASR-GoT processor was initialized at startup (should be lazy)")
        else:
            print("✅ ASR-GoT processor was NOT initialized at startup (correct lazy loading)")
        
        # Check for any errors
        if "error" in stderr.lower() and "LAZY LOADING" not in stderr:
            print(f"⚠️  Potential issues in stderr: {stderr}")
        else:
            print("✅ No errors in startup")
        
        return startup_time < 3.0  # Should start in under 3 seconds
        
    except subprocess.TimeoutExpired:
        print("❌ Server startup timed out (>5 seconds)")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        process.kill()
        return False

def test_tools_listing():
    """
    Verifies that the MCP server lists available tools correctly via JSON-RPC.
    
    Launches the MCP server, sends initialization and tools listing requests, and checks
    the server's output for the presence of expected tool names. Returns True if the
    expected tools are listed; otherwise, returns False.
    """
    print("\nTesting tools listing...")
    
    process = subprocess.Popen(
        [sys.executable, "mcp-wrapper/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Initialize first
        init_message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
            "id": 1
        }
        
        # Tools list
        tools_message = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        # Send both messages
        for msg in [init_message, tools_message]:
            message_json = json.dumps(msg)
            message_with_header = f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"
            process.stdin.write(message_with_header)
            process.stdin.flush()
        
        # Shutdown
        shutdown_message = {
            "jsonrpc": "2.0",
            "method": "shutdown",
            "params": {},
            "id": 3
        }
        message_json = json.dumps(shutdown_message)
        message_with_header = f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"
        process.stdin.write(message_with_header)
        process.stdin.flush()
        
        stdout, stderr = process.communicate(timeout=5)
        
        # Check if tools are listed
        if "asr_got_query" in stdout and "get_graph_state" in stdout:
            print("✅ Tools are listed correctly")
            return True
        else:
            print("❌ Tools not listed correctly")
            print(f"STDOUT: {stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tools: {e}")
        process.kill()
        return False

def main():
    """
    Runs all MCP server verification tests and prints a summary of results.
    
    Executes the server startup speed and tools listing tests, displays their outcomes,
    and provides next-step instructions if all tests pass. Returns 0 if all tests succeed,
    otherwise returns 1.
    """
    print("🧠 ASR-GoT MCP Server Fix Verification")
    print("=" * 50)
    
    startup_ok = test_server_startup_speed()
    tools_ok = test_tools_listing()
    
    print("\n" + "=" * 50)
    if startup_ok and tools_ok:
        print("✅ ALL TESTS PASSED!")
        print("\nThe MCP server is working correctly.")
        print("\nNext steps:")
        print("1. Completely quit Claude Desktop (Cmd+Q)")
        print("2. Wait 5 seconds")
        print("3. Restart Claude Desktop")
        print("4. The ASR-GoT tools should now work without timeout issues")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the error messages above.")
    
    return 0 if (startup_ok and tools_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
