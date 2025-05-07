#!/usr/bin/env node

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

// Configure logging
const LOG_DIR = path.join(__dirname, 'logs');
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}
const LOG_FILE = path.join(LOG_DIR, 'mcp_server.log');

// Clear log file on startup
fs.writeFileSync(LOG_FILE, '');

const log = (message) => {
  const timestamp = new Date().toISOString();
  const logMessage = `${timestamp} - ${message}\n`;
  fs.appendFileSync(LOG_FILE, logMessage);
  console.error(logMessage.trim()); // Log to stderr for Claude to capture
};

// ASR-GoT API settings
const ASR_GOT_API_URL = 'http://localhost:8082/api/v1/claude/query';
const HEALTH_CHECK_URL = 'http://localhost:8082/health';

// Global state
let initialized = false;
let sessionId = null;
let dockerProcess = null;

// Setup stdin/stdout for JSON-RPC
const stdinChunks = [];
process.stdin.on('data', (chunk) => {
  stdinChunks.push(chunk);
  onStdinData();
});

process.on('SIGINT', async () => {
  log('Received SIGINT signal, shutting down');
  await stopDockerContainers();
  process.exit(0);
});

// Start Docker containers if needed
async function startDockerContainers() {
  try {
    // Check if ASR-GoT is already running
    const isRunning = await checkASRGotRunning();
    if (isRunning) {
      log('ASR-GoT server is already running');
      return true;
    }

    // Get the project directory
    const projectDir = path.resolve(__dirname, '..');
    log(`Starting Docker containers in ${projectDir}...`);
    
    // Start containers in detached mode
    const process = spawn('docker-compose', ['up', '-d'], { 
      cwd: projectDir,
      shell: true 
    });
    
    // Wait for server to be available
    for (let i = 0; i < 10; i++) {
      log(`Waiting for ASR-GoT server to start (${i+1}/10)...`);
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const isRunning = await checkASRGotRunning();
      if (isRunning) {
        log('ASR-GoT server is now running!');
        return true;
      }
    }
    
    log('Failed to start ASR-GoT server after multiple attempts');
    return false;
  } catch (error) {
    log(`Error starting Docker containers: ${error.message}`);
    return false;
  }
}

// Stop Docker containers
async function stopDockerContainers() {
  try {
    const projectDir = path.resolve(__dirname, '..');
    log(`Stopping Docker containers in ${projectDir}...`);
    
    execSync('docker-compose down', {
      cwd: projectDir,
      stdio: 'ignore'
    });
    
    log('Docker containers stopped successfully');
  } catch (error) {
    log(`Error stopping Docker containers: ${error.message}`);
  }
}

// Check if ASR-GoT server is running
async function checkASRGotRunning() {
  try {
    return new Promise((resolve) => {
      const req = http.get(HEALTH_CHECK_URL, { timeout: 2000 }, (res) => {
        resolve(res.statusCode === 200);
      });
      
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  } catch (error) {
    log(`Error checking ASR-GoT server: ${error.message}`);
    return false;
  }
}

// Simple HTTP request to ASR-GoT API
function makeRequest(url, data) {
  return new Promise((resolve, reject) => {
    const jsonData = JSON.stringify(data);
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(jsonData)
      },
      timeout: 60000
    };
    
    const req = http.request(url, options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(responseData));
          } catch (error) {
            reject(new Error(`Failed to parse response: ${error.message}`));
          }
        } else {
          reject(new Error(`Request failed with status code ${res.statusCode}`));
        }
      });
    });
    
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timed out'));
    });
    
    req.write(jsonData);
    req.end();
  });
}

// Extract reasoning trace from ASR-GoT result
function extractReasoningTrace(asrGotResult) {
  if (!asrGotResult || !asrGotResult.reasoning_trace) {
    return 'No reasoning trace available.';
  }
  
  const trace = asrGotResult.reasoning_trace;
  const formattedTrace = [];
  
  for (const stage of trace) {
    const stageName = stage.name || 'Unknown Stage';
    const stageNumber = stage.stage || '?';
    const summary = stage.summary || 'No summary available.';
    
    formattedTrace.push(`Stage ${stageNumber}: ${stageName}\n${summary}\n`);
  }
  
  return formattedTrace.join('\n');
}

// Handle initialize request
async function handleInitialize(params, id) {
  log(`Handling initialize request with id: ${id}`);
  
  // Just respond immediately to prevent timeout
  const response = {
    jsonrpc: '2.0',
    id,
    result: {
      capabilities: {
        contextCapabilities: {
          defaultContext: {
            schema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'The research query to analyze using ASR-GoT'
                }
              },
              required: ['query']
            },
            exampleValue: {
              query: 'What is the relationship between autophagy and neurodegenerative diseases?'
            }
          }
        }
      },
      serverInfo: {
        name: 'asr-got-mcp-server',
        version: '1.0.0'
      }
    }
  };
  
  // Start Docker containers in the background
  startDockerContainers().then(success => {
    initialized = success;
    log(`Docker containers ${success ? 'started' : 'failed to start'}`);
  });
  
  return response;
}

// Handle ASR-GoT query request
async function handleAsrGotQuery(params, id) {
  log(`Handling ASR-GoT query with id: ${id}`);
  
  if (!initialized) {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32002,
        message: 'Server not initialized'
      }
    };
  }
  
  const context = params.context || {};
  const query = context.query;
  
  if (!query) {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32602,
        message: 'Missing query in context'
      }
    };
  }
  
  try {
    // Prepare request
    const requestData = {
      query,
      process_response: true
    };
    
    // Send request to ASR-GoT API
    const asrGotResponse = await makeRequest(ASR_GOT_API_URL, requestData);
    
    // Extract response
    let claudeResponse = '';
    if (asrGotResponse.choices && 
        asrGotResponse.choices.length > 0 && 
        asrGotResponse.choices[0].message) {
      claudeResponse = asrGotResponse.choices[0].message.content || '';
    }
    
    // Extract ASR-GoT result
    const asrGotResult = asrGotResponse.asr_got_result || {};
    
    // Update session ID
    if (asrGotResponse.session_id) {
      sessionId = asrGotResponse.session_id;
    }
    
    // Construct MCP response
    return {
      jsonrpc: '2.0',
      id,
      result: {
        response: claudeResponse,
        reasoningTrace: extractReasoningTrace(asrGotResult),
        confidence: asrGotResult.confidence || [0.0, 0.0, 0.0, 0.0],
        sessionId
      }
    };
    
  } catch (error) {
    log(`Error processing query: ${error.message}`);
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32603,
        message: `Error communicating with ASR-GoT server: ${error.message}`
      }
    };
  }
}

// Handle shutdown request
async function handleShutdown(params, id) {
  log(`Handling shutdown request with id: ${id}`);
  
  // Stop Docker containers
  stopDockerContainers().catch(error => 
    log(`Error stopping containers: ${error.message}`)
  );
  
  initialized = false;
  
  return {
    jsonrpc: '2.0',
    id,
    result: null
  };
}

// Process MCP message
async function processMessage(message) {
  try {
    const { id, method, params } = message;
    
    log(`Processing message: method=${method}, id=${id}`);
    
    switch (method) {
      case 'initialize':
        return await handleInitialize(params, id);
      case 'shutdown':
        return await handleShutdown(params, id);
      case 'asr_got.query':
        return await handleAsrGotQuery(params, id);
      case 'notifications/cancelled':
        log(`Received cancellation notification`);
        return null;
      default:
        log(`Unknown method: ${method}`);
        return {
          jsonrpc: '2.0',
          id,
          error: {
            code: -32601,
            message: `Method not found: ${method}`
          }
        };
    }
  } catch (error) {
    log(`Error processing message: ${error.message}`);
    return {
      jsonrpc: '2.0',
      id: message.id || 0,
      error: {
        code: -32603,
        message: `Internal error: ${error.message}`
      }
    };
  }
}

// Simpler message handling
let buffer = '';
let contentLength = -1;

function onStdinData() {
  // Join all chunks
  buffer += Buffer.concat(stdinChunks).toString();
  stdinChunks.length = 0;
  
  let headerMatch;
  while (buffer.length > 0) {
    if (contentLength < 0) {
      // No content length determined yet, so look for it
      headerMatch = buffer.match(/Content-Length: (\d+)\r\n\r\n/);
      if (!headerMatch) {
        // Wait for more data
        return;
      }
      
      contentLength = parseInt(headerMatch[1], 10);
      buffer = buffer.substring(headerMatch.index + headerMatch[0].length);
    }
    
    // Check if we have enough data
    if (buffer.length < contentLength) {
      // Wait for more data
      return;
    }
    
    // Extract the message
    const messageJson = buffer.substring(0, contentLength);
    buffer = buffer.substring(contentLength);
    contentLength = -1;
    
    try {
      // Parse and process the message
      const message = JSON.parse(messageJson);
      
      processMessage(message).then(response => {
        if (response) {
          const responseJson = JSON.stringify(response);
          const responseLength = Buffer.byteLength(responseJson, 'utf8');
          
          process.stdout.write(`Content-Length: ${responseLength}\r\n\r\n${responseJson}`);
          log(`Sent response for method: ${message.method}`);
        }
      }).catch(error => {
        log(`Error processing message: ${error.message}`);
      });
    } catch (error) {
      log(`Error parsing message: ${error.message}`);
    }
  }
}

// Start with a log message
log('ASR-GoT MCP Server started');