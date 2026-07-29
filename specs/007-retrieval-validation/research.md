# Research: Retrieval Validation & Pipeline Testing

## Decision: Query Embedding Model
**Decision**: Use Cohere embed-english-v3.0 with 'search_query' input type
**Rationale**: Must use the same model as ingestion (embed-english-v3.0) to ensure vector space compatibility. The 'search_query' input type is optimized for query embeddings vs 'search_document' used for document embeddings during ingestion.
**Alternatives considered**:
- Using 'search_document' input type - rejected as it's optimized for document embeddings, not queries
- Different embedding models - rejected as vectors must be in same space as ingested content

## Decision: Similarity Search Strategy
**Rationale**: Using Qdrant's built-in cosine similarity search (matching the Distance.COSINE used during ingestion). Will retrieve top-k results (default k=5) with similarity scores for ranking and validation.
**Alternatives considered**:
- Euclidean distance - rejected as ingestion used cosine similarity
- Dot product scoring - rejected as it requires normalized vectors
- Hybrid search with metadata filtering - rejected as unnecessary for validation phase

## Decision: Top-K Configuration
**Decision**: Default to k=5 results per query, configurable via command-line parameter
**Rationale**: Top-5 provides sufficient results for validation while remaining manageable for manual inspection. Aligns with SC-001 success criterion (80% relevance in top-5).
**Alternatives considered**:
- k=3 - might miss relevant results
- k=10 - too many results for manual validation
- Dynamic k based on score threshold - adds complexity without clear benefit

## Decision: Metadata Validation Approach
**Rationale**: Will verify completeness (all fields present) and accuracy (URLs are valid format, section names match expected patterns). Full HTTP URL validation optional to avoid slowing down validation with network requests.
**Alternatives considered**:
- HTTP HEAD requests to validate URLs - too slow, might rate-limit
- No URL validation - insufficient for validation requirements
- Pattern matching only - adequate for format validation

## Decision: Relevance Validation Method
**Rationale**: Will use keyword overlap and semantic coherence scoring as proxy for relevance. Since we don't have ground truth labels, we'll validate that retrieved content contains terms related to the query and that similarity scores are within acceptable ranges.
**Alternatives considered**:
- Manual ground truth dataset - too labor-intensive for initial validation
- LLM-based relevance scoring - adds external dependency and cost
- Simple score threshold only - insufficient for content validation

## Decision: Performance Measurement
**Rationale**: Will measure end-to-end query time (embedding generation + similarity search + result retrieval). Target is <2 seconds per query (SC-004). Will report breakdown by operation type.
**Alternatives considered**:
- Only measuring search time - doesn't reflect user experience
- Including connection time - inflates measurements unfairly
- Separate timing for each operation - provides better diagnostics

## Decision: Determinism Testing
**Rationale**: Will execute same query multiple times and compare results. Since Qdrant uses deterministic algorithms and we use the same embeddings, results should be identical. Will track result order and scores across runs.
**Alternatives considered**:
- Statistical similarity testing - unnecessary given deterministic vector operations
- Single run only - doesn't validate determinism requirement
- Different query variants - tests different functionality

## Decision: Configuration Management
**Rationale**: Reuse existing .env file from Spec 1 ingestion pipeline. Same Qdrant credentials, same Cohere API key. Add optional QUERY_TOP_K parameter with sensible default.
**Alternatives considered**:
- Separate .env file - unnecessary duplication
- Command-line arguments for all config - inconvenient for credentials
- Hardcoded values - security risk, not flexible

## Decision: Result Output Format
**Rationale**: Console output with structured logging. Each query shows: query text, execution time, top-k results with similarity scores and metadata. JSON export option for programmatic use. Both human-readable and machine-parseable formats.
**Alternatives considered**:
- Console only - limits programmatic use
- JSON only - harder for humans to inspect
- CSV export - loses nested metadata structure
