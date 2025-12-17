"""
Main FastAPI application module.

This module initializes the FastAPI application with:
- CORS middleware for cross-origin requests
- WebSocket endpoint for real-time communication
- Health check endpoints
- Error handling
- Startup and shutdown events
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.websocket import handle_websocket

# Initialize FastAPI application
app = FastAPI(
    title="Realtime AI Backend",
    description="A real-time AI backend with WebSocket streaming, LLM interaction, and Supabase persistence",
    version="1.0.0"
)

# Configure CORS middleware
# This allows the frontend to connect from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    
    Runs when the server starts. Can be used for:
    - Database connection pool initialization
    - Loading ML models
    - Starting background tasks
    """
    print("=" * 60)
    print("🚀 Realtime AI Backend Starting...")
    print("=" * 60)
    print("📡 WebSocket endpoint: ws://localhost:8000/ws/session/{session_id}")
    print("🏥 Health check: http://localhost:8000/health")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.
    
    Runs when the server shuts down. Can be used for:
    - Closing database connections
    - Saving state
    - Cleanup tasks
    """
    print("=" * 60)
    print("🛑 Realtime AI Backend Shutting Down...")
    print("=" * 60)


# ============================================================================
# HTTP ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - basic health check.
    
    Returns:
        Dict with status message
    """
    return {
        "status": "online",
        "message": "Realtime AI Backend is running",
        "websocket_endpoint": "/ws/session/{session_id}"
    }


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint.
    
    Returns:
        Dict with detailed health status
    """
    return {
        "status": "healthy",
        "service": "Realtime AI Backend",
        "version": "1.0.0",
        "features": {
            "websocket_streaming": True,
            "llm_interaction": True,
            "tool_calling": True,
            "database_persistence": True,
            "post_session_processing": True
        }
    }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time AI chat sessions.
    
    This endpoint:
    - Accepts WebSocket connections with a unique session_id
    - Receives user messages in JSON format: {"message": "text"}
    - Streams AI responses token-by-token
    - Persists all events to Supabase asynchronously
    - Maintains conversation context across multiple messages
    - Triggers post-session processing on disconnect
    
    Args:
        websocket: WebSocket connection
        session_id: Unique identifier for the session
    
    Example usage from JavaScript:
        const ws = new WebSocket('ws://localhost:8000/ws/session/my-session-123');
        ws.send(JSON.stringify({message: 'Hello!'}));
    """
    await handle_websocket(websocket, session_id)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: The request that caused the error
        exc: The exception that was raised
    
    Returns:
        Dict with error details
    """
    print(f"[Error] Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "detail": str(exc)
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    # Use --reload flag for development (auto-restart on code changes)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
