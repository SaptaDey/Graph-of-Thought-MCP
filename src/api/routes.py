from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional
from asr_got.core import ASRGoTProcessor
from api.schema import QueryRequest, QueryResponse, GraphState, ClaudeRequest
from api.claude_client import ClaudeClient

router = APIRouter(prefix="/api/v1")

# Initialize the ASR-GoT processor
processor = ASRGoTProcessor()

# Initialize the Claude client
claude_client = ClaudeClient()

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest = Body(...)):
    """Process a query using the ASR-GoT framework"""
    # Implementation as before
    
@router.get("/graph/{session_id}", response_model=GraphState)
async def get_graph_state(session_id: str):
    """Get the current graph state for a specific session"""
    # Implementation as before
    
@router.post("/feedback/{session_id}")
async def provide_feedback(session_id: str, feedback: Dict[str, Any] = Body(...)):
    """Provide feedback to refine the ASR-GoT graph"""
    # Implementation as before

@router.post("/claude/query")
async def claude_query(request: ClaudeRequest = Body(...), web_request: Request = None):
    """
    Process a query using Claude with ASR-GoT integration.
    """
    try:
        # Get the current graph state if session_id is provided
        graph_state = None
        if request.session_id:
            try:
                graph_state = processor.get_graph_state(request.session_id)
            except:
                # Create a new session if not found
                pass
        
        # Format the query for Claude with ASR-GoT context
        formatted_query = await claude_client.format_asr_got_query(
            query=request.query,
            graph_state=graph_state
        )
        
        # Query Claude
        claude_response = await claude_client.query_claude(
            message=formatted_query,
            context=request.context
        )
        
        # Check if using desktop mode
        if claude_response.get("desktop_mode", False):
            # Return the desktop mode response
            return JSONResponse(content={
                "desktop_mode": True,
                "message": claude_response.get("message", "Query sent to Claude desktop application"),
                "session_id": request.session_id
            })
        
        # Process Claude's response through ASR-GoT if needed
        if request.process_response and not claude_response.get("error"):
            # Extract the content from Claude's response
            content = claude_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Process through ASR-GoT
            result = processor.process_query(
                query=request.query,
                context={
                    "claude_response": content,
                    "original_context": request.context
                },
                parameters=request.parameters
            )
            
            # Add the processed result to the response
            claude_response["asr_got_result"] = result
            
            # Store the session ID
            claude_response["session_id"] = result.get("session_id", request.session_id)
        
        return claude_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/claude/desktop-prompt", response_class=HTMLResponse)
async def get_desktop_prompt_page():
    """
    Return a simple HTML page for working with Claude desktop application
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claude Desktop Integration</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            textarea {
                width: 100%;
                height: 200px;
                padding: 10px;
                margin-bottom: 10px;
                font-family: monospace;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            .response {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                white-space: pre-wrap;
            }
            .instructions {
                background-color: #ffffd9;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid #ffcc00;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Claude Desktop Integration</h1>
            
            <div class="instructions">
                <h3>How to use:</h3>
                <ol>
                    <li>Enter your research query in the text area below</li>
                    <li>Click "Generate Claude Prompt"</li>
                    <li>A new window will open with a formatted prompt</li>
                    <li>Copy the prompt and paste it into your Claude desktop application</li>
                    <li>After receiving Claude's response, you can copy it back here for further analysis</li>
                </ol>
            </div>
            
            <h2>Enter Your Research Query</h2>
            <textarea id="query-input" placeholder="Enter your research question or topic here..."></textarea>
            <button id="generate-btn">Generate Claude Prompt</button>
            
            <div id="result" class="response" style="display: none;"></div>
            
            <h2>Claude's Response</h2>
            <p>Paste Claude's response below for further processing:</p>
            <textarea id="claude-response" placeholder="Paste Claude's response here..."></textarea>
            <button id="process-btn">Process Response</button>
            
            <div id="processed-result" class="response" style="display: none;"></div>
        </div>
        
        <script>
            document.getElementById('generate-btn').addEventListener('click', async () => {
                const query = document.getElementById('query-input').value.trim();
                if (!query) {
                    alert('Please enter a query');
                    return;
                }
                
                try {
                    const response = await fetch('/api/v1/claude/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            query: query,
                            process_response: false
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.desktop_mode) {
                        document.getElementById('result').textContent = 'Prompt generated and opened in a new window. Copy the prompt into your Claude desktop application.';
                        document.getElementById('result').style.display = 'block';
                    } else {
                        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                        document.getElementById('result').style.display = 'block';
                    }
                } catch (error) {
                    document.getElementById('result').textContent = `Error: ${error.message}`;
                    document.getElementById('result').style.display = 'block';
                }
            });
            
            document.getElementById('process-btn').addEventListener('click', async () => {
                const claudeResponse = document.getElementById('claude-response').value.trim();
                const originalQuery = document.getElementById('query-input').value.trim();
                
                if (!claudeResponse) {
                    alert('Please paste Claude\'s response');
                    return;
                }
                
                try {
                    // This would typically call a backend endpoint to process Claude's response
                    // For now, we'll just display it
                    document.getElementById('processed-result').textContent = 
                        `Claude's response has been received (${claudeResponse.length} characters).\n\n` +
                        `To fully integrate with ASR-GoT, you would need to implement additional processing.`;
                    document.getElementById('processed-result').style.display = 'block';
                } catch (error) {
                    document.getElementById('processed-result').textContent = `Error: ${error.message}`;
                    document.getElementById('processed-result').style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)