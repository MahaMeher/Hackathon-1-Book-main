"""
Book Content Ingestion Pipeline

This module implements a complete pipeline for:
1. Fetching content from deployed Docusaurus books on Vercel
2. Extracting and normalizing text content
3. Chunking text into appropriate segments
4. Generating Cohere embeddings
5. Storing vectors in Qdrant Cloud with metadata

The pipeline follows the requirements specified in the feature specification:
- Fetch content from Vercel-hosted Docusaurus books
- Extract clean text, removing navigation/layout elements
- Generate semantic embeddings using Cohere
- Store in Qdrant Cloud with URL, section, and chunk index metadata
"""

import asyncio
import os
import logging
import hashlib
import time
import uuid
import random
import argparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
import dotenv
import xml.etree.ElementTree as ET

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BookContent:
    """Represents fetched book page content"""
    url: str
    html_content: str
    title: str
    status_code: int
    fetched_at: float
    content_hash: str


@dataclass
class TextChunk:
    """Represents a chunk of extracted text with metadata"""
    id: str
    content: str
    source_url: str
    section: str
    chunk_index: int
    word_count: int
    char_count: int
    created_at: float


@dataclass
class EmbeddingVector:
    """Represents a semantic vector with metadata"""
    vector_id: str
    vector: List[float]
    text_chunk_id: str
    source_url: str
    section: str
    chunk_index: int
    model_used: str
    generated_at: float


class BookIngestionPipeline:
    """Main class for the book content ingestion pipeline"""

    def __init__(self):
        # Configuration from environment variables
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.book_url = os.getenv("BOOK_BASE_URL")  # GitHub Pages URL (spec 006)

        # Validate required configuration
        if not all([self.cohere_api_key, self.qdrant_url, self.qdrant_api_key, self.book_url]):
            raise ValueError("Missing required environment variables")

        # Initialize clients
        self.cohere_client = cohere.Client(self.cohere_api_key)
        self.qdrant_client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=30
        )

        # Configuration parameters
        self.max_chunk_size = 3000  # characters
        self.chunk_overlap = 200    # characters
        self.request_timeout = 30   # seconds
        self.embedding_model = "embed-english-v3.0"

        # Enhanced configuration parameters for robust URL handling
        self.enhanced_request_timeout = 60   # Longer timeout for cold starts (was 30s)
        self.max_retries = 5                # Maximum retry attempts
        self.base_delay = 1.0               # Base delay for exponential backoff (seconds)
        self.request_delay = 1.0            # Delay between requests to allow server warmup
        self.retryable_status_codes = {429, 500, 502, 503, 504}  # Temporary failures
        self.permanent_failure_codes = {400, 401, 403, 404}      # Permanent failures

        # Track ingestion run
        self.run_id = f"ingestion_{int(time.time())}"
        self.stats = {
            "pages_fetched": 0,
            "pages_failed": 0,
            "chunks_created": 0,
            "vectors_stored": 0
        }

    async def discover_book_urls(self) -> List[str]:
        """
        Discover all URLs in the Docusaurus book using the sitemap.xml and crawling
        """
        logger.info(f"Discovering URLs from: {self.book_url}")

        try:
            # Try to get URLs from sitemap.xml first
            sitemap_url = f"{self.book_url.rstrip('/')}/sitemap.xml"
            logger.info(f"Fetching sitemap from: {sitemap_url}")

            response = requests.get(sitemap_url, timeout=self.request_timeout)
            response.raise_for_status()

            # Parse the XML sitemap
            root = ET.fromstring(response.content)

            all_sitemap_urls = set()
            # Handle both default namespace and namespaced elements
            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                all_sitemap_urls.add(url.text)
            # Also try without namespace if the above didn't work
            for url in root.findall('.//loc'):
                all_sitemap_urls.add(url.text)

            logger.info(f"Discovered {len(all_sitemap_urls)} URLs from sitemap.xml")

            if all_sitemap_urls:
                # Return all sitemap URLs to be processed with retry logic during fetch
                # This is more efficient than validating each URL during discovery
                sitemap_urls = list(all_sitemap_urls)

                # Also discover additional URLs by crawling the main site
                additional_urls = await self._discover_urls_by_scraping()

                # Combine sitemap URLs with additionally discovered URLs
                all_urls = list(set(sitemap_urls + additional_urls))
                logger.info(f"Total URLs to process (with retry logic): {len(all_urls)}")
                return all_urls
            else:
                logger.warning("No URLs found in sitemap.xml, falling back to link scraping")
                # Fallback to the original method
                return await self._discover_urls_by_scraping()

        except Exception as e:
            logger.error(f"Error discovering URLs from sitemap: {e}")
            # If we can't get the sitemap, fall back to the original method
            return await self._discover_urls_by_scraping()

    async def _discover_urls_by_scraping(self) -> List[str]:
        """
        Fallback method to discover URLs by scraping the main page
        and finding internal links that point to other book pages.
        """
        logger.info(f"Discovering URLs by scraping: {self.book_url}")

        try:
            response = requests.get(self.book_url, timeout=self.request_timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all internal links that are likely to be book pages
            base_url = f"{urlparse(self.book_url).scheme}://{urlparse(self.book_url).netloc}"
            urls = set()

            # Look for navigation links in common Docusaurus navigation elements
            nav_selectors = ['nav', 'header', '.navbar', '.menu', '.sidebar', '.table-of-contents', '.theme-doc-sidebar-menu']
            for selector in nav_selectors:
                nav_elements = soup.select(selector)
                for nav_element in nav_elements:
                    for link in nav_element.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/') or base_url in href:
                            full_url = urljoin(self.book_url, href)
                            # Only include URLs that look like book pages (not assets, etc.)
                            if any(ext not in full_url.lower() for ext in ['.jpg', '.png', '.pdf', '.zip', '.css', '.js', '.ico']):
                                urls.add(full_url)

            # Look for all links on the page
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Check if it's an internal link to a potential book page
                if href.startswith('/') or base_url in href:
                    full_url = urljoin(self.book_url, href)
                    # Only include URLs that look like book pages (not assets, etc.)
                    if any(ext not in full_url.lower() for ext in ['.jpg', '.png', '.pdf', '.zip', '.css', '.js', '.ico']):
                        # Include URLs that are likely documentation pages
                        if any(part in full_url for part in ['docs', 'category', 'guide', 'tutorial', 'intro', 'module']):
                            urls.add(full_url)
                        # Also include any URLs that look like they might be documentation
                        elif '/docs/' in full_url or full_url.endswith('.html') or not any(ext in full_url for ext in ['.pdf', '.jpg', '.png', '.zip', '.css', '.js']):
                            urls.add(full_url)

            # Add the main page itself
            urls.add(self.book_url)

            # Remove duplicates by normalizing URLs (remove trailing slashes)
            normalized_urls = set()
            for url in urls:
                normalized = url.rstrip('/')
                normalized_urls.add(normalized)

            logger.info(f"Discovered {len(normalized_urls)} potential book pages by scraping")
            return list(normalized_urls)

        except Exception as e:
            logger.error(f"Error discovering URLs by scraping: {e}")
            # If we can't discover URLs, try the main URL at least
            return [self.book_url]

    async def fetch_book_content(self, url: str, max_retries: int = None, base_delay: float = None) -> Optional[BookContent]:
        """
        Fetch HTML content from a single book page URL with retry logic and exponential backoff.

        Args:
            url: The URL to fetch content from
            max_retries: Maximum number of retry attempts (uses self.max_retries if None)
            base_delay: Base delay in seconds for exponential backoff (uses self.base_delay if None)

        Returns:
            BookContent object if successful, None if failed after all retries
        """
        if max_retries is None:
            max_retries = self.max_retries
        if base_delay is None:
            base_delay = self.base_delay

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries + 1} for URL: {url}")
                start_time = time.time()

                # Apply longer timeout for cold start delays
                response = requests.get(
                    url,
                    timeout=self.enhanced_request_timeout,  # Longer timeout for cold starts
                    headers={'User-Agent': 'BookIngestionBot/1.0'}
                )

                # Check for permanent failure conditions
                if response.status_code in [400, 401, 403, 404]:
                    logger.error(f"Permanent failure for {url}: Status {response.status_code}")
                    self.stats["pages_failed"] += 1
                    return None  # Don't retry on permanent failures

                response.raise_for_status()

                html_content = response.text
                title = self._extract_title(html_content)
                content_hash = hashlib.md5(html_content.encode()).hexdigest()

                book_content = BookContent(
                    url=url,
                    html_content=html_content,
                    title=title,
                    status_code=response.status_code,
                    fetched_at=time.time(),
                    content_hash=content_hash
                )

                duration = (time.time() - start_time) * 1000
                logger.info(f"Fetched {url} in {duration:.2f}ms (attempt {attempt + 1})")

                self.stats["pages_fetched"] += 1
                return book_content

            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}: {e}")
                last_exception = e

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1} for {url}: {e}")
                last_exception = e

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                if status_code in [429]:  # Rate limit - temporary failure
                    logger.warning(f"Rate limited on attempt {attempt + 1} for {url}: {e}")
                    last_exception = e
                elif status_code in [500, 502, 503, 504]:  # Server errors - temporary failures
                    logger.warning(f"Server error on attempt {attempt + 1} for {url}: {e}")
                    last_exception = e
                elif status_code == 404:
                    # For cold start scenarios, treat 404 as potentially temporary
                    # Only consider it permanent after max retries
                    logger.debug(f"404 received on attempt {attempt + 1} for {url}, will retry for cold start")
                    last_exception = e
                else:  # Other permanent failures like 400, 401, 403
                    logger.error(f"Permanent HTTP error for {url}: {e}")
                    self.stats["pages_failed"] += 1
                    return None

            except Exception as e:
                logger.warning(f"General error on attempt {attempt + 1} for {url}: {e}")
                last_exception = e

            # Apply exponential backoff if not the last attempt
            if attempt < max_retries:
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                jitter = random.uniform(0, delay * 0.1)  # Add jitter to prevent thundering herd
                total_delay = delay + jitter

                logger.info(f"Waiting {total_delay:.2f}s before retry {attempt + 2} for {url}")
                await asyncio.sleep(total_delay)

        # All retries exhausted
        logger.error(f"Failed to fetch {url} after {max_retries + 1} attempts: {last_exception}")
        self.stats["pages_failed"] += 1
        return None

    def _extract_title(self, html_content: str) -> str:
        """Extract page title from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()

            # Fallback: look for h1 tags
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text().strip()

            return "Untitled Page"
        except:
            return "Untitled Page"

    def extract_text_content(self, book_content: BookContent) -> str:
        """
        Extract clean text content from HTML, removing navigation and layout elements.
        """
        try:
            soup = BeautifulSoup(book_content.html_content, 'html.parser')

            # Remove common navigation and layout elements
            for element in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                element.decompose()

            # Try to find the main content area (Docusaurus specific selectors)
            content_selectors = [
                'main',  # General main content
                '.main-wrapper',  # Docusaurus main wrapper
                '.container.padding-vert--lg',  # Docusaurus container
                '.theme-doc-markdown',  # Docusaurus markdown content
                '.markdown',  # General markdown class
                '.doc-content',  # Documentation content
                '.content',  # General content area
            ]

            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break

            # If no specific content area found, use the body
            if not content_element:
                content_element = soup.find('body')

            if content_element:
                # Get text and clean it up
                text = content_element.get_text(separator='\\n', strip=True)
                # Remove extra whitespace
                import re
                text = re.sub(r'\\n+', '\\n', text).strip()
                return text
            else:
                # Fallback: get all text from body
                body = soup.find('body')
                if body:
                    text = body.get_text(separator='\\n', strip=True)
                    import re
                    text = re.sub(r'\\n+', '\\n', text).strip()
                    return text
                else:
                    return ""

        except Exception as e:
            logger.error(f"Error extracting text from {book_content.url}: {e}")
            return ""

    def chunk_text(self, text: str, source_url: str, section: str = "") -> List[TextChunk]:
        """
        Split text into chunks of appropriate size for embedding.
        """
        if not text.strip():
            return []

        chunks = []
        start = 0

        while start < len(text):
            # Find the end of the chunk
            end = start + self.max_chunk_size

            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence boundaries near the end
                chunk_text = text[start:end]
                sentence_end = max(
                    chunk_text.rfind('. '),
                    chunk_text.rfind('?'),
                    chunk_text.rfind('!'),
                    chunk_text.rfind('\\n'),
                    chunk_text.rfind('\\t')
                )

                # If we found a good break point and it's not too close to the start
                if sentence_end > len(chunk_text) * 0.7:  # At least 70% through the chunk
                    end = start + sentence_end + 1
                else:
                    # Look for word boundaries instead
                    word_end = chunk_text.rfind(' ')
                    if word_end > len(chunk_text) * 0.7:
                        end = start + word_end

            chunk_content = text[start:end].strip()
            if chunk_content:  # Only add non-empty chunks
                chunk_id = f"{hashlib.md5(source_url.encode()).hexdigest()}_{self.stats['chunks_created'] + len(chunks)}_{start}"
                vector_id = f"vec_{hashlib.md5(chunk_id.encode()).hexdigest()}"

                chunk = TextChunk(
                    id=chunk_id,
                    content=chunk_content,
                    source_url=source_url,
                    section=section or self._extract_section_from_url(source_url),
                    chunk_index=self.stats['chunks_created'] + len(chunks),
                    word_count=len(chunk_content.split()),
                    char_count=len(chunk_content),
                    created_at=time.time()
                )
                chunks.append(chunk)

            # Move start position forward, with overlap if possible
            start = end - self.chunk_overlap if end < len(text) else end

            # Ensure we make progress to avoid infinite loops
            if start <= end - self.chunk_overlap:
                start = max(start, end - 100)  # Minimum progress if overlap is too large

        logger.info(f"Created {len(chunks)} chunks from {source_url}")
        return chunks

    def _extract_section_from_url(self, url: str) -> str:
        """Extract section name from URL."""
        path = urlparse(url).path
        # Remove leading and trailing slashes
        path_parts = [part for part in path.split('/') if part]
        if path_parts:
            # Return the last meaningful part of the URL path
            return path_parts[-1].replace('-', ' ').replace('_', ' ').title()
        return "Unknown Section"

    async def generate_embeddings(self, chunks: List[TextChunk]) -> List[EmbeddingVector]:
        """
        Generate embeddings for text chunks using Cohere.
        """
        if not chunks:
            return []

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Prepare texts for embedding (limit batch size for Cohere API)
        batch_size = 96  # Cohere's recommended batch size
        all_vectors = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]

            try:
                response = self.cohere_client.embed(
                    texts=texts,
                    model=self.embedding_model,
                    input_type="search_document"
                )

                # Create embedding vectors
                for idx, embedding in enumerate(response.embeddings):
                    chunk = batch[idx]
                    # Generate a UUID for the vector ID since Qdrant requires proper ID format
                    vector_uuid = str(uuid.uuid4())
                    vector = EmbeddingVector(
                        vector_id=vector_uuid,
                        vector=embedding,
                        text_chunk_id=chunk.id,
                        source_url=chunk.source_url,
                        section=chunk.section,
                        chunk_index=chunk.chunk_index,
                        model_used=self.embedding_model,
                        generated_at=time.time()
                    )
                    all_vectors.append(vector)

                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {e}")
                # Continue with remaining batches
                continue

        logger.info(f"Generated {len(all_vectors)} embedding vectors")
        return all_vectors

    async def store_vectors_in_qdrant(self, vectors: List[EmbeddingVector]) -> bool:
        """
        Store embedding vectors in Qdrant Cloud with metadata.
        """
        if not vectors:
            logger.info("No vectors to store")
            return True

        logger.info(f"Storing {len(vectors)} vectors in Qdrant")

        try:
            # Define collection name
            collection_name = "book_embeddings"

            # Check if collection exists, create if it doesn't
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} exists with config: {collection_info.config}")
            except Exception as collection_error:
                logger.info(f"Collection {collection_name} does not exist, creating it. Error: {collection_error}")
                # Get vector size from first vector
                vector_size = len(vectors[0].vector)

                logger.info(f"Creating collection {collection_name} with vector size {vector_size}")
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Collection {collection_name} created successfully")

            # Prepare points for Qdrant
            points = []
            for vector in vectors:
                point = models.PointStruct(
                    id=vector.vector_id,
                    vector=vector.vector,
                    payload={
                        "source_url": vector.source_url,
                        "section": vector.section,
                        "chunk_index": vector.chunk_index,
                        "model_used": vector.model_used,
                        "generated_at": vector.generated_at,
                        "text_chunk_id": vector.text_chunk_id
                    }
                )
                points.append(point)

            # Upload points to Qdrant
            logger.info(f"Uploading {len(points)} points to Qdrant collection {collection_name}")
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Successfully stored {len(vectors)} vectors in Qdrant collection {collection_name}")
            self.stats["vectors_stored"] += len(vectors)
            return True

        except Exception as e:
            logger.error(f"Error storing vectors in Qdrant: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    async def run_ingestion_pipeline(self):
        """
        Execute the complete ingestion pipeline.
        """
        logger.info(f"Starting ingestion pipeline run: {self.run_id}")
        start_time = time.time()

        try:
            # Step 1: Discover URLs
            urls = await self.discover_book_urls()
            logger.info(f"Discovered {len(urls)} URLs to process: {urls}")

            if not urls:
                logger.error("No URLs discovered, pipeline cannot proceed")
                return False

            # Step 2: Normalize and deduplicate URLs before fetching
            normalized_urls = set()
            for url in urls:
                # Normalize URL by removing trailing slashes and standardizing
                normalized = url.rstrip('/').lower()
                normalized_urls.add(normalized)

            logger.info(f"Deduplicated URLs from {len(urls)} to {len(normalized_urls)} unique URLs")

            # Step 3: Fetch all content with delays between requests
            all_book_contents = []
            for i, url in enumerate(normalized_urls):
                logger.info(f"Processing URL {i+1}/{len(normalized_urls)}: {url}")

                # Apply delay between requests to allow server warmup (except for first request)
                if i > 0:
                    logger.debug(f"Waiting {self.request_delay}s before fetching next URL to allow server warmup")
                    await asyncio.sleep(self.request_delay)

                content = await self.fetch_book_content(url)
                if content:
                    all_book_contents.append(content)
                    logger.info(f"Successfully fetched content from {url}")
                else:
                    logger.warning(f"Failed to fetch content from {url}")

            logger.info(f"Fetched content from {len(all_book_contents)} out of {len(normalized_urls)} URLs")

            # Step 4: Extract and chunk text for each page
            all_chunks = []
            for i, book_content in enumerate(all_book_contents):
                logger.info(f"Processing content {i+1}/{len(all_book_contents)} for {book_content.url}")
                text = self.extract_text_content(book_content)
                if text.strip():
                    logger.info(f"Extracted {len(text)} characters from {book_content.url}")
                    chunks = self.chunk_text(text, book_content.url, book_content.title)
                    all_chunks.extend(chunks)
                    logger.info(f"Created {len(chunks)} chunks from {book_content.url}")
                else:
                    logger.warning(f"No text extracted from {book_content.url}")

            logger.info(f"Created a total of {len(all_chunks)} chunks from all pages")

            # Step 4: Generate embeddings
            if all_chunks:
                logger.info(f"Starting embedding generation for {len(all_chunks)} chunks")
                embedding_vectors = await self.generate_embeddings(all_chunks)
                logger.info(f"Generated {len(embedding_vectors)} embedding vectors")
            else:
                logger.error("No chunks to process, no embeddings to generate")
                embedding_vectors = []

            # Step 5: Store in Qdrant
            if embedding_vectors:
                logger.info(f"Starting storage of {len(embedding_vectors)} vectors in Qdrant")
                success = await self.store_vectors_in_qdrant(embedding_vectors)
            else:
                logger.warning("No embedding vectors to store in Qdrant")
                success = True  # Not an error if there are no vectors to store

            # Log final statistics
            duration = time.time() - start_time
            logger.info(f"Ingestion pipeline completed in {duration:.2f}s")
            logger.info(f"Final statistics: {self.stats}")

            if success:
                logger.info("Ingestion pipeline completed successfully!")
                return True
            else:
                logger.error("Ingestion pipeline completed with storage errors")
                return False

        except Exception as e:
            logger.error(f"Ingestion pipeline failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def _is_temporary_failure(self, status_code: int) -> bool:
        """
        Determine if an HTTP status code represents a temporary failure that warrants retrying.
        """
        return status_code in self.retryable_status_codes

    def _is_permanent_failure(self, status_code: int) -> bool:
        """
        Determine if an HTTP status code represents a permanent failure that should not be retried.
        """
        return status_code in self.permanent_failure_codes

    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if a request should be retried based on the exception type.
        """
        if isinstance(exception, requests.exceptions.Timeout):
            return True
        elif isinstance(exception, requests.exceptions.ConnectionError):
            return True
        elif isinstance(exception, requests.exceptions.ChunkedEncodingError):
            return True
        else:
            return False

    async def _validate_url_with_retry(self, url: str) -> bool:
        """
        Validate a URL with retry logic to handle cold starts.
        This method tests if a URL will eventually become accessible after retries.
        """
        # Use fewer retries and shorter delays for validation to avoid long delays during discovery
        validation_max_retries = 3  # Reduced from max_retries to speed up discovery
        validation_base_delay = 2.0  # Start with 2s delay to give time for cold start

        for attempt in range(validation_max_retries + 1):
            try:
                # Use a longer timeout for validation to allow for cold starts
                response = requests.head(
                    url,
                    timeout=self.enhanced_request_timeout,
                    headers={'User-Agent': 'BookIngestionBot/1.0'}
                )

                # If we get a 200, the URL is accessible
                if response.status_code == 200:
                    return True
                # If we get a 404, we might want to retry as it could be a cold start
                elif response.status_code == 404:
                    logger.debug(f"URL {url} returned 404 on validation attempt {attempt + 1}, may be cold start")
                # For server errors (5xx), retry
                elif response.status_code in [500, 502, 503, 504]:
                    logger.debug(f"URL {url} returned {response.status_code} on validation attempt {attempt + 1}, retrying")
                # For other permanent failures, don't retry
                elif response.status_code in [400, 401, 403]:
                    logger.debug(f"URL {url} returned permanent failure {response.status_code}")
                    return False

            except requests.exceptions.Timeout:
                logger.debug(f"Timeout validating {url} on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError as e:
                logger.debug(f"Connection error validating {url} on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.debug(f"General error validating {url} on attempt {attempt + 1}: {e}")

            # Apply exponential backoff if not the last attempt
            if attempt < validation_max_retries:
                delay = validation_base_delay * (2 ** attempt)
                jitter = random.uniform(0, delay * 0.1)
                total_delay = delay + jitter
                logger.info(f"Waiting {total_delay:.2f}s before URL validation retry {attempt + 2} for {url}")
                await asyncio.sleep(total_delay)

        # All retries exhausted
        return False

    async def run_ingestion_pipeline_with_urls(self, urls: List[str]):
        """
        Execute the complete ingestion pipeline with a specific list of URLs.
        """
        logger.info(f"Starting ingestion pipeline run with specific URLs: {self.run_id}")
        start_time = time.time()

        try:
            if not urls:
                logger.error("No URLs provided, pipeline cannot proceed")
                return False

            # Step 1: Normalize and deduplicate URLs before fetching
            normalized_urls = set()
            for url in urls:
                # Normalize URL by removing trailing slashes and standardizing
                normalized = url.rstrip('/').lower()
                normalized_urls.add(normalized)

            logger.info(f"Deduplicated URLs from {len(urls)} to {len(normalized_urls)} unique URLs")

            # Step 2: Fetch all content with delays between requests
            all_book_contents = []
            for i, url in enumerate(normalized_urls):
                logger.info(f"Processing URL {i+1}/{len(normalized_urls)}: {url}")

                # Apply delay between requests to allow server warmup (except for first request)
                if i > 0:
                    logger.debug(f"Waiting {self.request_delay}s before fetching next URL to allow server warmup")
                    await asyncio.sleep(self.request_delay)

                content = await self.fetch_book_content(url)
                if content:
                    all_book_contents.append(content)
                    logger.info(f"Successfully fetched content from {url}")
                else:
                    logger.warning(f"Failed to fetch content from {url}")

            logger.info(f"Fetched content from {len(all_book_contents)} out of {len(normalized_urls)} URLs")

            # Step 3: Extract and chunk text for each page
            all_chunks = []
            for i, book_content in enumerate(all_book_contents):
                logger.info(f"Processing content {i+1}/{len(all_book_contents)} for {book_content.url}")
                text = self.extract_text_content(book_content)
                if text.strip():
                    logger.info(f"Extracted {len(text)} characters from {book_content.url}")
                    chunks = self.chunk_text(text, book_content.url, book_content.title)
                    all_chunks.extend(chunks)
                    logger.info(f"Created {len(chunks)} chunks from {book_content.url}")
                else:
                    logger.warning(f"No text extracted from {book_content.url}")

            logger.info(f"Created a total of {len(all_chunks)} chunks from all pages")

            # Step 4: Generate embeddings
            if all_chunks:
                logger.info(f"Starting embedding generation for {len(all_chunks)} chunks")
                embedding_vectors = await self.generate_embeddings(all_chunks)
                logger.info(f"Generated {len(embedding_vectors)} embedding vectors")
            else:
                logger.error("No chunks to process, no embeddings to generate")
                embedding_vectors = []

            # Step 5: Store in Qdrant
            if embedding_vectors:
                logger.info(f"Starting storage of {len(embedding_vectors)} vectors in Qdrant")
                success = await self.store_vectors_in_qdrant(embedding_vectors)
            else:
                logger.warning("No embedding vectors to store in Qdrant")
                success = True  # Not an error if there are no vectors to store

            # Log final statistics
            duration = time.time() - start_time
            logger.info(f"Ingestion pipeline completed in {duration:.2f}s")
            logger.info(f"Final statistics: {self.stats}")

            if success:
                logger.info("Ingestion pipeline completed successfully!")
                return True
            else:
                logger.error("Ingestion pipeline completed with storage errors")
                return False

        except Exception as e:
            logger.error(f"Ingestion pipeline failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Book Content Ingestion Pipeline')
    parser.add_argument('--urls', type=str, help='Comma-separated URLs to process', default=None)
    parser.add_argument('--sitemap', action='store_true', help='Use sitemap.xml to discover URLs')
    parser.add_argument('--url', type=str, help='Single URL to process (alternative to --urls)')
    return parser.parse_args()

async def main():
    """
    Main function to orchestrate the full ingestion pipeline.
    """
    args = parse_arguments()

    logger.info("Starting Book Content Ingestion Pipeline")

    try:
        pipeline = BookIngestionPipeline()

        # Override default URL if specified via command line
        if args.url:
            pipeline.book_url = args.url
        elif args.urls:
            urls_list = [url.strip() for url in args.urls.split(',')]
            if urls_list:
                pipeline.book_url = urls_list[0]  # Use first URL as base

        success = False

        if args.sitemap:
            # Override the URL discovery to use sitemap only
            urls = await pipeline.discover_book_urls()
            success = await pipeline.run_ingestion_pipeline_with_urls(urls)
        else:
            success = await pipeline.run_ingestion_pipeline()

        if success:
            logger.info("Pipeline completed successfully!")
            return 0
        else:
            logger.error("Pipeline completed with errors!")
            return 1

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
