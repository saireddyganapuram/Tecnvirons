"""
Database models and helper functions for Supabase operations.

This module provides async functions for all database operations including:
- Creating and managing sessions
- Inserting events (user messages, AI responses, tool calls)
- Fetching conversation history
- Updating session summaries
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.db import get_supabase_client


async def create_session(session_id: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """
    Create a new session in the database.
    
    Args:
        session_id: Unique identifier for the session
        user_id: User identifier (defaults to "anonymous")
    
    Returns:
        Dict containing the created session data
    
    Raises:
        Exception: If session creation fails
    """
    try:
        supabase = get_supabase_client()
        
        # Run the blocking Supabase call in a thread pool to keep it async
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: supabase.table("sessions").insert({
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.utcnow().isoformat()
            }).execute()
        )
        
        return result.data[0] if result.data else {}
    
    except Exception as e:
        print(f"Error creating session: {e}")
        raise


async def insert_event(
    session_id: str,
    role: str,
    content: str
) -> Dict[str, Any]:
    """
    Insert an event (message) into the database.
    
    Args:
        session_id: Session identifier
        role: Role of the message sender ("user", "assistant", or "tool")
        content: Message content
    
    Returns:
        Dict containing the created event data
    
    Raises:
        Exception: If event insertion fails
    """
    try:
        supabase = get_supabase_client()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: supabase.table("events").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
        )
        
        return result.data[0] if result.data else {}
    
    except Exception as e:
        print(f"Error inserting event: {e}")
        raise


async def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all events for a given session, ordered by timestamp.
    
    Args:
        session_id: Session identifier
    
    Returns:
        List of event dictionaries containing role, content, and timestamp
    
    Raises:
        Exception: If fetching history fails
    """
    try:
        supabase = get_supabase_client()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: supabase.table("events")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("timestamp")\
                .execute()
        )
        
        return result.data if result.data else []
    
    except Exception as e:
        print(f"Error fetching session history: {e}")
        raise


async def update_session_summary(
    session_id: str,
    summary: str,
    duration: int
) -> Dict[str, Any]:
    """
    Update session with end time, duration, and summary.
    
    Args:
        session_id: Session identifier
        summary: Generated summary of the conversation
        duration: Session duration in seconds
    
    Returns:
        Dict containing the updated session data
    
    Raises:
        Exception: If update fails
    """
    try:
        supabase = get_supabase_client()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: supabase.table("sessions")\
                .update({
                    "end_time": datetime.utcnow().isoformat(),
                    "duration": duration,
                    "final_summary": summary
                })\
                .eq("session_id", session_id)\
                .execute()
        )
        
        return result.data[0] if result.data else {}
    
    except Exception as e:
        print(f"Error updating session summary: {e}")
        raise


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch session data by session_id.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Dict containing session data or None if not found
    """
    try:
        supabase = get_supabase_client()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: supabase.table("sessions")\
                .select("*")\
                .eq("session_id", session_id)\
                .execute()
        )
        
        return result.data[0] if result.data else None
    
    except Exception as e:
        print(f"Error fetching session: {e}")
        return None
