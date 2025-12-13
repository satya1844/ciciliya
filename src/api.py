import os
import asyncio
import json
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging

# Load environment variables before other imports
load_dotenv()

# Import your existing RAG pipeline
from .pipelines.chat_pipeline import run_rag, run_rag_stream

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models for API ---

class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's question", min_length=1)
    max_sources: int = Field(3, description="Maximum number of sources to return", ge=1, le=10)
    stream: bool = Field(False, description="Whether to stream the response")

class Source(BaseModel):
    url: str
    title: str
    snippet: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    query: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# --- FastAPI Application ---

app = FastAPI(
    title="Real-Time Browsing Chatbot API",
    description="API for a chatbot that can browse the web in real-time to answer questions using RAG.",
    version="1.0.0",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/", tags=["Status"])
async def read_root():
    """Root endpoint to check if the API is running."""
    return {
        "status": "running",
        "service": "Real-Time Browsing Chatbot API",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Status"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.post("/api/query", response_model=QueryResponse, tags=["Chat"])
async def query_endpoint(request: QueryRequest):
    """
    Receives a user query, performs a RAG pipeline, and returns the answer with sources.
    
    Args:
        request: QueryRequest containing the user's question and parameters
        
    Returns:
        QueryResponse with the answer and relevant sources
    """
    try:
        logger.info(f"Received query: {request.query}")
        
        result = await run_rag(
            query=request.query,
            max_results=request.max_sources
        )

        if not result.get("success"):
            message = result.get("error", "Unknown pipeline failure.")
            logger.error(f"Pipeline failed: {message}")
            raise HTTPException(status_code=502, detail=message)

        formatted_sources = [
            Source(
                url=source.get("url", ""),
                title=source.get("title", "Untitled"),
                snippet=source.get("snippet"),
            )
            for source in result.get("sources", [])
        ]

        response = QueryResponse(
            answer=result.get("answer", "Sorry, I couldn't find an answer."),
            sources=formatted_sources,
            query=request.query
        )

        logger.info(f"Query processed successfully. Sources: {len(formatted_sources)}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your query: {str(e)}"
        )

@app.post("/api/stream", tags=["Chat"])
async def stream_endpoint(request: QueryRequest):
    """
    Streams the answer token by token for a real-time chat experience.
    
    Args:
        request: QueryRequest containing the user's question and parameters
        
    Returns:
        Server-Sent Events stream with answer tokens and sources
    """
    async def event_generator():
        try:
            logger.info(f"Starting stream for query: {request.query}")
            
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'query': request.query})}\n\n"
            
            async for event in run_rag_stream(
                query=request.query,
                max_results=request.max_sources
            ):
                payload = {"type": event.get("type")}
                if event.get("type") == "token":
                    payload["content"] = event.get("data", "")
                elif event.get("type") == "sources":
                    payload["sources"] = event.get("data", [])
                elif event.get("type") == "error":
                    payload["error"] = event.get("data", "")

                yield f"data: {json.dumps(payload)}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            logger.info("Stream completed successfully")
            
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return {
        "error": "Not Found",
        "detail": "The requested endpoint does not exist"
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return {
        "error": "Internal Server Error",
        "detail": "An unexpected error occurred. Please try again later."
    }

# To run this API, use:
# uvicorn src.api:app --reload --host 0.0.0.0 --port 8000