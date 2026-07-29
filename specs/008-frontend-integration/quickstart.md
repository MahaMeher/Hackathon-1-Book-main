# Quickstart: Frontend & Backend Integration

## Prerequisites

- Python 3.11+ installed
- Node.js 20+ installed
- Backend dependencies installed (`cd backend && pip install -e .`)
- Frontend dependencies installed (`cd Frontend_book && npm install`)
- `.env` file configured with valid `COHERE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`
- Qdrant collection `book_vectors` must have data (run ingestion pipeline if not)

## Running Locally

### 1. Start the Backend API Server

```bash
cd backend
uvicorn api:app --reload --port 8000
```

The server starts at `http://localhost:8000`. The `/api/chat` endpoint is ready.

**Verify**: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"query": "What is ROS 2?"}'`

### 2. Start the Docusaurus Frontend

```bash
cd Frontend_book
npm start
```

The site opens at `http://localhost:3000`. The chatbot component appears on book content pages.

### 3. Test End-to-End

1. Open `http://localhost:3000` in a browser
2. Navigate to a book content page
3. Type a question into the chatbot (e.g., "What is ROS 2?")
4. Verify a grounded response appears with source citations
5. Select text on the page and click "Ask about this selection"
6. Verify the contextual question works

## Verification Checklist

| # | Check | Expected |
|---|-------|----------|
| 1 | Backend starts | `uvicorn` runs on port 8000, no errors |
| 2 | Frontend starts | Docusaurus runs on port 3000, no errors |
| 3 | Chatbot visible | Chat panel/button appears on book pages |
| 4 | Query works | Type question → response with sources appears |
| 5 | Selected text | Select text → "Ask about this" → question with context works |
| 6 | Empty query | Submit empty → prevented or shown validation |
| 7 | Backend offline | Chatbot shows "Service unavailable" message |
| 8 | Response quality | Answer references specific book content |

## Dependencies to Add

### Backend (`pyproject.toml`)

```toml
dependencies = [
    ...existing...,
    "fastapi[standard]>=0.115.0",
    "uvicorn[standard]>=0.30.0",
]
```

### Frontend (`package.json`)

No additional dependencies needed. The chatbot component uses:
- `fetch()` (browser built-in)
- React `useState` / `useEffect` hooks
- `window.getSelection()` for text selection
