# ASR-GoT MCP Server - Claude Desktop Integration

This document explains how to integrate the Advanced Scientific Reasoning Graph-of-Thoughts (ASR-GoT) MCP Server with Claude Desktop.

## Overview

The ASR-GoT MCP Server provides Claude Desktop with advanced reasoning capabilities through a Graph-of-Thoughts approach. It implements the Model Context Protocol (MCP) specification and offers tools for complex problem-solving and scientific reasoning.

## Features

- **Advanced Scientific Reasoning**: 8-stage reasoning pipeline for complex problem analysis
- **Graph-based Thinking**: Visual representation of reasoning processes
- **Session Management**: Maintain reasoning context across conversations
- **Confidence Tracking**: Multi-dimensional confidence assessment
- **Interdisciplinary Analysis**: Cross-domain reasoning capabilities

## Quick Setup

### Automatic Setup (Recommended)

1. **Run the setup script:**
   ```bash
   python setup_claude_desktop.py
   ```

2. **Restart Claude Desktop**

3. **Test the integration:**
   Ask Claude: "Use the ASR-GoT tool to analyze this problem: What are the implications of quantum computing on cryptography?"

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Find your Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. **Add the MCP server configuration:**
   ```json
   {
     "mcpServers": {
       "asr-got": {
         "command": "python",
         "args": ["path/to/Graph-of-Thought-MCP/mcp-wrapper/mcp_server.py"],
         "cwd": "path/to/Graph-of-Thought-MCP",
         "env": {
           "PYTHONPATH": "path/to/Graph-of-Thought-MCP/src"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop**

## Available Tools

### 1. ASR-GoT Query Tool

**Name**: `asr_got_query`

**Description**: Process complex queries using the 8-stage ASR-GoT reasoning framework.

**Parameters**:
- `query` (required): The question or problem to analyze
- `context` (optional): Additional context including domain, complexity level, session ID
- `options` (optional): Processing options like max nodes, confidence threshold

**Example Usage**:
```
Use the ASR-GoT tool to analyze: "How might climate change affect global food security in the next 50 years?"
```

### 2. Graph State Tool

**Name**: `get_graph_state`

**Description**: Retrieve the current state of a reasoning graph from a previous session.

**Parameters**:
- `session_id` (required): The session ID of the graph to retrieve

**Example Usage**:
```
Get the graph state for session: abc123-def456-ghi789
```

## How It Works

### The 8-Stage ASR-GoT Process

1. **Initialization**: Problem scoping and setup
2. **Decomposition**: Breaking down complex problems
3. **Hypothesis Generation**: Creating potential solutions
4. **Evidence Integration**: Gathering and analyzing evidence
5. **Pruning/Merging**: Refining the reasoning graph
6. **Subgraph Extraction**: Identifying key reasoning paths
7. **Composition**: Synthesizing results
8. **Reflection**: Final validation and confidence assessment

### Graph Structure

The reasoning process creates a graph with:
- **Nodes**: Representing concepts, hypotheses, and evidence
- **Edges**: Showing relationships and dependencies
- **Layers**: Organizing information by abstraction level
- **Confidence Scores**: Multi-dimensional assessment of reliability

## Troubleshooting

### Common Issues

1. **"Tool not found" error**:
   - Ensure Claude Desktop has been restarted after configuration
   - Check that the configuration file path is correct
   - Verify Python dependencies are installed

2. **Import errors**:
   - Check that PYTHONPATH is set correctly in the configuration
   - Ensure all dependencies from requirements.txt are installed
   - Verify the working directory (cwd) is set to the project root

3. **Server startup issues**:
   - Check the MCP server logs in `mcp-wrapper/logs/mcp_server.log`
   - Ensure Python 3.7+ is installed
   - Verify file permissions on the mcp_server.py script

### Debug Mode

To enable debug logging, modify the configuration:
```json
{
  "mcpServers": {
    "asr-got": {
      "command": "python",
      "args": ["mcp-wrapper/mcp_server.py"],
      "cwd": ".",
      "env": {
        "PYTHONPATH": "src",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Example Conversations

### Scientific Analysis
```
User: Use the ASR-GoT tool to analyze the potential impacts of CRISPR gene editing on human evolution.

Claude: I'll use the ASR-GoT tool to provide a comprehensive analysis of this complex topic.

[Tool execution shows detailed 8-stage reasoning process with confidence scores and graph visualization]
```

### Complex Problem Solving
```
User: How can we design sustainable cities for 2050? Use ASR-GoT to explore this.

Claude: Let me apply the ASR-GoT framework to analyze sustainable city design for 2050.

[Tool shows interdisciplinary analysis covering urban planning, technology, environment, and social factors]
```

## Advanced Configuration

### Custom Parameters

You can customize the ASR-GoT behavior by modifying the tool calls:

```json
{
  "query": "Your complex question here",
  "context": {
    "domain": "environmental_science",
    "complexity": "high"
  },
  "options": {
    "max_nodes": 30,
    "confidence_threshold": 0.8,
    "include_reasoning_trace": true,
    "include_graph_state": true
  }
}
```

### Session Continuity

To continue a previous reasoning session:

```json
{
  "query": "Continue the analysis with new evidence...",
  "context": {
    "session_id": "previous-session-id"
  }
}
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the MCP server logs
3. Ensure all dependencies are properly installed
4. Verify the Claude Desktop configuration is correct

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
