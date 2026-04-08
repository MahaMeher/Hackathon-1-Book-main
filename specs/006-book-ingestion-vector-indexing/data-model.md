# Data Model: Book Content Ingestion & Vector Indexing

**Feature**: 006-book-ingestion-vector-indexing
**Date**: 2026-04-08

## Entities

### 1. BookSource

**Description**: Represents the deployed Docusaurus book on GitHub Pages, identified by its base URL.

**Fields**:
- `base_url` (string): Root URL of the deployed book (e.g., `https://username.github.io/book-name`)
- `discovery_method` (string): How URLs were discovered (`sitemap` or `crawl`)
- `total_pages` (int): Number of pages discovered
- `discovered_at` (datetime): Timestamp of URL discovery

**Validation**:
- `base_url` must be a valid HTTP/HTTPS URL
- `base_url` must not end with `/` (normalize by stripping trailing slash)
- `total_pages` must be > 0

---

### 2. FetchedPage

**Description**: An individual HTML page retrieved from the GitHub Pages deployment.

**Fields**:
- `url` (string): Full URL of the fetched page
- `html_content` (string): Raw HTML response body
- `status_code` (int): HTTP response status (200, 404, etc.)
- `fetched_at` (datetime): Timestamp of successful fetch
- `error` (string, optional): Error message if fetch failed

**Validation**:
- `url` must be within the book's domain (subdomain of `base_url`)
- `status_code` must be 200 for successful processing
- `html_content` must not be empty for successful fetches

**Relationships**:
- Belongs to: `BookSource` (many pages → one book)
- Produces: one `ExtractedText` (after text extraction)

---

### 3. ExtractedText

**Description**: Clean, normalized text extracted from a fetched HTML page.

**Fields**:
- `url` (string): Source page URL
- `raw_text` (string): Extracted text before chunking
- `section_title` (string): Page title or section name (from `<title>` or `<h1>`)
- `extracted_at` (datetime): Timestamp of extraction
- `char_count` (int): Length of extracted text

**Validation**:
- `raw_text` must not be empty or whitespace-only
- `section_title` must be non-empty (fallback to URL slug if no title found)
- `char_count` must match `len(raw_text)`

**Relationships**:
- Derived from: one `FetchedPage`
- Produces: many `TextChunk` (after chunking)

---

### 4. TextChunk

**Description**: A segment of extracted text, chunked for embedding generation.

**Fields**:
- `chunk_id` (string): Unique identifier (format: `{url_slug}_{chunk_index}`)
- `text` (string): Chunk content (500-1000 tokens)
- `url` (string): Source page URL
- `section_title` (string): Section name from parent `ExtractedText`
- `chunk_index` (int): Zero-based index within source text
- `start_char` (int): Character offset in source text
- `end_char` (int): End character offset in source text
- `token_estimate` (int): Approximate token count (~4 chars/token)

**Validation**:
- `text` must be non-empty
- `chunk_index` must be >= 0
- `start_char` must be < `end_char`
- `token_estimate` must be <= 512 (Cohere model limit)

**Relationships**:
- Derived from: one `ExtractedText`
- Produces: one `EmbeddingVector` (after embedding generation)

---

### 5. EmbeddingVector

**Description**: Semantic vector representation of a text chunk, stored in Qdrant Cloud.

**Fields**:
- `vector_id` (int): Qdrant point ID (sequential)
- `embedding` (list[float]): 1024-dimensional vector from Cohere
- `url` (string): Source page URL
- `section_title` (string): Section name
- `chunk_index` (int): Chunk position in source text
- `start_char` (int): Start offset in source text
- `end_char` (int): End offset in source text
- `ingestion_date` (string): ISO date of ingestion run (YYYY-MM-DD)

**Storage**: Qdrant Cloud collection `book_knowledge_base`

**Validation**:
- `embedding` must have exactly 1024 dimensions
- All metadata fields must be non-empty
- `vector_id` must be unique within collection

**Relationships**:
- Derived from: one `TextChunk`
- Stored in: Qdrant Cloud collection

---

### 6. IngestionRun

**Description**: A single execution of the ingestion pipeline, tracked for monitoring and debugging.

**Fields**:
- `run_id` (string): Unique identifier (UUID or timestamp-based)
- `started_at` (datetime): Pipeline start time
- `completed_at` (datetime, optional): Pipeline end time
- `status` (enum): `running`, `completed`, `failed`, `partial`
- `book_base_url` (string): Source book URL
- `pages_fetched` (int): Count of successfully fetched pages
- `pages_failed` (int): Count of failed fetches
- `chunks_created` (int): Total text chunks created
- `vectors_stored` (int): Total embeddings stored in Qdrant
- `errors` (list[string]): List of error messages (if any)

**Validation**:
- `started_at` must be set before pipeline begins
- `completed_at` must be > `started_at` (if set)
- `pages_fetched + pages_failed` must equal total discovered URLs
- `vectors_stored` must equal `chunks_created` (for successful runs)

**State Transitions**:
```
running → completed (all steps successful)
running → partial (some pages failed, but vectors stored)
running → failed (critical error, no vectors stored)
```

---

## Data Flow

```
BookSource (base_url)
    ↓ get_urls()
[FetchedPage URLs]
    ↓ fetch_and_extract()
FetchedPage (html_content)
    ↓ extract_text()
ExtractedText (raw_text, section_title)
    ↓ chunk_text()
[TextChunk] (text, metadata)
    ↓ generate_embeddings()
[EmbeddingVector] (1024-dim vector + metadata)
    ↓ store_vectors()
Qdrant Cloud Collection (book_knowledge_base)
    ↑
IngestionRun (tracks all steps)
```

---

## Validation Rules (from Requirements)

| Requirement | Validation |
|-------------|-----------|
| FR-001: Fetch all public pages | Verify `pages_fetched` equals expected count from sitemap |
| FR-003: Extract clean text | Assert no HTML tags in `raw_text` (regex: `<[^>]+>`) |
| FR-005: Chunk appropriately | Assert `token_estimate` <= 512 for all chunks |
| FR-006: Use Cohere model | Assert `len(embedding)` == 1024 |
| FR-007: Store in Qdrant | Verify collection point count == `vectors_stored` |
| FR-008: Include metadata | Assert all metadata fields non-empty for each vector |
| FR-009: Deterministic | Re-run pipeline produces same `vectors_stored` count |
