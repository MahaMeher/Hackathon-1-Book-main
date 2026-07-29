# Data Model: Frontend & Backend Integration

## Entities

### ChatMessage

A single exchange in the chatbot conversation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the message |
| `role` | enum("user", "assistant") | Yes | Who sent the message |
| `content` | string | Yes | The text content of the message |
| `sources` | Source[] | No | Supporting source citations (assistant only) |
| `selectedContext` | string | No | Selected text context if provided (user only) |
| `timestamp` | ISO 8601 string | Yes | When the message was created |
| `error` | boolean | No | Whether this message represents an error state |

**Validation Rules**:
- `content` must not be empty
- `sources` must be empty for user messages
- `id` must be unique per conversation
- `selectedContext` must be < 12,000 characters

### Source

A source citation from the book content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | The excerpted text from the book |
| `section` | string | Yes | The section heading where this content appears |
| `sourceUrl` | string | Yes | URL of the book page |
| `similarityScore` | number | Yes | Relevance score from the vector search (0-1) |

**Validation Rules**:
- `similarityScore` must be between 0 and 1
- `sourceUrl` must be a valid URL format

### ChatRequest

The payload sent from frontend to backend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The user's question |
| `selectedContext` | string | No | Optional selected text from the book page |

**Validation Rules**:
- `query` must not be empty or whitespace-only
- `query` must not exceed 5000 characters
- `selectedContext` must not exceed 12,000 characters

### ChatResponse

The payload returned from backend to frontend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | string | Yes | The AI-generated answer |
| `sources` | Source[] | Yes | Source citations for the answer |
| `modelUsed` | string | Yes | The model identifier used for generation |
| `executionTimeMs` | number | Yes | How long the query took in milliseconds |
| `status` | string | Yes | "success" or "error" |

## State Transitions

### Conversation Flow

```text
[Idle] → User types query → [Loading] → Response received → [Displaying]
                                       → Error received → [Error State]
                                                       → User retries → [Loading]
```

### ChatMessage Lifecycle

```text
User types query
  → Create user ChatMessage (role: "user", content: query, selectedContext?)
  → Set conversation state to "loading"
  → POST /api/chat
  → On success:
      → Create assistant ChatMessage (role: "assistant", content: answer, sources)
      → Set conversation state to "displaying"
  → On error:
      → Create assistant ChatMessage (role: "assistant", content: errorMsg, error: true)
      → Set conversation state to "error"
```
