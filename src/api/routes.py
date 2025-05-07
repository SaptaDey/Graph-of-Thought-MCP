from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, Optional
from asr_got.core import ASRGoTProcessor
from api.schema import QueryRequest, QueryResponse, GraphState, ClaudeRequest
from api.claude_client import ClaudeClient
import logging

router = APIRouter(prefix="/api/v1")

# Initialize the ASR-GoT processor
processor = ASRGoTProcessor()

# Initialize the Claude client
claude_client = ClaudeClient()

# Initialize logger
logger = logging.getLogger("asr-got-api")

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest = Body(...)):
    """Process a query using the ASR-GoT framework"""
    logger.info(f"Received query: {request.query}")
    try:
        result = processor.process_query(
            query=request.query,
            context=request.context,
            parameters=request.parameters
        )
        logger.info(f"Query processed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/{session_id}", response_model=GraphState)
async def get_graph_state(session_id: str):
    """Get the current graph state for a specific session"""
    logger.info(f"Fetching graph state for session: {session_id}")
    try:
        graph_state = processor.get_graph_state(session_id)
        logger.info(f"Graph state fetched successfully for session: {session_id}")
        return graph_state
    except Exception as e:
        logger.error(f"Error fetching graph state for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback/{session_id}")
async def provide_feedback(session_id: str, feedback: Dict[str, Any] = Body(...)):
    """Provide feedback to refine the ASR-GoT graph"""
    logger.info(f"Received feedback for session: {session_id}")
    try:
        processor.incorporate_feedback(session_id, feedback)
        logger.info(f"Feedback incorporated successfully for session: {session_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error incorporating feedback for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/claude/query")
async def claude_query(request: ClaudeRequest = Body(...)):
    """
    Process a query using Claude with ASR-GoT integration.
    """
    logger.info(f"Received Claude query: {request.query}")
    try:
        # Get the current graph state if session_id is provided
        graph_state = None
        if request.session_id:
            try:
                graph_state = processor.get_graph_state(request.session_id)
            except ValueError as e:
                logger.warning(f"Session ID {request.session_id} not found: {str(e)}")
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
        
        logger.info(f"Claude query processed successfully: {claude_response}")
        return claude_response
    except Exception as e:
        logger.error(f"Error processing Claude query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
