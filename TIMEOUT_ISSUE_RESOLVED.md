# ASR-GoT MCP Server - Timeout Issue RESOLVED ✅

## Problem Summary
The ASR-GoT MCP Server was experiencing timeout issues when connecting to Claude Desktop:
- Server took 60+ seconds to initialize
- Claude Desktop would timeout after 60 seconds
- Connection would fail with "Request timed out" errors

## Root Cause
The server was importing and initializing heavy ASR-GoT modules at startup, including:
- ASR-GoT processor with 8 stages
- NetworkX graph libraries
- NumPy and other scientific computing libraries

## Solution Applied

### 1. **Lazy Loading Implementation**
- Moved all heavy imports to lazy loading functions
- ASR-GoT processor only initializes when actually needed
- Server startup now takes 0.06 seconds instead of 60+ seconds

### 2. **Optimized Initialization**
- Streamlined MCP protocol handshake
- Removed unnecessary operations from startup
- Added proper notification handlers

### 3. **Configuration Fixes**
- Ensured Claude Desktop uses the correct Python server
- Updated configuration with proper paths and environment variables

## Test Results

**Before Fix:**
```
2025-05-27T04:29:29.783Z [asr-got] [info] Message from client: {"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":0,"reason":"Error: MCP error -32001: Request timed out"}}
```

**After Fix:**
```
🧠 ASR-GoT MCP Server Fix Verification
==================================================
✅ Server startup and response time: 0.06 seconds
✅ Server responded with correct protocol version
✅ ASR-GoT processor was NOT initialized at startup (correct lazy loading)
✅ No errors in startup
✅ Tools are listed correctly
✅ ALL TESTS PASSED!
```

## How to Apply the Fix

The fix has already been applied to your codebase. To activate it:

### 1. **Restart Claude Desktop**
```bash
# Completely quit Claude Desktop
# Press Cmd+Q or use Claude Desktop > Quit Claude Desktop

# Wait 5 seconds

# Restart Claude Desktop
# Open Claude Desktop from Applications or Spotlight
```

### 2. **Verify the Fix**
After restarting Claude Desktop, you should see:
- No timeout errors in the logs
- ASR-GoT tools available in Claude Desktop
- Fast connection establishment

### 3. **Test the Integration**
Try asking Claude Desktop:
```
Use the ASR-GoT tool to analyze this problem: What are the key challenges in developing sustainable energy solutions?
```

## Technical Details

### Files Modified:
- `mcp-wrapper/mcp_server.py` - Implemented lazy loading and optimized startup
- `setup_claude_desktop.py` - Updated configuration generation
- `config/claude_desktop_config.json` - Fixed MCP server format

### Key Changes:
1. **Lazy Import Pattern:**
   ```python
   # Before: Heavy imports at startup
   from asr_got.core import ASRGoTProcessor

   # After: Lazy loading when needed
   def _import_asr_got():
       global ASRGoTProcessor
       if ASRGoTProcessor is None:
           from asr_got.core import ASRGoTProcessor as _ASRGoTProcessor
           ASRGoTProcessor = _ASRGoTProcessor
   ```

2. **Fast Initialization:**
   ```python
   # Return MCP initialize response immediately
   # Don't load heavy modules until tools are actually called
   ```

## Current Status: ✅ RESOLVED

- **Startup Time:** 0.06 seconds (was 60+ seconds)
- **Timeout Issues:** Eliminated
- **Lazy Loading:** Working correctly
- **Tools Available:** `asr_got_query` and `get_graph_state`
- **Configuration:** Correct and verified

## Additional Improvements (May 2025 Update)

### Query Processing Timeout Handling

We've implemented additional improvements to handle timeouts during query processing:

1. **Asynchronous Query Processing:**
   - Query processing now runs in a separate thread
   - Configurable timeout prevents hanging on complex queries
   - User-friendly error messages when processing takes too long

2. **Configurable Timeout Parameter:**
   - Added `timeout` parameter to the `asr_got_query` tool schema
   - Default: 60 seconds
   - Range: 10-300 seconds (configurable by user)
   - Example usage: `Use the ASR-GoT tool with a timeout of 120 seconds to analyze...`

3. **Enhanced Error Handling:**
   - Graceful handling of timeout errors
   - Detailed logging for troubleshooting
   - Clear user feedback when queries exceed time limits

### Technical Implementation:

```python
# Run query processing in a thread pool with timeout
result = await asyncio.wait_for(
    loop.run_in_executor(None, process_query_task),
    timeout=timeout
)
```

## Next Steps

1. **Restart Claude Desktop** to activate the fix
2. **Test the ASR-GoT tools** in Claude Desktop with the new timeout parameter
3. **Enjoy fast, reliable ASR-GoT integration!**

The ASR-GoT MCP Server is now properly optimized for Claude Desktop integration and should work without any timeout issues, both during startup and during query processing.
