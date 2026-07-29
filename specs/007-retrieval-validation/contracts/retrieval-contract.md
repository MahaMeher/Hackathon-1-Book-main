# Retrieval API Contract

## Overview

This contract defines the retrieval functionality for querying the Qdrant vector database and validating results. Implemented as `retrieved.py` for validation testing.

## Function: execute_query

**Description**: Execute a semantic similarity search query against the Qdrant collection

**Input**:
- `query_text` (string, required): The search query text
- `top_k` (integer, optional, default=5): Number of results to retrieve
- `collection_name` (string, optional, default="book_vectors"): Qdrant collection to query

**Output** (RetrievalResult):
```json
{
  "result_id": "result_1776024000_001",
  "query_text": "What is ROS 2?",
  "query_embedding_model": "embed-english-v3.0",
  "retrieved_chunks": [
    {
      "chunk_id": "uuid-from-qdrant",
      "content": "ROS 2 is a flexible framework...",
      "similarity_score": 0.723,
      "source_url": "https://hackathon-1-book-chi.vercel.app/docs/module1/chapter1-ros2-fundamentals.html",
      "section": "docs/module1",
      "chunk_index": 0,
      "model_used": "embed-english-v3.0",
      "generated_at": "2026-04-13T00:52:20Z"
    }
  ],
  "total_results": 5,
  "execution_time_ms": 847,
  "embedding_time_ms": 312,
  "search_time_ms": 535,
  "timestamp": "2026-04-13T01:00:00Z",
  "top_k": 5
}
```

**Errors**:
- `QueryEmptyError`: When query text is empty or whitespace-only
- `ConnectionError`: When unable to connect to Qdrant or Cohere API
- `CollectionNotFoundError`: When specified collection doesn't exist
- `EmbeddingError`: When Cohere API fails to generate embedding

---

## Function: validate_result

**Description**: Validate a retrieval result for metadata completeness, URL validity, and relevance

**Input**:
- `retrieval_result` (RetrievalResult, required): The result to validate

**Output** (ValidationResult):
```json
{
  "validation_id": "validation_1776024000_001",
  "result_id": "result_1776024000_001",
  "metadata_completeness": true,
  "metadata_issues": [],
  "url_valid": true,
  "url_invalid": [],
  "relevance_score": 0.85,
  "relevance_assessment": "high",
  "passes_criteria": true,
  "validation_timestamp": "2026-04-13T01:00:01Z"
}
```

**Validation Criteria**:
- All chunks have required metadata fields (source_url, section, chunk_index)
- Source URLs are valid URL format
- Similarity scores are within expected range (>0.5 for relevance)
- Content is non-empty for all chunks

---

## Function: test_determinism

**Description**: Verify that the same query returns identical results across multiple runs

**Input**:
- `query_text` (string, required): The query to test
- `num_runs` (integer, optional, default=5): Number of times to run the query
- `top_k` (integer, optional, default=5): Number of results per query

**Output**:
```json
{
  "query_text": "What is ROS 2?",
  "num_runs": 5,
  "determinism_verified": true,
  "results_match": true,
  "mismatches": []
}
```

**Validation**:
- All runs must return same number of results
- Results must have identical chunk_ids in same order
- Similarity scores must be identical across runs

---

## Function: run_validation_session

**Description**: Execute a complete validation session with multiple queries

**Input**:
- `queries` (list[string], required): List of query texts to test
- `top_k` (integer, optional, default=5): Results per query
- `test_determinism` (boolean, optional, default=False): Whether to run determinism tests

**Output** (QuerySession):
```json
{
  "session_id": "session_1776024000",
  "start_time": "2026-04-13T01:00:00Z",
  "end_time": "2026-04-13T01:05:00Z",
  "status": "completed",
  "total_queries": 5,
  "successful_queries": 5,
  "failed_queries": 0,
  "avg_execution_time_ms": 892,
  "avg_relevance_score": 0.87,
  "determinism_verified": true,
  "qdrant_collection": "book_vectors",
  "collection_vector_count": 53
}
```

**Success Criteria**:
- All queries execute without errors
- Average relevance score >= 0.7
- Metadata completeness = 100%
- URL validity = 100%
- Execution time < 2000ms per query
