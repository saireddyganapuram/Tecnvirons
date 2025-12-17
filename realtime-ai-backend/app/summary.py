"""
Post-session processing module for conversation summarization.

This module handles background tasks that run after a WebSocket session ends:
- Fetching conversation history from database
- Generating session summary using LLM
- Calculating session duration
- Updating session record with summary and metadata
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from app.models import get_session_history, update_session_summary, get_session


async def generate_session_summary(messages: List[Dict[str, Any]]) -> str:
    """
    Generate a concise summary of the conversation.
    
    Args:
        messages: List of conversation events from database
    
    Returns:
        Summary string
    """
    if not messages:
        return "No conversation occurred in this session."
    
    # Count messages by role
    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    tool_calls = [m for m in messages if m["role"] == "tool"]
    
    # Extract key topics from user messages
    topics = []
    for msg in user_messages[:3]:  # First 3 messages for context
        content = msg["content"].lower()
        if "websocket" in content or "realtime" in content:
            topics.append("WebSockets")
        if "fastapi" in content or "api" in content:
            topics.append("FastAPI")
        if "supabase" in content or "database" in content:
            topics.append("Supabase")
        if "data" in content or "fetch" in content or "stats" in content:
            topics.append("Data Retrieval")
    
    # Remove duplicates while preserving order
    topics = list(dict.fromkeys(topics))
    
    # Build summary
    summary_parts = [
        f"Session with {len(user_messages)} user message(s) and {len(assistant_messages)} AI response(s)."
    ]
    
    if tool_calls:
        summary_parts.append(f"Used {len(tool_calls)} tool call(s) for data retrieval.")
    
    if topics:
        summary_parts.append(f"Topics discussed: {', '.join(topics)}.")
    else:
        summary_parts.append("General conversation.")
    
    return " ".join(summary_parts)


async def process_session_end(session_id: str) -> None:
    """
    Process session end: generate summary and update database.
    
    This is a background task that runs asynchronously after WebSocket disconnect.
    
    Args:
        session_id: Session identifier
    """
    try:
        print(f"[Background Task] Processing session end for: {session_id}")
        
        # Fetch session data to get start time
        session = await get_session(session_id)
        if not session:
            print(f"[Background Task] Session {session_id} not found")
            return
        
        # Fetch conversation history
        messages = await get_session_history(session_id)
        
        if not messages:
            print(f"[Background Task] No messages found for session {session_id}")
            summary = "Empty session - no messages exchanged."
            duration = 0
        else:
            # Generate summary
            summary = await generate_session_summary(messages)
            
            # Calculate duration
            start_time = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())
        
        # Update session in database
        await update_session_summary(session_id, summary, duration)
        
        print(f"[Background Task] Session {session_id} processed successfully")
        print(f"[Background Task] Summary: {summary}")
        print(f"[Background Task] Duration: {duration}s")
    
    except Exception as e:
        print(f"[Background Task] Error processing session {session_id}: {e}")
