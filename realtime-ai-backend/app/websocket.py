"""
WebSocket session handler module.

This module manages WebSocket connections and handles real-time communication:
- Accepts WebSocket connections per session
- Receives user messages
- Streams AI responses token-by-token
- Persists all events to database asynchronously
- Maintains conversation state across multiple messages
- Triggers post-session processing on disconnect
"""

import json
import asyncio
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from app.models import create_session, insert_event
from app.llm import stream_llm_response
from app.summary import process_session_end


class ConnectionManager:
    """
    Manages WebSocket connections and conversation state.
    
    Each session maintains its own conversation history in memory
    for context management during the session.
    """
    
    def __init__(self):
        # Active connections: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Conversation history: session_id -> List[messages]
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Accept WebSocket connection and initialize session.
        
        Args:
            websocket: WebSocket connection
            session_id: Unique session identifier
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.conversation_history[session_id] = []
        
        print(f"[WebSocket] Client connected: {session_id}")
        
        # Create session in database
        try:
            await create_session(session_id)
            print(f"[Database] Session created: {session_id}")
        except Exception as e:
            print(f"[Database] Error creating session {session_id}: {e}")
    
    async def disconnect(self, session_id: str):
        """
        Handle WebSocket disconnect and cleanup.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
        
        print(f"[WebSocket] Client disconnected: {session_id}")
        
        # Trigger background task for session summary
        asyncio.create_task(process_session_end(session_id))
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of messages with role and content
        """
        return self.conversation_history.get(session_id, [])
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant/tool)
            content: Message content
        """
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "role": role,
            "content": content
        })


# Global connection manager instance
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, session_id: str):
    """
    Main WebSocket handler for a session.
    
    This function:
    1. Accepts the WebSocket connection
    2. Receives user messages
    3. Streams AI responses token-by-token
    4. Persists all events to database asynchronously
    5. Maintains conversation context
    6. Handles disconnection gracefully
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    # Connect and initialize session
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": f"Connected to session: {session_id}"
        })
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Empty message received"
                    })
                    continue
                
                print(f"[WebSocket] Received from {session_id}: {user_message}")
                
                # Add user message to conversation history
                manager.add_message(session_id, "user", user_message)
                
                # Persist user message to database (async, non-blocking)
                asyncio.create_task(insert_event(session_id, "user", user_message))
                
                # Get conversation history for context
                conversation = manager.get_conversation_history(session_id)
                
                # Stream AI response
                full_response = ""
                tool_content = ""
                
                async for chunk in stream_llm_response(conversation, session_id):
                    chunk_type = chunk["type"]
                    chunk_content = chunk["content"]
                    
                    if chunk_type == "token":
                        # Stream text token to client
                        await websocket.send_json({
                            "type": "token",
                            "content": chunk_content
                        })
                        full_response += chunk_content
                    
                    elif chunk_type == "tool_call":
                        # Send tool call notification
                        await websocket.send_json({
                            "type": "tool_call",
                            "content": chunk_content
                        })
                        tool_content += chunk_content + "\n"
                    
                    elif chunk_type == "tool_result":
                        # Send tool result
                        await websocket.send_json({
                            "type": "tool_result",
                            "content": chunk_content
                        })
                        tool_content += chunk_content + "\n"
                        
                        # Persist tool event to database
                        asyncio.create_task(
                            insert_event(session_id, "tool", chunk_content)
                        )
                    
                    elif chunk_type == "error":
                        # Send error
                        await websocket.send_json({
                            "type": "error",
                            "content": chunk_content
                        })
                
                # Send end-of-stream marker
                await websocket.send_json({
                    "type": "end",
                    "content": ""
                })
                
                # Add assistant response to conversation history
                manager.add_message(session_id, "assistant", full_response)
                
                # Persist assistant message to database (async, non-blocking)
                asyncio.create_task(insert_event(session_id, "assistant", full_response))
                
                print(f"[WebSocket] Sent response to {session_id}")
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON format"
                })
            
            except Exception as e:
                print(f"[WebSocket] Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected normally: {session_id}")
    
    except Exception as e:
        print(f"[WebSocket] Unexpected error for {session_id}: {e}")
    
    finally:
        # Cleanup and trigger post-session processing
        await manager.disconnect(session_id)
