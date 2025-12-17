"""
LLM interaction module with streaming and tool calling support.

This module provides:
- Mocked LLM with realistic token-by-token streaming
- Tool/function calling detection and execution
- Multi-step routing based on conversation mode
- Conversation context management
- OpenAI-compatible interface for easy swapping

The mocked LLM simulates realistic streaming behavior and can be easily
replaced with a real OpenAI client or other LLM provider.
"""

import asyncio
import json
from typing import List, Dict, Any, AsyncGenerator, Optional


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

async def get_user_stats() -> Dict[str, Any]:
    """
    Simulated tool: Fetch user statistics.
    
    Returns:
        Dict containing mock user statistics
    """
    await asyncio.sleep(0.1)  # Simulate API call delay
    return {
        "total_sessions": 42,
        "total_messages": 1337,
        "avg_session_duration": 180,
        "favorite_topics": ["AI", "WebSockets", "FastAPI"]
    }


async def fetch_data(query: str = "general") -> Dict[str, Any]:
    """
    Simulated tool: Fetch data based on query.
    
    Args:
        query: The data query type
    
    Returns:
        Dict containing mock data
    """
    await asyncio.sleep(0.15)  # Simulate API call delay
    
    data_responses = {
        "general": {
            "status": "success",
            "data": ["Item 1", "Item 2", "Item 3"],
            "count": 3
        },
        "stats": {
            "status": "success",
            "metrics": {"cpu": "45%", "memory": "2.1GB", "uptime": "24h"}
        }
    }
    
    return data_responses.get(query, data_responses["general"])


# Tool registry for easy lookup
AVAILABLE_TOOLS = {
    "get_user_stats": get_user_stats,
    "fetch_data": fetch_data
}


# ============================================================================
# TOOL CALLING LOGIC
# ============================================================================

def detect_tool_call(message: str) -> Optional[Dict[str, Any]]:
    """
    Detect if a user message requires a tool call.
    
    Args:
        message: User message to analyze
    
    Returns:
        Dict with tool name and arguments if tool call detected, None otherwise
    """
    message_lower = message.lower()
    
    # Check for stats-related keywords
    if any(keyword in message_lower for keyword in ["stats", "statistics", "user data"]):
        return {
            "name": "get_user_stats",
            "arguments": {}
        }
    
    # Check for data fetching keywords
    if any(keyword in message_lower for keyword in ["fetch", "get data", "retrieve"]):
        query_type = "stats" if "stats" in message_lower else "general"
        return {
            "name": "fetch_data",
            "arguments": {"query": query_type}
        }
    
    return None


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
    
    Returns:
        Tool execution result
    
    Raises:
        ValueError: If tool not found
    """
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    tool_func = AVAILABLE_TOOLS[tool_name]
    
    # Call tool with or without arguments
    if arguments:
        result = await tool_func(**arguments)
    else:
        result = await tool_func()
    
    return result


# ============================================================================
# CONVERSATION MODE ROUTING
# ============================================================================

def determine_conversation_mode(messages: List[Dict[str, str]]) -> str:
    """
    Determine conversation mode based on message history.
    
    Args:
        messages: List of conversation messages
    
    Returns:
        Conversation mode: "analytical" or "casual"
    """
    if not messages:
        return "casual"
    
    # Check first user message for analytical keywords
    first_message = messages[0].get("content", "").lower()
    
    analytical_keywords = [
        "analyze", "data", "statistics", "report", 
        "metrics", "performance", "technical"
    ]
    
    if any(keyword in first_message for keyword in analytical_keywords):
        return "analytical"
    
    return "casual"


def get_system_prompt(mode: str) -> str:
    """
    Get system prompt based on conversation mode.
    
    Args:
        mode: Conversation mode
    
    Returns:
        System prompt string
    """
    prompts = {
        "analytical": (
            "You are a professional data analyst assistant. "
            "Provide detailed, technical responses with data-driven insights. "
            "Be precise and analytical in your communication."
        ),
        "casual": (
            "You are a friendly and helpful AI assistant. "
            "Provide clear, conversational responses. "
            "Be warm and approachable in your communication."
        )
    }
    
    return prompts.get(mode, prompts["casual"])


# ============================================================================
# MOCKED LLM WITH STREAMING
# ============================================================================

class MockedLLM:
    """
    Mocked LLM that simulates OpenAI-compatible streaming behavior.
    
    This class provides realistic token-by-token streaming and can be
    easily replaced with a real OpenAI client.
    """
    
    def __init__(self, delay_ms: int = 30):
        """
        Initialize the mocked LLM.
        
        Args:
            delay_ms: Delay between tokens in milliseconds (default: 30ms)
        """
        self.delay_ms = delay_ms
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion token by token.
        
        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt to guide response
        
        Yields:
            Individual tokens (words/punctuation)
        """
        # Get the last user message
        last_message = messages[-1]["content"] if messages else ""
        
        # Generate response based on message content
        response = self._generate_response(last_message, system_prompt)
        
        # Split response into tokens (words and punctuation)
        tokens = self._tokenize(response)
        
        # Stream tokens with delay
        for token in tokens:
            await asyncio.sleep(self.delay_ms / 1000.0)
            yield token
    
    def _generate_response(self, message: str, system_prompt: Optional[str]) -> str:
        """
        Generate a response based on the message.
        
        Args:
            message: User message
            system_prompt: System prompt for context
        
        Returns:
            Generated response string
        """
        message_lower = message.lower()
        
        # Contextual responses based on keywords
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm here to help you. How can I assist you today?"
        
        elif "how are you" in message_lower:
            return "I'm functioning perfectly, thank you for asking! I'm ready to help with any questions or tasks you have."
        
        elif "websocket" in message_lower or "realtime" in message_lower:
            return "WebSockets enable real-time, bidirectional communication between clients and servers. This is perfect for chat applications, live updates, and streaming data like we're doing right now!"
        
        elif "fastapi" in message_lower:
            return "FastAPI is an excellent modern Python web framework. It's fast, supports async/await natively, has automatic API documentation, and makes building WebSocket applications straightforward."
        
        elif "supabase" in message_lower or "database" in message_lower:
            return "Supabase is a fantastic open-source Firebase alternative built on PostgreSQL. It provides real-time subscriptions, authentication, storage, and a powerful database with excellent Python client support."
        
        else:
            # Generic helpful response
            return f"I understand you're asking about: '{message}'. I'm here to help! Could you provide more details about what you'd like to know?"
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Split text into tokens for streaming.
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        tokens = []
        current_word = ""
        
        for char in text:
            if char in " \n\t":
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
                tokens.append(char)
            elif char in ".,!?;:":
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
                tokens.append(char)
            else:
                current_word += char
        
        if current_word:
            tokens.append(current_word)
        
        return tokens


# ============================================================================
# MAIN LLM INTERFACE
# ============================================================================

async def stream_llm_response(
    messages: List[Dict[str, str]],
    session_id: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream LLM response with tool calling support.
    
    This is the main interface for LLM interaction. It handles:
    - Conversation mode detection
    - Tool calling detection and execution
    - Token-by-token streaming
    - Tool result integration
    
    Args:
        messages: List of conversation messages with 'role' and 'content'
        session_id: Current session identifier
    
    Yields:
        Dict with 'type' and 'content':
        - type: "token" (text chunk), "tool_call" (tool execution), "tool_result" (tool output)
        - content: The actual content
    """
    # Determine conversation mode
    mode = determine_conversation_mode(messages)
    system_prompt = get_system_prompt(mode)
    
    # Check if we need to call a tool
    last_message = messages[-1]["content"] if messages else ""
    tool_call = detect_tool_call(last_message)
    
    if tool_call:
        # Yield tool call notification
        yield {
            "type": "tool_call",
            "content": f"🔧 Calling tool: {tool_call['name']}..."
        }
        
        # Execute the tool
        try:
            tool_result = await execute_tool(tool_call["name"], tool_call["arguments"])
            
            # Yield tool result
            yield {
                "type": "tool_result",
                "content": json.dumps(tool_result, indent=2)
            }
            
            # Add tool result to messages for context
            messages.append({
                "role": "tool",
                "content": f"Tool '{tool_call['name']}' returned: {json.dumps(tool_result)}"
            })
            
            # Generate response incorporating tool result
            llm = MockedLLM(delay_ms=30)
            
            # Create a contextual message about the tool result
            tool_context = f"Based on the {tool_call['name']} results, here's what I found: "
            
            # Stream the context first
            for token in tool_context.split():
                await asyncio.sleep(0.03)
                yield {"type": "token", "content": token + " "}
            
            # Then stream a summary of the tool result
            summary = f"The data shows {len(tool_result)} key metrics. "
            for token in summary.split():
                await asyncio.sleep(0.03)
                yield {"type": "token", "content": token + " "}
            
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Tool execution failed: {str(e)}"
            }
    
    else:
        # No tool call needed, just stream normal response
        llm = MockedLLM(delay_ms=30)
        
        async for token in llm.stream_completion(messages, system_prompt):
            yield {
                "type": "token",
                "content": token
            }
