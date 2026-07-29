# Implementation Plan: Frontend & Backend Integration

**Branch**: `008-frontend-integration` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-frontend-integration/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Integrate the Docusaurus frontend with the FastAPI RAG backend to provide an interactive chatbot on book pages. The backend does not yet expose an API — a new FastAPI server will wrap the existing `RAGChatbot` class into a REST endpoint. The frontend will gain a React chatbot component that communicates with the backend over localhost, supports both free-form queries and selected-text queries, and handles loading, error, and empty states gracefully.

## Technical Context

**Language/Version**: Python 3.11+ (backend), Node 20+ / Docusaurus 3.9.2 / React 19 (frontend)  
**Primary Dependencies**: cohere, qdrant-client (existing); fastapi[standard], uvicorn (to add to backend); none beyond Docusaurus defaults (frontend)  
**Storage**: Qdrant Cloud (existing `book_vectors` collection via `RAGChatbot`)  
**Testing**: pytest (backend), manual browser testing (frontend — Docusaurus has no built-in test runner for components)  
**Target Platform**: Local web browser on desktop (localhost:3000 frontend, localhost:8000 backend)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Chatbot response under 5 seconds (SC-001); UI loads within 2 seconds (SC-004)  
**Constraints**: Local-only communication; no authentication; no user session persistence  
**Scale/Scope**: Single-user local usage; all book content pages must support the chatbot

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is still in its template form (unfilled). No active constitutional gates are in effect. This plan follows the existing project patterns:
- Python backend with existing dependency management (pyproject.toml)
- Docusaurus frontend with standard React components
- No new architectural patterns beyond what the feature spec requires

**Gate verdict**: PASS (no constitutional violations found)

**Post-design re-check (Phase 1 complete)**: PASS — all artifacts generated (research.md, data-model.md, api-contract.md, quickstart.md). No design decisions violate existing project patterns. The FastAPI server wraps, rather than replaces, the existing `RAGChatbot` class. The frontend component follows the existing `HomepageFeatures` component pattern for React code.

## Project Structure

### Documentation (this feature)

```text
specs/008-frontend-integration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── api.py               # NEW — FastAPI server with /api/chat endpoint
├── main.py              # EXISTING — ingestion pipeline (unchanged)
├── rag_chatbot.py       # EXISTING — RAGChatbot class (add selected-text context support)
├── pyproject.toml       # EXISTING — add fastapi[standard], uvicorn
└── tests/
    └── test_api.py      # NEW — endpoint tests

Frontend_book/
├── src/
│   └── components/
│       └── ChatBot/
│           ├── index.jsx           # NEW — chatbot component
│           ├── ChatBot.css         # NEW — chatbot styles
│           └── ChatBotAPI.js       # NEW — API client helper
└── docusaurus.config.js  # EXISTING — add CORS proxy config (devServer)
```

**Structure Decision**: Follows the existing project layout — backend in `backend/`, frontend in `Frontend_book/`. Adds a new backend API module and a frontend component directory, consistent with the existing `HomepageFeatures` component pattern.

## Complexity Tracking

> No constitution violations to justify. Complexity is minimal — one new backend endpoint and one new frontend component, both following existing patterns.
