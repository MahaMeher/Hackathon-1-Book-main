# Book Content Ingestion & Vector Indexing Pipeline

This project implements an automated pipeline that fetches content from a deployed Docusaurus book on Vercel, processes the text, generates semantic embeddings using Cohere, and stores the vectors in Qdrant Cloud.

## Prerequisites

- Python 3.9 or higher
- Cohere API key
- Qdrant Cloud cluster URL and API key

## Setup

1. Install dependencies:
   ```bash
   pip install -r pyproject.toml
   ```

2. Create a `.env` file in the root directory with:
   ```env
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   BOOK_BASE_URL=https://hackathon-1-book-chi.vercel.app/
   ```

## Usage

Run the ingestion pipeline:

```bash
python main.py
```

## Pipeline Steps

1. **URL Discovery**: Finds all pages in the Docusaurus book
2. **Content Fetching**: Retrieves HTML content from each URL
3. **Text Extraction**: Extracts clean text, removing navigation and layout elements
4. **Text Chunking**: Splits text into appropriate segments
5. **Embedding Generation**: Creates semantic vectors using Cohere
6. **Vector Storage**: Stores embeddings in Qdrant Cloud with metadata

## Configuration

All configuration is done through environment variables (loaded from `.env` file):

- `COHERE_API_KEY`: Your Cohere API key
- `QDRANT_URL`: Your Qdrant Cloud cluster URL
- `QDRANT_API_KEY`: Your Qdrant API key
- `BOOK_BASE_URL`: Base URL of the Vercel-hosted Docusaurus book
- `COLLECTION_NAME`: (Optional) Name for the Qdrant collection (default: "book_vectors")
- `CHUNK_SIZE`: (Optional) Size of text chunks in characters (default: 3000)
- `CHUNK_OVERLAP`: (Optional) Overlap between chunks in characters (default: 200)
