# Data Model: Book Content Ingestion & Vector Indexing

## Entity: BookContent
**Description**: Represents the fetched Docusaurus book pages with their original URLs and structural information

**Fields**:
- `url`: string (required) - The original Vercel URL of the book page
- `html_content`: string (required) - The raw HTML content fetched from the URL
- `title`: string (required) - The page title extracted from HTML
- `fetched_at`: datetime (required) - Timestamp when content was fetched
- `status_code`: integer (required) - HTTP status code from the fetch
- `content_hash`: string (required) - Hash of the content for change detection

**Validation**:
- URL must be a valid Vercel-hosted Docusaurus URL
- HTML content must not be empty
- Status code must be 200 for successful fetch

## Entity: TextChunk
**Description**: Represents a segment of extracted and normalized text from the book content, with metadata linking back to source

**Fields**:
- `id`: string (required) - Unique identifier for the chunk
- `content`: string (required) - The clean, extracted text content
- `source_url`: string (required) - Reference to the original URL
- `section`: string (required) - The section or heading this chunk belongs to
- `chunk_index`: integer (required) - Sequential index of this chunk within the page
- `word_count`: integer (required) - Number of words in the chunk
- `char_count`: integer (required) - Number of characters in the chunk
- `created_at`: datetime (required) - Timestamp when chunk was created

**Validation**:
- Content must be between 100 and 5000 characters
- Chunk index must be non-negative
- Source URL must reference an existing BookContent entity

## Entity: EmbeddingVector
**Description**: Represents the semantic vector representation of a text chunk, stored in Qdrant Cloud with associated metadata

**Fields**:
- `vector_id`: string (required) - Unique identifier for the vector in Qdrant
- `vector`: array<float> (required) - The actual embedding vector (typically 1024 dimensions)
- `text_chunk_id`: string (required) - Reference to the source TextChunk
- `source_url`: string (required) - Direct reference to original URL for quick access
- `section`: string (required) - The section this vector represents
- `chunk_index`: integer (required) - Index of the chunk within the page
- `model_used`: string (required) - Name of the embedding model used (e.g., "embed-english-v3.0")
- `generated_at`: datetime (required) - Timestamp when embedding was generated

**Validation**:
- Vector must have the correct dimensionality for the model used
- Text chunk ID must reference an existing TextChunk entity
- Vector values must be within valid range for embeddings

## Entity: IngestionLog
**Description**: Represents the record of ingestion operations, including success/failure status for each page

**Fields**:
- `log_id`: string (required) - Unique identifier for the log entry
- `operation`: string (required) - Type of operation (fetch, extract, chunk, embed, store)
- `url`: string (optional) - URL being processed (null for pipeline-level logs)
- `status`: string (required) - Status of the operation (success, failed, skipped)
- `message`: string (optional) - Detailed message about the operation
- `timestamp`: datetime (required) - When the log entry was created
- `duration_ms`: integer (optional) - Duration of the operation in milliseconds
- `ingestion_run_id`: string (required) - ID grouping all logs for a single ingestion run

**Validation**:
- Operation must be one of the defined values
- Status must be one of: success, failed, skipped
- Duration must be non-negative when provided

## Entity: IngestionRun
**Description**: Represents a complete ingestion pipeline execution

**Fields**:
- `run_id`: string (required) - Unique identifier for the ingestion run
- `start_time`: datetime (required) - When the ingestion started
- `end_time`: datetime (optional) - When the ingestion completed (null if running)
- `status`: string (required) - Current status (running, completed, failed)
- `pages_fetched`: integer (required) - Number of pages successfully fetched
- `pages_failed`: integer (required) - Number of pages that failed to fetch
- `chunks_created`: integer (required) - Number of text chunks created
- `vectors_stored`: integer (required) - Number of vectors successfully stored
- `total_duration_ms`: integer (optional) - Total duration in milliseconds

**Validation**:
- Status must be one of: running, completed, failed
- Count values must be non-negative
- End time must be after start time when provided