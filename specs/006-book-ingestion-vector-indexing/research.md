# Research: Book Content Ingestion & Vector Indexing

**Feature**: 006-book-ingestion-vector-indexing
**Date**: 2026-04-08

## Decision 1: URL Discovery Strategy

**Context**: Need to discover all public page URLs from a Docusaurus book hosted on GitHub Pages.

**Decision**: Use sitemap.xml discovery as primary method, with HTML crawling as fallback.

**Rationale**: 
- Docusaurus generates `sitemap.xml` by default at the root URL
- Sitemap provides complete URL list in one request (efficient)
- Fallback: crawl navigation sidebar if sitemap is unavailable
- Docusaurus sitemaps follow standard format: `<loc>https://example.com/page</loc>`

**Alternatives considered**:
1. Hardcode URL list - rejected (not maintainable)
2. Full site crawling (recursive link following) - rejected (complex, risk of infinite loops)
3. GitHub repository file listing - rejected (doesn't match deployed URL structure)

**Implementation approach**:
```python
async def get_urls(book_base_url: str) -> list[str]:
    # Try sitemap.xml first
    sitemap_url = f"{book_base_url}/sitemap.xml"
    response = await httpx.AsyncClient().get(sitemap_url)
    if response.status_code == 200:
        return parse_sitemap(response.text)
    
    # Fallback: crawl homepage for navigation links
    return await crawl_navigation(book_base_url)
```

---

## Decision 2: HTML Text Extraction Method

**Context**: Need to extract clean text from Docusaurus HTML pages, removing navigation, sidebars, footers, and boilerplate.

**Decision**: Use BeautifulSoup4 with Docusaurus-specific CSS selectors.

**Rationale**:
- Docusaurus has consistent HTML structure with semantic CSS classes
- Main content is in `<article class="markdown">` or `<div class="theme-doc-markdown">`
- BeautifulSoup4 is lightweight, well-tested, and sufficient for this task
- Alternative: Readability libraries (better for arbitrary HTML, overkill for known structure)

**Key selectors for Docusaurus**:
```python
# Target main content area
content_selectors = [
    "article.markdown",           # Docusaurus v2/v3
    "div.theme-doc-markdown",    # Alternative selector
    "main .container",           # Generic fallback
]

# Remove these elements
noise_selectors = [
    "nav",                        # Navigation bar
    "aside",                      # Sidebar
    "footer",                     # Footer
    ".theme-doc-toc-mobile",     # Table of contents (mobile)
    ".theme-doc-toc-desktop",    # Table of contents (desktop)
    ".pagination-nav",           # Previous/Next navigation
    "script", "style",           # Scripts and styles
]
```

**Alternatives considered**:
1. trafilatura - rejected (general-purpose, may remove valid content)
2. readability-lxml - rejected (designed for articles, not documentation sites)
3. Regex-based extraction - rejected (fragile, hard to maintain)

---

## Decision 3: Text Chunking Strategy

**Context**: Need to split extracted text into chunks appropriate for embedding generation.

**Decision**: Use token-based chunking with 500-1000 token chunks and 10% overlap.

**Rationale**:
- Cohere embedding models handle up to 512 tokens (embed-english-v3.0) or 4000 tokens (embed-english-light-v3.0)
- 500-1000 token chunks balance granularity with context preservation
- 10% overlap (50-100 tokens) ensures semantic continuity across chunk boundaries
- Simple character-level splitting with token estimation is sufficient (no need for exact tokenization)

**Implementation approach**:
```python
def chunk_text(text: str, metadata: dict, chunk_size: int = 800, overlap: int = 80) -> list[dict]:
    """Split text into chunks with overlap, preserving metadata."""
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        chunks.append({
            "text": chunk,
            "metadata": {
                **metadata,
                "chunk_index": chunk_index,
                "start_char": start,
                "end_char": end,
            }
        })
        
        start = end - overlap
        chunk_index += 1
    
    return chunks
```

**Alternatives considered**:
1. Semantic chunking (sentence/paragraph boundaries) - rejected (complex, marginal benefit)
2. Fixed character splitting - rejected (may cut mid-sentence)
3. Recursive chunking (by headers, then paragraphs) - rejected (overkill for this use case)

---

## Decision 4: Cohere Embedding Model Selection

**Context**: Need to select appropriate Cohere embedding model for book content.

**Decision**: Use `embed-english-v3.0` for highest quality embeddings.

**Rationale**:
- `embed-english-v3.0`: 1024 dimensions, best quality, 512 token limit
- `embed-english-light-v3.0`: 384 dimensions, faster, 4000 token limit
- Book content benefits from higher dimensionality (technical terminology, complex concepts)
- Free tier limits: 5 calls/minute, 100 calls/minute burst - acceptable for batch processing with rate limiting

**Rate limiting strategy**:
```python
import asyncio
from cohere import Client

async def generate_embeddings(chunks: list[dict], api_key: str) -> list[list[float]]:
    cohere = Client(api_key=api_key)
    embeddings = []
    
    for i in range(0, len(chunks), 96):  # Batch size (96 texts per request)
        batch = chunks[i:i+96]
        texts = [chunk["text"] for chunk in batch]
        
        response = cohere.embed(texts=texts, model="embed-english-v3.0")
        embeddings.extend(response.embeddings)
        
        if i + 96 < len(chunks):
            await asyncio.sleep(12)  # Rate limit: 5 requests/minute
    
    return embeddings
```

**Alternatives considered**:
1. OpenAI embeddings (text-embedding-3-small) - rejected (spec requires Cohere)
2. Sentence Transformers (local models) - rejected (spec requires Cohere)
3. `embed-english-light-v3.0` - rejected (lower quality for technical content)

---

## Decision 5: Qdrant Cloud Storage Configuration

**Context**: Need to configure Qdrant Cloud client for vector storage with metadata.

**Decision**: Use Qdrant Cloud Free Tier with in-memory batching and single collection.

**Rationale**:
- Free tier: 1GB storage, 1 collection - sufficient for ~100 pages (estimated 50-200MB)
- Use `models.Distance.COSINE` for semantic similarity
- Payload (metadata) stored with each vector: URL, section title, chunk index
- Collection name: `book_knowledge_base` (descriptive, single collection)

**Implementation approach**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct
)

def store_vectors(embeddings: list[list[float]], metadata: list[dict], qdrant_url: str, api_key: str):
    client = QdrantClient(url=qdrant_url, api_key=api_key)
    
    # Create collection if not exists
    collections = client.get_collections().collections
    if "book_knowledge_base" not in [c.name for c in collections]:
        client.create_collection(
            collection_name="book_knowledge_base",
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
    
    # Prepare points
    points = [
        PointStruct(
            id=i,  # Simple sequential ID
            vector=embedding,
            payload=meta,
        )
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata))
    ]
    
    # Upsert in batches
    client.upsert(collection_name="book_knowledge_base", points=points)
```

**Metadata schema**:
```python
{
    "url": "https://example.com/docs/chapter1",
    "section": "Chapter 1: Introduction",
    "chunk_index": 0,
    "start_char": 0,
    "end_char": 800,
    "ingestion_date": "2026-04-08",
}
```

**Alternatives considered**:
1. Pinecone - rejected (spec requires Qdrant)
2. Weaviate - rejected (spec requires Qdrant)
3. Multiple collections (by chapter) - rejected (Free tier allows 1 collection)

---

## Decision 6: Error Handling and Retries

**Context**: Need robust error handling for network failures, API limits, and invalid pages.

**Decision**: Implement exponential backoff retries with configurable max attempts.

**Rationale**:
- Transient failures (network timeouts, 429 rate limits) are common in batch processing
- Exponential backoff: 1s → 2s → 4s → 8s (max 4 retries)
- Skip invalid pages with warnings (don't abort entire pipeline)
- Log all failures for post-run review

**Implementation approach**:
```python
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=8))
async def fetch_with_retry(url: str) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response
```

**Alternatives considered**:
1. No retries (fail fast) - rejected (fragile for batch processing)
2. Manual retry loops - rejected (complex, error-prone)
3. tenacity library - ✅ selected (clean decorator-based approach)

---

## Summary of Technology Choices

| Component | Choice | Justification |
|-----------|--------|---------------|
| HTTP Client | httpx | Async support, modern API, timeout handling |
| HTML Parser | BeautifulSoup4 | Mature, CSS selectors, Docusaurus-compatible |
| Embedding Model | Cohere embed-english-v3.0 | Highest quality, spec requirement |
| Vector Database | Qdrant Cloud Free Tier | Spec requirement, sufficient capacity |
| Retry Logic | tenacity | Clean decorator API, exponential backoff |
| Environment Config | python-dotenv | Standard pattern, .env file support |

## Estimated Costs (Free Tier Limits)

| Service | Limit | Estimated Usage | Within Limit? |
|---------|-------|-----------------|---------------|
| Cohere API | 5 req/min, 100 req/min burst | ~10-20 batches (100 pages) | ✅ Yes (with rate limiting) |
| Qdrant Cloud | 1GB storage, 1 collection | ~50-200MB (1000-5000 vectors) | ✅ Yes |
| GitHub Pages | No strict limits, 429 on abuse | ~100 page fetches | ✅ Yes |
