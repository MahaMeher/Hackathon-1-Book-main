# Implementation Plan: Book Content Ingestion & Vector Indexing

**Branch**: `006-book-ingestion-vector-indexing` | **Date**: 2026-04-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-book-ingestion-vector-indexing/spec.md`

## Summary

Build a deterministic ingestion pipeline in a single `backend/main.py` file that crawls a Docusaurus book deployed on GitHub Pages, extracts and chunks text content, generates semantic embeddings using Cohere's embedding model, and stores vectors with metadata in Qdrant Cloud. The pipeline runs as a simple Python script with a `main()` function orchestrating all steps: URL discovery → crawling → text extraction → chunking → embedding → vector storage.

## Technical Context

**Language/Version**: Python 3.11+ (existing backend uses Python with uv)
**Primary Dependencies**: 
- httpx for async HTTP crawling
- BeautifulSoup4 for HTML parsing and text extraction
- cohere Python SDK for embedding generation
- qdrant-client for Qdrant Cloud interaction
- python-dotenv for environment variable loading
**Storage**: Qdrant Cloud (Free Tier) for vector embeddings; no local database
**Testing**: pytest (basic unit tests for extraction, chunking, embedding functions)
**Target Platform**: Development environment (Linux/macOS/Windows)
**Project Type**: Single file script (`backend/main.py`)
**Performance Goals**: Complete ingestion of ~100 pages in under 1 hour
**Constraints**: 
- Free-tier API limits (Cohere, Qdrant Cloud)
- GitHub Pages rate limits (respect 429 responses with retries)
- All secrets via environment variables: COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY, BOOK_BASE_URL
**Scale/Scope**: Medium-sized Docusaurus book (~100 pages, ~1000-5000 text chunks)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Spec-first**: Feature spec (006-book-ingestion-vector-indexing) is complete with requirements, user stories, and success criteria
✅ **Environment variables**: All API keys (Cohere, Qdrant) loaded from .env, never hardcoded
✅ **Free-tier only**: Architecture uses only Cohere embedding API and Qdrant Cloud Free Tier
✅ **Content accuracy**: Text extraction preserves book content faithfully without modification
✅ **Reproducible**: Deterministic pipeline that can be re-run with consistent results
⚠️ **Modular design**: Single-file architecture (`main.py`) violates modular design principle, but justified for hackathon simplicity and rapid prototyping

**Gate Status**: PASS with complexity tracking entry for single-file decision

## Project Structure

### Documentation (this feature)

```text
specs/006-book-ingestion-vector-indexing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no API contracts for batch pipeline)
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── main.py              # Complete ingestion pipeline (all functionality)
├── .env                 # API keys (gitignored)
├── .env.example         # Template for required variables
├── pyproject.toml       # Dependencies and scripts
└── README.md            # Usage documentation
```

**Structure Decision**: Single `backend/main.py` file containing all ingestion functionality. The file will have clearly separated functions:

1. `get_urls(book_base_url)` - Discover all book page URLs via sitemap/crawling
2. `fetch_and_extract(url)` - Fetch HTML and extract clean text
3. `chunk_text(text, metadata)` - Split text into chunks with overlap
4. `generate_embeddings(chunks)` - Generate Cohere embeddings
5. `store_vectors(embeddings, metadata)` - Store in Qdrant Cloud
6. `main()` - Orchestrate all steps: get URLs → fetch/extract → chunk → embed → store

This simplified structure is chosen for hackathon speed and clarity. All functions are importable and testable independently despite living in one file.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Single-file architecture (main.py) | Hackathon constraint, rapid prototyping, simplified debugging | Modular package would add complexity without benefit for a single-purpose batch script |
