# Implementation Plan: Retrieval Validation & Pipeline Testing

**Branch**: `007-retrieval-validation` | **Date**: 2026-04-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-retrieval-validation/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a Python-based retrieval validation tool that connects to the existing Qdrant Cloud collection (populated in Spec 1), accepts test queries, generates embeddings using Cohere, performs semantic similarity search, retrieves top-k chunks with metadata, and validates the results against source content. The implementation will be contained in a single `retrieved.py` file for simplicity, with comprehensive logging and validation reporting.

## Technical Context

**Language/Version**: Python 3.9+ with appropriate async support
**Primary Dependencies**: qdrant-client for vector DB queries, cohere for query embeddings, requests for URL validation, python-dotenv for config
**Storage**: Qdrant Cloud (existing collection from Spec 1), no new storage
**Testing**: pytest for unit/integration tests, validation scripts for end-to-end testing
**Target Platform**: Command-line application that runs retrieval validation tests
**Project Type**: Single-file CLI tool with validation and reporting capabilities
**Performance Goals**: Query response under 2 seconds (SC-004), consistent results across runs (SC-005)
**Constraints**: Must use same Cohere model (embed-english-v3.0) as ingestion, must connect to existing Qdrant collection
**Scale/Scope**: Validate 53 vectors across 19 pages from 4 book modules, support multiple test queries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the constitution file, this implementation must:
- Follow spec-first, reproducible development methodology
- Maintain content accuracy and grounding in retrieval results
- Ensure no hallucination beyond book content
- Implement modular and transparent system design
- Use free-tier services only where possible
- Achieve deterministic and reproducible pipeline execution
- Connect to existing infrastructure (Qdrant collection from Spec 1)

**Gate Status**: All gates pass - ready for Phase 0 research

## Project Structure

### Documentation (this feature)

```text
specs/007-retrieval-validation/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (backend directory - reuse from Spec 1)

```text
backend/
├── retrieved.py         # Single file containing all retrieval and validation logic
├── main.py              # Existing ingestion pipeline (from Spec 1, unchanged)
├── pyproject.toml       # Project dependencies (already configured)
├── .env                 # Environment variables (already configured)
└── tests/
    ├── test_retrieval.py       # Unit tests for retrieval functionality
    └── test_validation.py      # Unit tests for validation logic
```

**Structure Decision**: Single `retrieved.py` file in existing backend directory, reusing infrastructure and dependencies from Spec 1. This approach maintains consistency with the ingestion pipeline architecture and minimizes complexity.

## Pipeline Architecture

The retrieval validation will follow these sequential steps:

1. **Configuration Loading**: Load Qdrant and Cohere credentials from environment
2. **Connection Verification**: Connect to existing Qdrant collection and verify it has vectors
3. **Query Processing**: Accept test queries and convert to embeddings using Cohere
4. **Similarity Search**: Query Qdrant using semantic search, retrieve top-k results
5. **Metadata Validation**: Verify completeness and accuracy of returned metadata
6. **Source URL Verification**: Validate that source URLs correspond to actual book pages
7. **Result Logging**: Log all queries, results, and validation outcomes
8. **Performance Measurement**: Track and report query execution times
9. **Determinism Testing**: Run repeated queries to verify consistency

Each step will be implemented as a separate function in retrieved.py with clear inputs and outputs.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A - No violations identified | | |
