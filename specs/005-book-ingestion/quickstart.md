# Quickstart: Book Content Ingestion & Vector Indexing

## Prerequisites

- Python 3.9 or higher
- `uv` package manager
- Cohere API key
- Qdrant Cloud cluster URL and API key

## Setup

1. **Clone the repository and navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file in the backend directory with the following:
   ```env
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   BOOK_URL=https://your-book.vercel.app
   ```

## Installation

The project uses uv for dependency management. After cloning:

```bash
# Navigate to backend
cd backend

# Install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Usage

Run the ingestion pipeline:

```bash
# Run the full ingestion pipeline
uv run python main.py

# Or run with specific parameters (if implemented)
uv run python main.py --book-url "https://your-book.vercel.app" --collection-name "book_vectors"
```

## Configuration

The pipeline can be configured through:

1. **Environment variables** (required):
   - `COHERE_API_KEY`: Your Cohere API key for generating embeddings
   - `QDRANT_URL`: Your Qdrant Cloud cluster URL
   - `QDRANT_API_KEY`: Your Qdrant API key
   - `BOOK_URL`: The base URL of the Vercel-hosted Docusaurus book

2. **Optional parameters** that can be set in main.py or via command line:
   - Chunk size parameters
   - Retry settings
   - Timeout values

## Expected Output

After running the ingestion pipeline successfully:

1. Content from all public pages of the Docusaurus book will be fetched
2. Text will be extracted and chunked appropriately
3. Embeddings will be generated using Cohere
4. Vectors will be stored in Qdrant Cloud with metadata
5. Process logs will be available showing the status of each operation
6. The Qdrant collection will contain all the vectors with proper metadata (URL, section, chunk index)

## Verification

To verify the ingestion was successful:

1. Check the logs for successful completion of all steps
2. Verify that the Qdrant collection exists and contains the expected number of vectors
3. Confirm that metadata (URL, section, chunk index) is properly associated with each vector