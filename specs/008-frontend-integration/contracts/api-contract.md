# API Contract: Chat Endpoint

## Base URL

- **Development**: `http://localhost:8000`
- **Proxy path**: `/api` (Docusaurus devServer proxy maps `/api/*` to `http://localhost:8000/api/*`)

## Endpoint: POST /api/chat

Send a user query and receive an AI response grounded in book content.

### Request

```json
{
  "query": "What is the ROS 2 navigation stack?",
  "selected_context": "The ROS 2 Navigation Stack provides a framework for mobile robot navigation..." 
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The user's question (1-5000 chars) |
| `selected_context` | string | No | Optional book text selection to ground the answer (max 12000 chars) |

### Response (200 OK)

```json
{
  "answer": "The ROS 2 Navigation Stack (Nav2) is a framework...",
  "sources": [
    {
      "content": "Nav2 provides perception, planning, control...",
      "section": "Chapter 3: Navigation",
      "source_url": "https://book.example.com/ch3-navigation",
      "similarity_score": 0.92
    }
  ],
  "model_used": "command-r-08-2024",
  "execution_time_ms": 2340,
  "status": "success"
}
```

### Response (400 Bad Request)

```json
{
  "detail": "query must not be empty"
}
```

### Response (500 Internal Server Error)

```json
{
  "answer": "Sorry, I encountered an error while processing your question. Please try again.",
  "sources": [],
  "model_used": "",
  "execution_time_ms": 0,
  "status": "error"
}
```

### Error States

| Status Code | Condition | Handling |
|-------------|-----------|----------|
| 400 | Empty query / query too long | Frontend prevents empty submissions; displays validation message |
| 500 | Backend error (Qdrant down, Cohere API error) | Frontend shows friendly error, keeps conversation history |
| 503 | Backend unreachable | Frontend displays "Service unavailable" message |

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)
```
