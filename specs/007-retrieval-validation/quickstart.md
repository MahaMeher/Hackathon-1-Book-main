# Quickstart: Retrieval Validation & Pipeline Testing

## Prerequisites

- Python 3.9 or higher
- Existing Qdrant Cloud collection with vectors (from Spec 1 - Book Ingestion)
- Cohere API key (same as used in Spec 1)
- Qdrant Cloud cluster URL and API key (same as Spec 1)

## Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Ensure dependencies are installed** (already configured in Spec 1):
   ```bash
   pip install -q qdrant-client cohere python-dotenv
   ```

3. **Verify .env file exists** in root directory with:
   ```env
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   BOOK_BASE_URL=https://hackathon-1-book-chi.vercel.app/
   ```

## Usage

### Basic Usage - Run Default Validation

```bash
python retrieved.py
```

This will:
- Connect to Qdrant Cloud collection
- Run 5 default test queries covering all 4 book modules
- Retrieve top-5 results for each query
- Validate metadata and relevance
- Display results in console

### Custom Query Testing

```bash
python retrieved.py --query "What is ROS 2?"
```

### Configure Number of Results

```bash
python retrieved.py --top-k 10
```

### Multiple Queries from File

Create a file `queries.txt` with one query per line:
```
What is ROS 2?
Explain digital twin technology
How does Isaac Sim work?
What are collaborative robots?
```

Run:
```bash
python retrieved.py --queries-file queries.txt
```

### Export Results to JSON

```bash
python retrieved.py --output results.json
```

### Determinism Testing

```bash
python retrieved.py --test-determinism --query "ROS 2 communication"
```

This will run the same query 5 times and verify identical results.

### Verbose Output

```bash
python retrieved.py --verbose
```

## Configuration

All configuration via environment variables (from `.env` file):

**Required**:
- `COHERE_API_KEY`: Cohere API key for query embeddings
- `QDRANT_URL`: Qdrant Cloud cluster URL
- `QDRANT_API_KEY`: Qdrant API key

**Optional**:
- `COLLECTION_NAME`: Qdrant collection name (default: "book_vectors")
- `QUERY_TOP_K`: Number of results per query (default: 5)

## Command-Line Options

```
--query TEXT            Single test query
--queries-file FILE     File with multiple queries (one per line)
--top-k INT             Number of results to retrieve (default: 5)
--output FILE           Export results to JSON file
--test-determinism      Test deterministic behavior
--verbose               Show detailed output
--help                  Show help message
```

## Expected Output

### Console Output Example

```
============================================================
RETRIEVAL VALIDATION TEST
============================================================
Collection: book_vectors (53 vectors)
============================================================

Query 1: What is ROS 2?
Execution Time: 847ms (Embedding: 312ms, Search: 535ms)
Results: 5 chunks retrieved

  [1] Score: 0.723 | Section: docs/module1
      URL: https://hackathon-1-book-chi.vercel.app/docs/module1/chapter1-ros2-fundamentals.html
      Content: "ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software..."
      Metadata: ✓ Complete

  [2] Score: 0.681 | Section: docs/module1
      URL: https://hackathon-1-book-chi.vercel.app/docs/module1/chapter2-ros2-communication.html
      Content: "ROS 2 provides several communication mechanisms including topics, services, and actions..."
      Metadata: ✓ Complete

  ...

Validation:
  Metadata Completeness: ✓ PASS (5/5 complete)
  URL Validity: ✓ PASS (5/5 valid)
  Relevance: HIGH
  Passes Criteria: ✓ YES

============================================================
VALIDATION SUMMARY
============================================================
Total Queries: 5
Successful: 5
Failed: 0
Average Execution Time: 892ms
Average Relevance Score: 0.87
Determinism Verified: ✓ YES
============================================================
✅ All validation tests passed!
```

### JSON Output Structure

```json
{
  "session_id": "session_1776024000",
  "timestamp": "2026-04-13T01:00:00Z",
  "collection": "book_vectors",
  "total_vectors": 53,
  "queries": [
    {
      "query_text": "What is ROS 2?",
      "execution_time_ms": 847,
      "top_k": 5,
      "results": [
        {
          "chunk_id": "...",
          "similarity_score": 0.723,
          "content": "...",
          "source_url": "...",
          "section": "docs/module1",
          "chunk_index": 0
        }
      ],
      "validation": {
        "metadata_completeness": true,
        "url_valid": true,
        "relevance_score": 0.85,
        "relevance_assessment": "high",
        "passes_criteria": true
      }
    }
  ],
  "summary": {
    "total_queries": 5,
    "successful_queries": 5,
    "failed_queries": 0,
    "avg_execution_time_ms": 892,
    "avg_relevance_score": 0.87,
    "determinism_verified": true
  }
}
```

## Validation Tests

The retrieval validation tests verify:

1. **Semantic Search Quality**: Retrieved chunks are topically relevant to queries
2. **Metadata Completeness**: All results include required metadata fields
3. **Source Traceability**: Source URLs can be traced back to ingested content
4. **Performance**: Query execution meets latency targets (<2s)
5. **Determinism**: Same query returns same results across runs

## Troubleshooting

### Connection Errors

**Issue**: "Failed to connect to Qdrant"
**Solution**: 
- Verify QDRANT_URL and QDRANT_API_KEY in .env
- Ensure Qdrant Cloud cluster is accessible
- Check network connection

### Embedding Errors

**Issue**: "Failed to generate embeddings"
**Solution**:
- Verify COHERE_API_KEY is correct and active
- Check API quota/limits on Cohere account

### No Results Found

**Issue**: "0 chunks retrieved"
**Solution**:
- Verify Qdrant collection has vectors (run ingestion from Spec 1 first)
- Check COLLECTION_NAME matches your ingested collection
- Try different query terms

### Poor Relevance Scores

**Issue**: All results show "LOW" relevance
**Solution**:
- Collection may not be properly populated - re-run ingestion
- Query terms may not be well-represented in book content
- Try more specific queries aligned with book topics
