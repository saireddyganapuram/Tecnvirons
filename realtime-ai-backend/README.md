# 🚀 Realtime AI Backend

A production-ready real-time AI backend built with **FastAPI**, **WebSockets**, **LLM streaming**, and **Supabase** for persistent storage. This project demonstrates modern async Python architecture with token-by-token AI response streaming, tool calling, and background processing.

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Database Schema](#database-schema)
- [How to Run](#how-to-run)
- [How to Test](#how-to-test)
- [Design Decisions](#design-decisions)
- [Project Structure](#project-structure)

---

## 🎯 Overview

This project implements a **real-time AI chat backend** that showcases:

- **WebSocket-based streaming**: Token-by-token AI responses for real-time user experience
- **Tool/Function calling**: AI can invoke tools to fetch data and integrate results
- **Conversation state management**: Multi-turn conversations with context preservation
- **Async database persistence**: All events saved to Supabase without blocking
- **Post-session processing**: Background summarization after session ends
- **OpenAI-compatible design**: Easy to swap mocked LLM with real providers

This is an **internship assignment** focused on demonstrating backend architecture, async design patterns, and real-time communication rather than AI accuracy.

---

## 🛠️ Tech Stack

| Technology | Purpose | Why? |
|------------|---------|------|
| **Python 3.8+** | Backend language | Excellent async support, clean syntax |
| **FastAPI** | Web framework | Modern, fast, async-native, auto-docs |
| **WebSockets** | Real-time communication | Bidirectional streaming for chat |
| **Supabase** | Database (PostgreSQL) | Real-time capabilities, easy setup, Python client |
| **Uvicorn** | ASGI server | High-performance async server |
| **Mocked LLM** | AI simulation | Demonstrates streaming without API costs |

---

## ✨ Features

### 1. **Real-time WebSocket Sessions**
- Endpoint: `/ws/session/{session_id}`
- Accepts WebSocket connections with unique session IDs
- Streams AI responses token-by-token for smooth UX
- Maintains conversation state across multiple messages

### 2. **Complex LLM Interaction**

#### **Tool/Function Calling**
- Detects keywords like `fetch`, `data`, `stats` in user messages
- Calls simulated tools (e.g., `get_user_stats()`, `fetch_data()`)
- Integrates tool results back into AI response
- All tool calls persisted to database

#### **Multi-Step Routing**
- Analyzes first message to determine conversation mode
- **Analytical mode**: Technical, data-driven responses
- **Casual mode**: Friendly, conversational responses
- System prompt adapts based on mode

#### **Conversation State Management**
- Maintains message history in memory during session
- Provides context to LLM for coherent multi-turn conversations
- All messages persisted to database asynchronously

### 3. **Supabase Persistence**

Two tables store all session data:

- **`sessions`**: Session metadata (start/end time, duration, summary)
- **`events`**: All messages (user, assistant, tool) with timestamps

All database operations are **async** and **non-blocking**.

### 4. **Post-Session Processing**

When WebSocket disconnects:
1. Background task triggers automatically
2. Fetches full conversation history from database
3. Generates concise session summary
4. Calculates session duration
5. Updates session record with metadata

---

## 🏗️ Architecture

```
┌─────────────┐         WebSocket          ┌──────────────────┐
│   Frontend  │ ◄─────────────────────────► │  FastAPI Server  │
│ (HTML/JS)   │    Token-by-token stream    │   (WebSocket)    │
└─────────────┘                             └────────┬─────────┘
                                                     │
                                    ┌────────────────┼────────────────┐
                                    │                │                │
                              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
                              │    LLM    │   │  Database │   │ Background│
                              │ Streaming │   │  (Async)  │   │   Tasks   │
                              │ + Tools   │   │ Supabase  │   │ Summary   │
                              └───────────┘   └───────────┘   └───────────┘
```

**Flow:**
1. Client connects via WebSocket with session ID
2. User sends message → saved to DB (async)
3. LLM processes message, checks for tool calls
4. If tool needed → execute → integrate result
5. Stream response token-by-token to client
6. Save AI response to DB (async)
7. On disconnect → background task generates summary

---

## 📦 Setup Instructions

### Prerequisites

- **Python 3.8+** installed
- **Supabase account** (free tier works)
- **Git** (optional, for cloning)

### Step 1: Clone or Download Project

```bash
cd "c:\Users\Public\Desktop\23J41A12D8\Internship\Tecnvinors Assignment"
cd realtime-ai-backend
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Supabase

1. **Create a Supabase project**:
   - Go to [https://supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose a name and password

2. **Run the SQL schema** (see [Database Schema](#database-schema) section below):
   - In Supabase dashboard, go to **SQL Editor**
   - Copy and paste the schema from below
   - Click "Run"

3. **Get your credentials**:
   - Go to **Settings** → **API**
   - Copy **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - Copy **anon/public key** (starts with `eyJ...`)

### Step 5: Configure Environment Variables

1. Copy the example file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-or-service-key-here
   ```

---

## 🗄️ Database Schema

Run this SQL in your **Supabase SQL Editor**:

```sql
-- ============================================================================
-- SESSIONS TABLE
-- Stores metadata for each WebSocket session
-- ============================================================================
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    duration INTEGER,
    final_summary TEXT
);

-- ============================================================================
-- EVENTS TABLE
-- Stores all messages and tool calls for each session
-- ============================================================================
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- Improve query performance for session history lookups
-- ============================================================================
CREATE INDEX idx_events_session_id ON events(session_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);

-- ============================================================================
-- COMMENTS
-- Documentation for future reference
-- ============================================================================
COMMENT ON TABLE sessions IS 'Stores WebSocket session metadata and summaries';
COMMENT ON TABLE events IS 'Stores all conversation events (messages and tool calls)';
COMMENT ON COLUMN events.role IS 'Message sender: user, assistant, or tool';
```

**Verify tables created:**
- Go to **Table Editor** in Supabase
- You should see `sessions` and `events` tables

---

## 🚀 How to Run

### Start the Backend Server

```bash
# Make sure you're in the realtime-ai-backend directory
# and your virtual environment is activated

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
🚀 Realtime AI Backend Starting...
📡 WebSocket endpoint: ws://localhost:8000/ws/session/{session_id}
🏥 Health check: http://localhost:8000/health
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Open the Frontend

1. Open `frontend/index.html` in your web browser
2. Or navigate to: `file:///c:/Users/Public/Desktop/23J41A12D8/Internship/Tecnvinors%20Assignment/realtime-ai-backend/frontend/index.html`

---

## 🧪 How to Test

### Test 1: Basic Connection

1. **Open frontend** in browser
2. **Enter session ID**: `test-session-1`
3. **Click "Connect"**
4. **Verify**: Status shows "Connected" (green indicator)

### Test 2: Simple Chat

1. **Send message**: `"Hello, how are you?"`
2. **Verify**: 
   - AI response streams token-by-token
   - Response appears in chat window
3. **Check Supabase**:
   - Go to **Table Editor** → `sessions`
   - Should see new row with `session_id = test-session-1`
   - Go to **Table Editor** → `events`
   - Should see 2 rows: one `user` message, one `assistant` message

### Test 3: Tool Calling

1. **Send message**: `"Can you fetch some data for me?"`
2. **Verify**:
   - See tool call notification (yellow box)
   - See tool result (blue box with JSON)
   - See AI response incorporating the data
3. **Check Supabase** → `events`:
   - Should see 3 rows: user message, tool event, assistant message

### Test 4: Multi-Turn Conversation

1. **Send multiple messages**:
   - `"Tell me about WebSockets"`
   - `"What about FastAPI?"`
   - `"And Supabase?"`
2. **Verify**: Each response maintains context
3. **Check Supabase**: All messages saved in order

### Test 5: Post-Session Processing

1. **Click "Disconnect"** (or close browser tab)
2. **Wait 2-3 seconds**
3. **Check Supabase** → `sessions` table:
   - `end_time` should be populated
   - `duration` should show session length (in seconds)
   - `final_summary` should contain conversation summary

### Test 6: Multiple Concurrent Sessions

1. **Open 2 browser tabs**
2. **Tab 1**: Connect with `session-A`
3. **Tab 2**: Connect with `session-B`
4. **Send different messages** in each tab
5. **Verify**: Sessions are independent
6. **Check Supabase**: Separate session records

### Test 7: API Health Check

Open in browser or use curl:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Realtime AI Backend",
  "version": "1.0.0",
  "features": {
    "websocket_streaming": true,
    "llm_interaction": true,
    "tool_calling": true,
    "database_persistence": true,
    "post_session_processing": true
  }
}
```

---

## 🧠 Design Decisions

### 1. **Why Async/Await Everywhere?**

**Decision**: All I/O operations use `async`/`await`

**Rationale**:
- **Non-blocking**: Database writes don't block WebSocket streaming
- **Scalability**: Can handle many concurrent connections efficiently
- **Modern Python**: FastAPI is built for async, leveraging it fully
- **Performance**: Event loop handles I/O while CPU does other work

**Example**: While streaming AI response, database writes happen in background without interrupting the stream.

### 2. **Why WebSockets for Real-Time Communication?**

**Decision**: WebSocket instead of HTTP polling or SSE

**Rationale**:
- **Bidirectional**: Client and server both send messages freely
- **Low latency**: Persistent connection, no handshake overhead
- **Efficient**: Single connection for entire session
- **Native support**: FastAPI has excellent WebSocket support

**Alternative considered**: Server-Sent Events (SSE) - rejected because it's unidirectional (server → client only).

### 3. **How LLM Streaming Works**

**Decision**: Async generator pattern for token streaming

**Implementation**:
```python
async def stream_llm_response(...) -> AsyncGenerator[Dict, None]:
    async for token in llm.stream_completion(...):
        yield {"type": "token", "content": token}
```

**Rationale**:
- **Memory efficient**: Tokens yielded one at a time, not stored in memory
- **Real-time UX**: User sees response as it's generated
- **Cancellable**: Can stop mid-stream if client disconnects
- **OpenAI-compatible**: Same pattern as OpenAI's streaming API

### 4. **How Tool Calling is Implemented**

**Decision**: Keyword detection + function registry

**Implementation**:
1. Detect keywords in user message (`fetch`, `stats`, etc.)
2. Look up tool in registry: `AVAILABLE_TOOLS = {"get_user_stats": func, ...}`
3. Execute tool asynchronously
4. Inject result into conversation context
5. LLM generates response incorporating tool data

**Rationale**:
- **Simple**: No complex parsing or LLM-based tool selection
- **Extensible**: Easy to add new tools to registry
- **Demonstrative**: Shows architecture without requiring real LLM
- **Production-ready**: Can swap with OpenAI function calling

### 5. **How Background Processing Works**

**Decision**: `asyncio.create_task()` for fire-and-forget tasks

**Implementation**:
```python
# In WebSocket handler
asyncio.create_task(insert_event(session_id, "user", message))

# On disconnect
asyncio.create_task(process_session_end(session_id))
```

**Rationale**:
- **Non-blocking**: Database writes don't slow down streaming
- **Automatic**: Summary generation happens without user waiting
- **Resilient**: Errors in background tasks don't crash main flow
- **Scalable**: Event loop manages task scheduling

### 6. **Why Mocked LLM Instead of Real API?**

**Decision**: Simulated LLM with realistic streaming

**Rationale**:
- **No API costs**: Runs without OpenAI/Anthropic keys
- **Deterministic**: Easier to test and demonstrate
- **Fast**: No network latency
- **Educational**: Shows architecture clearly
- **Swappable**: OpenAI-compatible interface for easy replacement

**To use real LLM**: Replace `MockedLLM` class in `app/llm.py` with OpenAI client.

### 7. **Database Design Choices**

**Decision**: Two tables (`sessions`, `events`) with foreign key

**Rationale**:
- **Normalized**: Avoids data duplication
- **Efficient queries**: Index on `session_id` for fast lookups
- **Flexible**: Easy to add new event types (e.g., `system`, `error`)
- **Cascade delete**: Deleting session removes all events automatically

**Alternative considered**: Single table with JSON - rejected for query performance and type safety.

### 8. **Why Supabase Over Other Databases?**

**Decision**: Supabase (PostgreSQL) instead of MongoDB, Firebase, etc.

**Rationale**:
- **SQL**: Powerful queries, joins, transactions
- **Real-time**: Built-in subscriptions (not used here, but available)
- **Free tier**: Generous limits for development
- **Python client**: Excellent async support
- **Open source**: Can self-host if needed

---

## 📁 Project Structure

```
realtime-ai-backend/
│
├── app/
│   ├── __init__.py           # Python package marker
│   ├── main.py               # FastAPI app & startup
│   ├── websocket.py          # WebSocket session handler
│   ├── llm.py                # LLM streaming + tool logic
│   ├── db.py                 # Supabase client
│   ├── models.py             # DB helper functions
│   └── summary.py            # Post-session summarization
│
├── frontend/
│   └── index.html            # Simple WebSocket UI
│
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Your actual credentials (git-ignored)
└── README.md                 # This file
```

### File Responsibilities

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | FastAPI app initialization | `app`, `websocket_endpoint()`, health checks |
| `websocket.py` | WebSocket connection management | `handle_websocket()`, `ConnectionManager` |
| `llm.py` | LLM streaming and tool calling | `stream_llm_response()`, `MockedLLM`, tool registry |
| `db.py` | Supabase client setup | `get_supabase_client()` |
| `models.py` | Database operations | `create_session()`, `insert_event()`, `get_session_history()` |
| `summary.py` | Background processing | `process_session_end()`, `generate_session_summary()` |
| `index.html` | Frontend UI | WebSocket client, message rendering |

---

## 🎓 Learning Outcomes

This project demonstrates:

✅ **Async Python**: Proper use of `async`/`await`, event loops, background tasks  
✅ **WebSocket Architecture**: Real-time bidirectional communication  
✅ **Streaming Patterns**: Async generators for token-by-token delivery  
✅ **Database Design**: Normalized schema, async operations, indexing  
✅ **Tool Calling**: Function registry, dynamic execution, result integration  
✅ **State Management**: In-memory conversation history + persistent storage  
✅ **Background Processing**: Fire-and-forget tasks, session summarization  
✅ **Error Handling**: Graceful disconnects, exception handling  
✅ **Production Practices**: Environment variables, CORS, health checks  

---

## 🚧 Future Enhancements

- [ ] Add authentication (JWT tokens)
- [ ] Implement rate limiting
- [ ] Add Redis for session caching
- [ ] Support multiple LLM providers (OpenAI, Anthropic, etc.)
- [ ] Add conversation export (PDF, JSON)
- [ ] Implement user feedback mechanism
- [ ] Add metrics and monitoring (Prometheus)
- [ ] Create Docker containerization
- [ ] Add comprehensive test suite (pytest)

---

## 📄 License

This is an internship assignment project. Feel free to use as reference or learning material.

---

## 👤 Author

**Internship Assignment - Tecnvinors**  
Built with ❤️ using FastAPI, WebSockets, and Supabase

---

## 🆘 Troubleshooting

### Issue: "Missing Supabase credentials"
**Solution**: Make sure `.env` file exists with correct `SUPABASE_URL` and `SUPABASE_KEY`

### Issue: WebSocket connection fails
**Solution**: 
1. Check backend is running on port 8000
2. Verify firewall isn't blocking WebSocket connections
3. Check browser console for errors

### Issue: Database errors
**Solution**:
1. Verify Supabase tables are created (run SQL schema)
2. Check credentials are correct
3. Ensure Supabase project is active (not paused)

### Issue: No token streaming visible
**Solution**:
1. Check browser console for WebSocket messages
2. Verify backend logs show message processing
3. Try refreshing the page

---

**Happy Coding! 🚀**
