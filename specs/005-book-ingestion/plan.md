# Implementation Plan: Book Content Ingestion & Vector Indexing

**Branch**: `003-book-ingestion` | **Date**: 2025-12-24 | **Spec**: [link to spec](spec.md)
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a Python-based ingestion pipeline that fetches content from deployed Docusaurus books on Vercel, processes the text, generates semantic embeddings using Cohere, and stores the vectors in Qdrant Cloud. The implementation will be contained in a single main.py file with clearly separated functions for each step of the pipeline.

## Technical Context

**Language/Version**: Python 3.9+ with appropriate async support
**Primary Dependencies**: requests/BeautifulSoup for web scraping, Cohere for embeddings, qdrant-client for vector storage, uv for project management
**Storage**: Qdrant Cloud (vector database), with metadata storage for URLs and sections
**Testing**: Unit tests for each component, integration tests for end-to-end pipeline
**Target Platform**: Command-line application that can be run to execute the full ingestion pipeline
**Project Type**: Data processing pipeline with external API integrations
**Performance Goals**: Efficient processing of large documentation sites, proper error handling and retry logic
**Constraints**: Must use Cohere for embeddings, Qdrant Cloud for storage, and only fetch from Vercel-hosted Docusaurus sites
**Scale/Scope**: Handle medium to large documentation sites with hundreds of pages, chunk text appropriately for embedding models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the constitution file, this implementation must:
- Follow spec-first, reproducible development methodology
- Maintain content accuracy and grounding
- Ensure no hallucination beyond book content
- Implement modular and transparent system design
- Adhere to book standards (proper data processing, clean text extraction)
- Use free-tier services only where possible
- Achieve deterministic and reproducible pipeline execution

## Project Structure

### Documentation (this feature)

```text
specs/003-book-ingestion/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (backend directory)

```text
backend/
├── main.py              # Single file containing all ingestion logic
├── pyproject.toml       # Project dependencies and metadata (uv initialized)
├── README.md            # Project documentation
├── .python-version      # Python version specification
└── tests/               # Test files for the ingestion pipeline
    ├── test_fetcher.py
    ├── test_extractor.py
    ├── test_chunker.py
    ├── test_embeddings.py
    └── test_storage.py
```

**Structure Decision**: Single main.py file with modular functions following the user's requirement, with additional test files in a separate tests directory. Dependencies will be managed through pyproject.toml using uv.

## Pipeline Architecture

The ingestion pipeline will follow these sequential steps:

1. **URL Discovery**: Identify all pages from the Vercel-hosted Docusaurus book
2. **Content Fetching**: Fetch HTML content from each page
3. **Text Extraction**: Extract clean text from HTML, removing navigation and layout elements
4. **Text Chunking**: Split text into appropriate chunks for embedding
5. **Embedding Generation**: Generate semantic vectors using Cohere API
6. **Vector Storage**: Store embeddings in Qdrant Cloud with metadata
7. **Logging & Verification**: Log operations and verify successful storage

Each step will be implemented as a separate function in main.py with clear inputs and outputs.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|