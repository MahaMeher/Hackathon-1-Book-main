# Book Content Ingestion Pipeline

This project implements a complete pipeline for ingesting content from deployed Docusaurus books, generating semantic embeddings, and storing them in a vector database for later RAG (Retrieval Augmented Generation) use.

## Features

- Fetches content from Vercel-hosted Docusaurus books
- Extracts clean text content, removing navigation and layout elements
- Chunks text into appropriate segments for embedding
- Generates semantic embeddings using Cohere
- Stores vectors in Qdrant Cloud with metadata (URL, section, chunk index)
- Provides comprehensive logging and monitoring

## Prerequisites

- Python 3.12+
- `uv` package manager
- Cohere API key
- Qdrant Cloud cluster URL and API key

## Setup

1. Install dependencies:
   ```bash
   cd backend
   uv sync
   ```

2. Set up environment variables by creating a `.env` file:
   ```env
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   BOOK_URL=https://your-book.vercel.app
   ```

## Usage

Run the ingestion pipeline:
```bash
uv run python main.py
```

## Architecture

The pipeline follows these steps:
1. Discover all URLs in the Docusaurus book
2. Fetch HTML content from each page
3. Extract clean text content
4. Chunk text into appropriate segments
5. Generate semantic embeddings using Cohere
6. Store vectors in Qdrant Cloud with metadata
7. Log all operations for verification

## Configuration

The pipeline can be configured through environment variables. Key parameters like chunk size and timeout values can be adjusted in the code as needed.

## Output

After successful execution, the pipeline will:
- Store all vectors in a Qdrant collection named "book_embeddings"
- Include metadata (URL, section, chunk index) with each vector
- Provide comprehensive logs of the ingestion process