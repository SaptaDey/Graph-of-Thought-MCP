#!/usr/bin/env python3
"""
Verify that the MCP server fixes are working correctly.
"""

import json
import subprocess
import sys
import time

def test_server_startup_speed():
    """Test that the server starts quickly."""
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
    """Test that tools are listed correctly."""
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

def test_query_timeout():
    """Test that query processing handles timeouts correctly."""
    print("\nTesting query timeout handling...")

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

        # Send initialize message
        message_json = json.dumps(init_message)
        message_with_header = f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"
        process.stdin.write(message_with_header)
        process.stdin.flush()

        # Read response (discard)
        response_line = process.stdout.readline()
        while response_line.strip():
            response_line = process.stdout.readline()
        content_length = int(response_line.strip().split(": ")[1])
        process.stdout.read(content_length)

        # Send a query with a very short timeout
        query_message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "asr_got_query",
                "arguments": {
                    "query": "Analyze the complete history of quantum physics and its implications for the future of computing",
                    "options": {
                        "timeout": 3  # Very short timeout to trigger the timeout handler
                    }
                }
            },
            "id": 2
        }

        message_json = json.dumps(query_message)
        message_with_header = f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"

        start_time = time.time()
        process.stdin.write(message_with_header)
        process.stdin.flush()

        # Read response headers
        response_line = process.stdout.readline()
        while response_line.strip():
            response_line = process.stdout.readline()

        # Read content length
        content_length_line = process.stdout.readline().strip()
        if not content_length_line.startswith("Content-Length: "):
            print("❌ Invalid response format")
            return False

        content_length = int(content_length_line.split(": ")[1])

        # Skip empty line
        process.stdout.readline()

        # Read response content
        response_content = process.stdout.read(content_length)
        end_time = time.time()

        response = json.loads(response_content)
        elapsed_time = end_time - start_time

        # Check if response was received within a reasonable time
        if elapsed_time < 10:  # Should respond within 10 seconds even with timeout
            print(f"✅ Received response in {elapsed_time:.2f} seconds")
        else:
            print(f"❌ Response took too long: {elapsed_time:.2f} seconds")
            return False

        # Check if it's a timeout error
        if "result" in response and "isError" in response["result"]:
            if response["result"]["isError"]:
                content = response["result"]["content"][0]["text"]
                if "timed out" in content.lower():
                    print("✅ Correctly received timeout error message")
                    print(f"   Message: {content}")
                    return True
                else:
                    print(f"❌ Received error but not a timeout: {content}")
                    return False
            else:
                print("❓ Query completed successfully (unexpected for such a complex query with short timeout)")
                return False
        else:
            print("❌ Unexpected response format")
            return False

    except Exception as e:
        print(f"❌ Error testing query timeout: {e}")
        process.kill()
        return False
    finally:
        # Shutdown
        try:
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
            process.wait(timeout=5)
        except:
            process.kill()

def main():
    """Run all tests."""
    print("🧠 ASR-GoT MCP Server Fix Verification")
    print("=" * 50)

    startup_ok = test_server_startup_speed()
    tools_ok = test_tools_listing()
    timeout_ok = test_query_timeout()

    print("\n" + "=" * 50)
    if startup_ok and tools_ok and timeout_ok:
        print("✅ ALL TESTS PASSED!")
        print("\nThe MCP server is working correctly with all fixes:")
        print("- Fast startup ✓")
        print("- Tools listing ✓")
        print("- Query timeout handling ✓")
        print("\nNext steps:")
        print("1. Completely quit Claude Desktop (Cmd+Q)")
        print("2. Wait 5 seconds")
        print("3. Restart Claude Desktop")
        print("4. The ASR-GoT tools should now work without timeout issues")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the error messages above.")

    return 0 if (startup_ok and tools_ok and timeout_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
