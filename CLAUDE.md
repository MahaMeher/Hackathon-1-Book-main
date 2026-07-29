# Hackathon_book Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-24

## Active Technologies
- Python 3.11+ (backend), Node 20+ / Docusaurus 3.9.2 / React 19 (frontend) + cohere, qdrant-client (existing); fastapi[standard], uvicorn (to add to backend); none beyond Docusaurus defaults (frontend) (008-frontend-integration)
- Qdrant Cloud (existing `book_vectors` collection via `RAGChatbot`) (008-frontend-integration)

- Python 3.11 + qdrant-client, cohere, python-dotenv (1-retrieval-validation)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- 008-frontend-integration: Added Python 3.11+ (backend), Node 20+ / Docusaurus 3.9.2 / React 19 (frontend) + cohere, qdrant-client (existing); fastapi[standard], uvicorn (to add to backend); none beyond Docusaurus defaults (frontend)

- 1-retrieval-validation: Added Python 3.11 + qdrant-client, cohere, python-dotenv

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
