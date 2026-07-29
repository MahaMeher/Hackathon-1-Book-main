"""
Book Content Ingestion & Vector Indexing Pipeline

This module implements an automated pipeline that fetches content from a deployed
Docusaurus book on Vercel, processes the text, generates semantic embeddings using
Cohere, and stores the vectors in Qdrant Cloud.
"""

import os
import re
import time
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

# Load environment variables from .env file in root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes (T011)
# ============================================================================

@dataclass
class BookContent:
    """Represents the fetched Docusaurus book pages with their original URLs and structural information"""
    url: str
    html_content: str
    title: str
    fetched_at: datetime
    status_code: int
    content_hash: str

    def __post_init__(self):
        if not self.url:
            raise ValueError("URL must be provided")
        if not self.html_content:
            raise ValueError("HTML content must not be empty")
        if self.status_code != 200:
            raise ValueError(f"Status code must be 200, got {self.status_code}")


@dataclass
class TextChunk:
    """Represents a segment of extracted and normalized text from the book content"""
    id: str
    content: str
    source_url: str
    section: str
    chunk_index: int
    word_count: int
    char_count: int
    created_at: datetime

    def __post_init__(self):
        if not (100 <= len(self.content) <= 5000):
            logger.warning(f"Chunk content length {len(self.content)} is outside recommended range (100-5000)")
        if self.chunk_index < 0:
            raise ValueError("Chunk index must be non-negative")


@dataclass
class EmbeddingVector:
    """Represents the semantic vector representation of a text chunk"""
    vector_id: str
    vector: List[float]
    text_chunk_id: str
    source_url: str
    section: str
    chunk_index: int
    model_used: str
    generated_at: datetime
    content: str = ""  # Actual text content for RAG retrieval


@dataclass
class IngestionRun:
    """Represents a complete ingestion pipeline execution"""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    pages_fetched: int = 0
    pages_failed: int = 0
    chunks_created: int = 0
    vectors_stored: int = 0
    total_duration_ms: Optional[int] = None

    def __post_init__(self):
        if self.status not in ["running", "completed", "failed"]:
            raise ValueError(f"Invalid status: {self.status}")
        if self.pages_fetched < 0 or self.pages_failed < 0:
            raise ValueError("Count values must be non-negative")


# ============================================================================
# Configuration (T012)
# ============================================================================

class Config:
    """Configuration loading from environment variables"""
    
    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.book_base_url = os.getenv("BOOK_BASE_URL", "https://hackathon-1-book-chi.vercel.app/")
        self.collection_name = os.getenv("COLLECTION_NAME", "book_vectors")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "3000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.embedding_model = "embed-english-v3.0"
        self.vector_size = 1024  # Cohere embed-english-v3.0 dimensionality
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
    def validate(self):
        """Validate required configuration"""
        missing = []
        if not self.cohere_api_key:
            missing.append("COHERE_API_KEY")
        if not self.qdrant_url:
            missing.append("QDRANT_URL")
        if not self.qdrant_api_key:
            missing.append("QDRANT_API_KEY")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Ensure base URL ends with /
        if not self.book_base_url.endswith('/'):
            self.book_base_url += '/'
        
        return True


# ============================================================================
# Book Ingestion Pipeline (T015)
# ============================================================================

class BookIngestionPipeline:
    """Main pipeline for book content ingestion and vector indexing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cohere_client = None
        self.qdrant_client = None
        self.ingestion_run: Optional[IngestionRun] = None
        
        # Initialize clients
        self._init_cohere()
        self._init_qdrant()
    
    def _init_cohere(self):
        """Initialize Cohere client (T013)"""
        try:
            self.cohere_client = cohere.Client(self.config.cohere_api_key)
            logger.info("Cohere client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cohere client: {e}")
            raise
    
    def _init_qdrant(self):
        """Initialize Qdrant client (T014)"""
        try:
            # Parse URL to extract host and port
            parsed = urlparse(self.config.qdrant_url)
            host = parsed.hostname
            port = parsed.port or 6333
            https = parsed.scheme == 'https'
            
            self.qdrant_client = QdrantClient(
                url=self.config.qdrant_url,
                api_key=self.config.qdrant_api_key,
                https=https,
                port=port
            )
            logger.info("Qdrant client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise
    
    # ========================================================================
    # URL Discovery & Content Fetching (US1)
    # ========================================================================
    
    def discover_book_urls(self, base_url: str) -> List[str]:
        """
        Discover all pages in the Docusaurus book by parsing sitemap.xml (T020)
        
        Args:
            base_url: Base URL of the Docusaurus book
            
        Returns:
            List of URLs found in sitemap (converted to .html format for static export)
        """
        logger.info(f"Discovering URLs from sitemap at {base_url}")
        
        sitemap_url = urljoin(base_url, "sitemap.xml")
        
        try:
            response = requests.get(sitemap_url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            # Parse sitemap XML
            soup = BeautifulSoup(response.content, 'xml')
            urls = []
            
            # Extract all URLs from <loc> tags
            for loc in soup.find_all('loc'):
                url = loc.get_text().strip()
                if url:
                    # Convert to .html format for Vercel static export
                    # Docusaurus on Vercel serves pages with .html extension
                    if not url.endswith('.html'):
                        # Don't add .html to root URL
                        parsed = urlparse(url)
                        if parsed.path and parsed.path != '/':
                            url = url + '.html'
                    urls.append(url)
            
            logger.info(f"Discovered {len(urls)} URLs from sitemap")
            return urls
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse sitemap: {e}")
            raise
    
    def fetch_book_content(self, url: str) -> BookContent:
        """
        Fetch HTML content from a URL with error handling and retry logic (T021, T022)
        
        Args:
            url: URL to fetch
            
        Returns:
            BookContent object with fetched content
        """
        logger.info(f"Fetching content from {url}")
        
        # Browser-like headers to avoid 404 on SPA sites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',  # No 'br' (brotli) — not supported by requests without brotli lib
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        for attempt in range(self.config.max_retries):
            try:
                # Add small delay to simulate browser behavior
                if attempt > 0:
                    time.sleep(2)
                
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.config.request_timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Small delay after receiving response to ensure full render
                time.sleep(1)
                
                # Generate content hash for change detection
                content_hash = hashlib.sha256(response.content).hexdigest()
                
                # Extract title
                title = self._extract_title(response.content)
                
                book_content = BookContent(
                    url=url,
                    html_content=response.text,
                    title=title,
                    fetched_at=datetime.now(timezone.utc),
                    status_code=response.status_code,
                    content_hash=content_hash
                )
                
                logger.info(f"Successfully fetched content from {url} (title: {title})")
                return book_content
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.config.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.config.max_retries} attempts")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _extract_title(self, html_content: str) -> str:
        """
        Extract page title from HTML content (T023)
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Page title or 'Untitled' if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                return title_tag.string.strip()
            
            # Fallback to h1 tag
            h1_tag = soup.find('h1')
            if h1_tag and h1_tag.string:
                return h1_tag.string.strip()
            
            return "Untitled"
        except Exception as e:
            logger.warning(f"Failed to extract title: {e}")
            return "Untitled"
    
    # ========================================================================
    # Text Extraction (US1)
    # ========================================================================
    
    def extract_text_content(self, book_content: BookContent) -> str:
        """
        Extract clean text from HTML, removing navigation and layout elements (T025, T026, T027)

        Args:
            book_content: BookContent object with HTML

        Returns:
            Clean extracted text
        """
        logger.info(f"Extracting text content from {book_content.url}")

        try:
            # Parse with explicit encoding handling
            soup = BeautifulSoup(book_content.html_content, 'lxml')
            
            # Remove navigation, header, footer, and sidebar elements
            # Docusaurus-specific selectors
            for selector in [
                'nav', 'header', 'footer', '.navbar',
                '.sidebar', '.menu', '.toc', '.table-of-contents',
                'script', 'style', 'noscript',
                '.theme-doc-toc', '.theme-doc-sidebar',
                '[class*="navbar"]', '[class*="sidebar"]',
                '[class*="footer"]', '[class*="header"]'
            ]:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract main content from Docusaurus content containers
            # Try Docusaurus-specific selectors first
            content_selectors = [
                '.markdown',
                '.theme-doc-markdown',
                'article',
                '.container',
                'main',
                '[class*="docMainContainer"]',
                '[class*="mdx"]'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    logger.info(f"Found content using selector: {selector}")
                    break
            
            if not content_element:
                # Fallback to body
                content_element = soup.find('body')
                if not content_element:
                    content_element = soup
            
            # Extract text and clean it
            text = content_element.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
            # Remove Unicode format characters (zero-width spaces, soft hyphens, BOM, etc.)
            import unicodedata
            text = ''.join(c for c in text if unicodedata.category(c) != 'Cf')
            text = text.strip()
            
            logger.info(f"Extracted {len(text)} characters of text")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text content: {e}")
            raise
    
    # ========================================================================
    # Text Chunking (US1)
    # ========================================================================
    
    def chunk_text(self, text: str, source_url: str, section: str) -> List[TextChunk]:
        """
        Split text into appropriate chunks for embedding (T030, T031, T032)

        Args:
            text: Text to chunk
            source_url: Source URL for metadata
            section: Section name for metadata

        Returns:
            List of TextChunk objects
        """
        logger.info(f"Chunking text from {source_url} (section: {section})")

        # Ensure text is a proper UTF-8 string
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        text = str(text).strip()

        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        # Split text into chunks with overlap
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at word boundary
            if end < len(text):
                # Look for last space before end
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk_content = text[start:end].strip()

            # Ensure chunk content is clean UTF-8
            chunk_content = chunk_content.encode('utf-8', errors='replace').decode('utf-8')

            # Only create chunk if it meets minimum size
            if len(chunk_content) >= 100:
                chunk_id = f"{hashlib.md5(f'{source_url}_{chunk_index}'.encode()).hexdigest()}_{chunk_index}"
                
                chunk = TextChunk(
                    id=chunk_id,
                    content=chunk_content,
                    source_url=source_url,
                    section=section,
                    chunk_index=chunk_index,
                    word_count=len(chunk_content.split()),
                    char_count=len(chunk_content),
                    created_at=datetime.now(timezone.utc)
                )
                
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - overlap
        
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def _extract_section_from_url(self, url: str, base_url: str) -> str:
        """
        Extract section name from URL path (T032)
        
        Args:
            url: Full URL
            base_url: Base URL to strip
            
        Returns:
            Section name extracted from URL
        """
        try:
            # Remove base URL
            path = url.replace(base_url, '')
            
            # Remove leading/trailing slashes
            path = path.strip('/')
            
            # Split by / and get first meaningful part
            parts = path.split('/')
            if len(parts) >= 2:
                # Return first two parts (e.g., "docs/module1")
                return '/'.join(parts[:2])
            elif len(parts) == 1:
                return parts[0]
            
            return "root"
        except Exception as e:
            logger.warning(f"Failed to extract section from URL: {e}")
            return "unknown"
    
    # ========================================================================
    # Embedding Generation (US2)
    # ========================================================================
    
    def generate_embeddings(self, chunks: List[TextChunk]) -> List[EmbeddingVector]:
        """
        Generate semantic embeddings using Cohere API (T040, T041, T042)

        Args:
            chunks: List of TextChunk objects

        Returns:
            List of EmbeddingVector objects
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Debug: Check first chunk content
        if chunks:
            logger.info(f"First chunk content type: {type(chunks[0].content)}")
            logger.info(f"First chunk first 100 chars: {chunks[0].content[:100]}")
            logger.info(f"First chunk repr first 100: {repr(chunks[0].content[:100])}")

        embeddings = []
        batch_size = 96  # Cohere batch limit
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]
            
            try:
                # Generate embeddings using Cohere
                response = self.cohere_client.embed(
                    texts=texts,
                    model=self.config.embedding_model,
                    input_type="search_document"
                )
                
                # Create embedding vectors
                for idx, (chunk, vector) in enumerate(zip(batch, response.embeddings)):
                    # Ensure content is clean UTF-8 string
                    content = chunk.content
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='replace')
                    content = str(content).strip()
                    
                    embedding = EmbeddingVector(
                        vector_id=f"vec_{chunk.id}",
                        vector=vector,
                        text_chunk_id=chunk.id,
                        source_url=chunk.source_url,
                        section=chunk.section,
                        chunk_index=chunk.chunk_index,
                        model_used=self.config.embedding_model,
                        generated_at=datetime.now(timezone.utc),
                        content=content  # Include actual text content for RAG retrieval
                    )
                    embeddings.append(embedding)
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1} ({len(batch)} chunks)")
                
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {e}")
                raise
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    # ========================================================================
    # Vector Storage (US2)
    # ========================================================================
    
    def create_collection(self, collection_name: str):
        """
        Create Qdrant collection with proper vector dimensions (T046)
        
        Args:
            collection_name: Name of the collection to create
        """
        logger.info(f"Creating Qdrant collection: {collection_name}")
        
        try:
            # Check if collection already exists
            collections = self.qdrant_client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists, skipping creation")
                return
            
            # Create collection
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Successfully created collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
            raise
    
    def store_vectors_in_qdrant(self, embeddings: List[EmbeddingVector], collection_name: str):
        """
        Store embeddings in Qdrant Cloud with metadata (T045, T047, T048)
        
        Args:
            embeddings: List of EmbeddingVector objects
            collection_name: Name of the collection to store in
        """
        logger.info(f"Storing {len(embeddings)} vectors in Qdrant collection: {collection_name}")
        
        try:
            # Prepare points for Qdrant
            points = []
            for embedding in embeddings:
                # Ensure content is clean UTF-8 string before storage
                content = embedding.content
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                content = str(content).strip()
                
                if not content:
                    logger.warning(f"Empty content for embedding {embedding.vector_id}")
                
                # Convert string ID to UUID format for Qdrant
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, embedding.vector_id))

                point = PointStruct(
                    id=point_id,
                    vector=embedding.vector,
                    payload={
                        "text_chunk_id": embedding.text_chunk_id,
                        "source_url": embedding.source_url,
                        "section": embedding.section,
                        "chunk_index": embedding.chunk_index,
                        "model_used": embedding.model_used,
                        "generated_at": embedding.generated_at.isoformat(),
                        "vector_id": embedding.vector_id,
                        "content": content  # Store actual text content for RAG retrieval
                    }
                )
                points.append(point)
            
            # Debug: Verify first point's content before upsert
            if points:
                first_content = points[0].payload.get("content", "")
                logger.info(f"First point content type: {type(first_content)}")
                logger.info(f"First 100 chars: {first_content[:100]}")
            
            # Upsert points into Qdrant
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Successfully stored {len(points)} vectors in Qdrant")
            
        except Exception as e:
            logger.error(f"Failed to store vectors in Qdrant: {e}")
            raise
    
    # ========================================================================
    # Logging & Pipeline Orchestration (US3)
    # ========================================================================
    
    def run_ingestion_pipeline(self, base_url: str) -> IngestionRun:
        """
        Orchestrate the complete ingestion pipeline (T055, T056, T057)
        
        Args:
            base_url: Base URL of the Docusaurus book
            
        Returns:
            IngestionRun object with execution statistics
        """
        # Create ingestion run record
        run_id = f"run_{int(time.time())}"
        self.ingestion_run = IngestionRun(
            run_id=run_id,
            start_time=datetime.now(timezone.utc)
        )
        
        logger.info(f"Starting ingestion pipeline (run_id: {run_id})")
        start_time = time.time()
        
        try:
            # Step 1: URL Discovery
            logger.info("Step 1: Discovering URLs...")
            urls = self.discover_book_urls(base_url)
            logger.info(f"Discovered {len(urls)} URLs")
            
            # Step 2: Fetch Content
            logger.info("Step 2: Fetching book content...")
            book_contents = []
            for url in urls:
                try:
                    content = self.fetch_book_content(url)
                    book_contents.append(content)
                    self.ingestion_run.pages_fetched += 1
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    self.ingestion_run.pages_failed += 1
            
            logger.info(f"Fetched {self.ingestion_run.pages_fetched} pages "
                       f"({self.ingestion_run.pages_failed} failed)")
            
            # Step 3: Extract Text
            logger.info("Step 3: Extracting text content...")
            all_chunks = []
            for book_content in book_contents:
                try:
                    text = self.extract_text_content(book_content)
                    section = self._extract_section_from_url(book_content.url, base_url)
                    
                    # Step 4: Chunk Text
                    chunks = self.chunk_text(text, book_content.url, section)
                    all_chunks.extend(chunks)
                    self.ingestion_run.chunks_created += len(chunks)
                except Exception as e:
                    logger.error(f"Failed to process content from {book_content.url}: {e}")
            
            logger.info(f"Created {self.ingestion_run.chunks_created} text chunks")
            
            # Step 5: Generate Embeddings
            logger.info("Step 5: Generating embeddings...")
            embeddings = self.generate_embeddings(all_chunks)
            
            # Step 6: Create Collection and Store Vectors
            logger.info("Step 6: Storing vectors in Qdrant...")
            self.create_collection(self.config.collection_name)
            self.store_vectors_in_qdrant(embeddings, self.config.collection_name)
            self.ingestion_run.vectors_stored = len(embeddings)
            
            # Mark as completed
            end_time = time.time()
            self.ingestion_run.end_time = datetime.now(timezone.utc)
            self.ingestion_run.status = "completed"
            self.ingestion_run.total_duration_ms = int((end_time - start_time) * 1000)
            
            logger.info(f"Pipeline completed successfully in {self.ingestion_run.total_duration_ms/1000:.2f}s")
            logger.info(f"Stats: {self.ingestion_run.pages_fetched} pages, "
                       f"{self.ingestion_run.chunks_created} chunks, "
                       f"{self.ingestion_run.vectors_stored} vectors")
            
            return self.ingestion_run
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            if self.ingestion_run:
                self.ingestion_run.status = "failed"
                self.ingestion_run.end_time = datetime.now(timezone.utc)
            raise


# ============================================================================
# Main Function (T056)
# ============================================================================

def main():
    """Main entry point for the ingestion pipeline"""
    logger.info("=" * 60)
    logger.info("Book Content Ingestion & Vector Indexing Pipeline")
    logger.info("=" * 60)
    
    try:
        # Load and validate configuration
        config = Config()
        config.validate()
        logger.info("Configuration loaded successfully")
        
        # Create and run pipeline
        pipeline = BookIngestionPipeline(config)
        run = pipeline.run_ingestion_pipeline(config.book_base_url)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Run ID: {run.run_id}")
        logger.info(f"Status: {run.status}")
        logger.info(f"Pages Fetched: {run.pages_fetched}")
        logger.info(f"Pages Failed: {run.pages_failed}")
        logger.info(f"Chunks Created: {run.chunks_created}")
        logger.info(f"Vectors Stored: {run.vectors_stored}")
        logger.info(f"Duration: {run.total_duration_ms/1000:.2f}s")
        logger.info("=" * 60)
        
        if run.status == "completed":
            logger.info("✅ Pipeline completed successfully!")
        else:
            logger.error("❌ Pipeline failed!")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
