# Research: Frontend & Backend Integration

## Resolved Technical Decisions

### 1. FastAPI Server Architecture

**Decision**: Create a new `backend/api.py` module that instantiates FastAPI, wraps `RAGChatbot.ask()`, and exposes a single REST endpoint.

**Rationale**:
- Existing `rag_chatbot.py` has a clean `RAGChatbot.ask()` method that returns a `ChatResponse` dataclass — ideal for wrapping
- Separate `api.py` keeps concerns separated from the ingestion pipeline in `main.py`
- Standard FastAPI pattern: one app instance, CORS middleware, Pydantic request/response models

**Alternatives considered**:
- Adding API endpoints directly to `main.py` — rejected to avoid mixing ingestion and serving responsibilities
- Using a separate framework (Flask) — rejected in favor of FastAPI since it's already listed in the spec constraints

**CORS Configuration**:
- Allow origin: `http://localhost:3000` (Docusaurus dev server)
- Methods: POST
- Headers: Content-Type

### 2. Selected Text Context Handling

**Decision**: Extend `RAGChatbot.ask()` to accept an optional `selected_context` parameter. When provided, prepend it to the prompt as additional grounding context.

**Rationale**:
- Minimal change to the existing method signature
- The prompt builder already constructs context from retrieved chunks — selected text is added as an additional context block
- No schema change needed; the optional string parameter is straightforward

### 3. Docusaurus Component Registration

**Decision**: Create a standalone React component (`ChatBot/index.jsx`) that renders a chat panel. Embed it on book pages via a custom Docusaurus plugin or by rendering it within the page layout using `@docusaurus/theme-classic`'s `Layout` component.

**Rationale**:
- Docusaurus 3.x supports client-side React components without JSX bundling config
- The existing `HomepageFeatures` component provides a working reference pattern
- The component can use a portal or fixed positioning to overlay on the page

**Alternatives considered**:
- Using a Docusaurus plugin — overkill for a single component
- Injecting into the theme's `Layout` via swizzling — fragile on Docusaurus upgrades

### 4. Frontend-Backend Communication

**Decision**: Use the browser `fetch()` API from the React component. In Docusaurus dev mode, use the `devServer.proxy` configuration to route `/api/*` calls to the FastAPI backend.

**Rationale**:
- No additional frontend dependencies (no axios, no fetch wrappers)
- `devServer.proxy` avoids CORS issues in development
- For production builds, the frontend is served separately from the backend, so direct `http://localhost:8000/api/chat` calls work with CORS

**Pattern**:
```text
Docusaurus dev (port 3000) → proxy → FastAPI (port 8000)
Production build → CORS → FastAPI (port 8000)
```

### 5. Frontend Testing

**Decision**: Manual browser testing. Docusaurus does not include a built-in component test runner, and adding Jest + React Testing Library for a single component is disproportionate to this feature's scope.

**Rationale**:
- Single component with straightforward logic (form input, fetch call, response display)
- Backend logic is already tested via `rag_chatbot.py`'s existing structure
- End-to-end validation is done by running both services locally and verifying acceptance scenarios

### 6. Selected Text Detection in the Browser

**Decision**: Use the native `window.getSelection()` API triggered by `mouseup` events on the document body. Display a floating "Ask about this selection" button near the selection when text is selected.

**Rationale**:
- No additional dependencies
- Works across all modern browsers
- The `mouseup` → `getSelection()` pattern is well-established

## Architecture Diagram (Text)

```text
┌──────────────────┐          HTTP POST /api/chat        ┌──────────────────────┐
│  Docusaurus       │  ──────────────────────────────→   │  FastAPI Server       │
│  (React 19)       │  ←──────────────────────────────   │  (port 8000)          │
│                   │          JSON Response              │                       │
│  ChatBot.jsx      │                                     │  api.py               │
│  └── state:       │                                     │  └── POST /api/chat   │
│      loading      │                                     │      → RAGChatbot.ask │
│      response     │                                     │      → ChatResponse   │
│      error        │                                     │                       │
└──────────────────┘                                     └───────┬──────────────┘
                                                                  │
                                                          ┌───────┴──────────────┐
                                                          │  RAGChatbot           │
                                                          │  (rag_chatbot.py)     │
                                                          │                       │
                                                          │  Cohere Embeddings    │
                                                          │  → Qdrant Search      │
                                                          │  → Cohere Generation  │
                                                          └───────────────────────┘
```

## Technology Versions

| Component | Current | Change |
|-----------|---------|--------|
| Python | 3.11+ | No change |
| FastAPI | Not installed | Add to pyproject.toml |
| Uvicorn | Not installed | Add to pyproject.toml |
| Cohere SDK | Existing | No change |
| Qdrant Client | Existing | No change |
| Docusaurus | 3.9.2 | No change |
| React | 19 | No change |
