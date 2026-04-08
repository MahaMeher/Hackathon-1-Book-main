# Feature Specification: Book Content Ingestion & Vector Indexing

**Feature Branch**: `006-book-ingestion-vector-indexing`
**Created**: 2026-04-08
**Status**: Draft
**Input**: User description: "Spec: Spec 1 – Book Content Ingestion & Vector Indexing Purpose: Convert the deployed Docusaurus book into a vectorized knowledge base for later RAG use. Target System: Spec-driven RAG backend for an AI-authored technical book. Focus: - Fetching book content from deployed GitHub Pages URLs - Extracting and normalizing text - Generating semantic embeddings - Persisting embeddings in a vector database Success Criteria: - All public book pages are successfully fetched - Text is cleanly extracted and chunked - Embeddings are generated using a Cohere embedding model - All embeddings are stored in Qdrant Cloud"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Book Content Fetching Pipeline (Priority: P1)

As a system operator, I want to automatically fetch all pages from a deployed Docusaurus book hosted on GitHub Pages, so that I can obtain the complete book content for vectorization.

**Why this priority**: This is the foundational step - without successfully fetching all book pages, no further processing can occur.

**Independent Test**: Can be fully tested by running the fetching pipeline against a known Docusaurus GitHub Pages URL and verifying that all public pages are retrieved with valid content.

**Acceptance Scenarios**:

1. **Given** a valid GitHub Pages URL for a Docusaurus book, **When** the fetching pipeline is executed, **Then** all public book pages are successfully retrieved
2. **Given** the sitemap or navigation structure, **When** the crawler runs, **Then** it discovers and fetches all nested pages
3. **Given** a fetched page, **When** the response is validated, **Then** it contains valid HTML content with expected structure

---

### User Story 2 - Text Extraction and Chunking (Priority: P1)

As a system operator, I want to extract clean, normalized text from fetched HTML pages and chunk it appropriately, so that the text is ready for semantic embedding generation.

**Why this priority**: Clean text extraction is essential for generating high-quality embeddings - noisy HTML artifacts degrade embedding quality.

**Independent Test**: Can be fully tested by running text extraction on fetched pages and verifying that HTML tags, navigation elements, and boilerplate are removed, leaving clean readable text divided into logical chunks.

**Acceptance Scenarios**:

1. **Given** fetched HTML pages, **When** the extraction process runs, **Then** clean text is produced with HTML tags, navigation menus, and footer elements removed
2. **Given** extracted text content, **When** the chunking process runs, **Then** text is divided into appropriately sized segments with logical boundaries
3. **Given** a chunk of text, **When** metadata is attached, **Then** it includes source URL, section title, and chunk index

---

### User Story 3 - Embedding Generation and Storage (Priority: P1)

As a system operator, I want to generate semantic embeddings using Cohere's embedding model and store them in Qdrant Cloud, so that the vectorized knowledge base is ready for later RAG retrieval.

**Why this priority**: This is the core value proposition - generating and storing embeddings enables all downstream RAG functionality.

**Independent Test**: Can be fully tested by running the embedding generation pipeline and verifying that vectors are created using Cohere's model and stored in Qdrant Cloud with complete metadata.

**Acceptance Scenarios**:

1. **Given** chunked text segments, **When** the embedding generation runs, **Then** semantic vectors are produced using the Cohere embedding model
2. **Given** generated embeddings, **When** they are persisted, **Then** all vectors are successfully stored in Qdrant Cloud
3. **Given** stored embeddings, **When** metadata is verified, **Then** each vector includes source URL, section name, and chunk index

---

### User Story 4 - Ingestion Verification and Inspection (Priority: P2)

As a system operator, I want to verify that the ingestion pipeline completed successfully and inspect the resulting vector collection, so that I can confirm the knowledge base is complete and usable.

**Why this priority**: Verification ensures operational confidence and enables troubleshooting if issues arise during ingestion.

**Independent Test**: Can be fully tested by running the inspection tools after ingestion and verifying that the collection exists, has the expected number of vectors, and metadata is intact.

**Acceptance Scenarios**:

1. **Given** a completed ingestion run, **When** collection status is checked, **Then** the vector collection can be listed and its size inspected
2. **Given** stored vectors, **When** sample vectors are retrieved, **Then** they contain valid embeddings and complete metadata
3. **Given** ingestion logs, **When** they are reviewed, **Then** they confirm successful fetching, extraction, embedding generation, and storage

---

### Edge Cases

- What happens when a GitHub Pages URL returns a 404 or timeout error during fetching?
- How does the system handle pages with dynamically generated content or JavaScript-rendered elements?
- What happens when the Cohere API rate limit is reached during embedding generation?
- How does the system handle very large pages that exceed token limits for embedding models?
- What happens when Qdrant Cloud experiences temporary connectivity issues during vector storage?
- How does the system handle duplicate or near-duplicate content across multiple pages?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch all publicly accessible pages from a Docusaurus book deployed on GitHub Pages
- **FR-002**: System MUST discover all pages through sitemap.xml or navigation structure crawling
- **FR-003**: System MUST extract clean text from fetched HTML, removing HTML tags, navigation menus, sidebars, footers, and other non-content elements
- **FR-004**: System MUST normalize extracted text (handle encoding, remove extra whitespace, standardize formatting)
- **FR-005**: System MUST chunk extracted text into segments appropriate for embedding (typically 500-1000 tokens with overlap)
- **FR-006**: System MUST generate semantic embeddings using a Cohere embedding model for each text chunk
- **FR-007**: System MUST persist all embeddings in Qdrant Cloud vector database
- **FR-008**: Each stored vector MUST include metadata: source URL, section title, and chunk index
- **FR-009**: System MUST provide deterministic ingestion pipeline that produces consistent results across runs
- **FR-010**: System MUST log all ingestion operations (fetching, extraction, embedding, storage) with success/failure status
- **FR-011**: System MUST allow listing and inspecting the populated vector collection
- **FR-012**: System MUST handle failures gracefully (network errors, API limits, invalid pages) and continue processing remaining content

### Key Entities

- **Book Source**: The deployed Docusaurus book on GitHub Pages, identified by its base URL and containing multiple individual pages
- **Fetched Page**: An individual HTML page retrieved from the GitHub Pages deployment, containing the raw HTML content and metadata (URL, status code, fetch timestamp)
- **Text Chunk**: A segment of extracted and normalized text from a page, with metadata linking back to the source URL and section title, plus a sequential chunk index
- **Embedding Vector**: The semantic vector representation of a text chunk generated by Cohere's embedding model, stored in Qdrant Cloud with associated metadata
- **Ingestion Run**: A single execution of the ingestion pipeline, tracked with start/end timestamps, total pages fetched, chunks created, and vectors stored

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of publicly accessible book pages from the GitHub Pages-hosted Docusaurus site are successfully fetched
- **SC-002**: Extracted text achieves 95%+ cleanliness rating (minimal HTML artifacts, navigation elements, or boilerplate content retained)
- **SC-003**: Text is chunked into appropriately sized segments (500-1000 tokens each) with logical section boundaries
- **SC-004**: 100% of text chunks have semantic embeddings successfully generated using Cohere's embedding model
- **SC-005**: 100% of generated embeddings are stored in Qdrant Cloud with complete metadata (source URL, section title, chunk index)
- **SC-006**: The vector collection can be listed and inspected within 30 seconds of ingestion completion
- **SC-007**: The complete ingestion pipeline finishes within a reasonable timeframe (under 1 hour for a medium-sized book of ~100 pages)
- **SC-008**: Ingestion pipeline is idempotent - re-running it on the same source produces consistent, deterministic results
