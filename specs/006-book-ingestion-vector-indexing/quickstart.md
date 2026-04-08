# Quickstart: Book Content Ingestion Pipeline

**Feature**: 006-book-ingestion-vector-indexing
**Date**: 2026-04-08

## Prerequisites

- Python 3.11+ installed
- `uv` package manager installed (`pip install uv`)
- Cohere API key (free tier: https://dashboard.cohere.com/)
- Qdrant Cloud account (free tier: https://cloud.qdrant.io/)
- Deployed Docusaurus book URL on GitHub Pages

## Setup

### 1. Install Dependencies

```bash
cd backend
uv sync
```

This installs all required packages from `pyproject.toml`:
- `httpx` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `cohere` - Cohere embedding SDK
- `qdrant-client` - Qdrant Cloud client
- `python-dotenv` - Environment variable loading
- `tenacity` - Retry logic

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required: Cohere API key
COHERE_API_KEY=your-cohere-api-key

# Required: Qdrant Cloud credentials
QDRANT_URL=https://your-cluster-id.us-east.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# Required: Deployed book URL
BOOK_BASE_URL=https://username.github.io/book-name
```

### 3. Run Ingestion Pipeline

```bash
python main.py
```

The pipeline will:
1. ✅ Discover all page URLs from the book's sitemap.xml
2. 📄 Fetch each page and extract clean text
3. ✂️ Split text into chunks (500-1000 tokens each)
4. 🧠 Generate embeddings using Cohere's embed-english-v3.0 model
5. 💾 Store vectors with metadata in Qdrant Cloud

### 4. Verify Results

After successful ingestion, you'll see output like:

```
✅ Ingestion completed!
   - Pages fetched: 42/42
   - Chunks created: 1,247
   - Vectors stored: 1,247
   - Collection: book_knowledge_base
   - Duration: 12m 34s
```

### 5. Inspect Qdrant Collection

Use the Qdrant Cloud dashboard or Python client to verify:

```python
from qdrant_client import QdrantClient
import os

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
collection = client.get_collection("book_knowledge_base")
print(f"Vector count: {collection.vectors_count}")
```

## Troubleshooting

### Issue: "Cohere API key not found"

**Solution**: Ensure `COHERE_API_KEY` is set in `.env` file and file is loaded.

### Issue: "Qdrant connection timeout"

**Solution**: Verify `QDRANT_URL` format includes protocol (`https://`) and port (`:6333`).

### Issue: "No URLs discovered from sitemap"

**Solution**: Check that the book URL is correct and sitemap.xml exists at `{BOOK_BASE_URL}/sitemap.xml`.

### Issue: "Rate limit exceeded (429)"

**Solution**: The pipeline includes automatic rate limiting. If you see this error, wait a few minutes and re-run.

### Issue: "Empty text extracted from page"

**Solution**: The page may have non-standard HTML structure. Check the page manually in a browser and verify it contains markdown content.

## Re-running Ingestion

The pipeline is idempotent - safe to re-run:

```bash
python main.py
```

Existing vectors will be **replaced** (upsert operation) with new embeddings from the same URLs.

## Estimated Costs

| Service | Free Tier Limit | Estimated Usage | Cost |
|---------|----------------|-----------------|------|
| Cohere API | 5 req/min | ~15 requests (100 pages) | ✅ Free |
| Qdrant Cloud | 1GB storage | ~100-200MB (1000-5000 vectors) | ✅ Free |

## Next Steps

After successful ingestion:
- The vector collection is ready for RAG retrieval
- Proceed to implementing the retrieval/query layer (separate feature)
- Set up periodic re-ingestion if book content changes
