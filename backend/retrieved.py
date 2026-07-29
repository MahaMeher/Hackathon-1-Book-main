"""
Retrieval Validation System for Qdrant Vector Database

This module implements a comprehensive retrieval validation system that queries
a Qdrant vector database using Cohere embeddings, validates retrieval results,
tests determinism, and provides detailed metrics and reporting.
"""

import os
import time
import logging
import hashlib
import uuid
import json
import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

# Load environment variables from .env file in root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class QueryEmptyError(Exception):
    """Raised when a query is empty or contains only whitespace."""
    pass


class ConnectionError(Exception):
    """Raised when connection to Qdrant or Cohere fails."""
    pass


class CollectionNotFoundError(Exception):
    """Raised when the specified Qdrant collection does not exist."""
    pass


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SearchQuery:
    """Represents a user's text query that is converted to embeddings for semantic search."""
    query_text: str
    embedding: List[float]
    model_used: str
    input_type: str
    timestamp: datetime

    def __post_init__(self):
        if not self.query_text or not self.query_text.strip():
            raise ValueError("Query text must not be empty (after stripping whitespace)")
        if len(self.embedding) != 1024:
            raise ValueError(f"Embedding must have correct dimensionality (1024 for embed-english-v3.0), got {len(self.embedding)}")


@dataclass
class RetrievedChunk:
    """Represents a text chunk retrieved from vector search, containing content and metadata."""
    chunk_id: str
    content: str
    similarity_score: float
    source_url: str
    section: str
    chunk_index: int
    model_used: str
    generated_at: str
    vector_id: Optional[str] = None

    def __post_init__(self):
        if not (-1.0 <= self.similarity_score <= 1.0):
            raise ValueError(f"Similarity score must be between -1.0 and 1.0, got {self.similarity_score}")
        if self.chunk_index < 0:
            raise ValueError(f"Chunk index must be non-negative, got {self.chunk_index}")
        if not self.content or not self.content.strip():
            raise ValueError("Content must not be empty")


@dataclass
class RetrievalResult:
    """Represents the complete result set for a query, including retrieved chunks and metadata."""
    result_id: str
    query_text: str
    query_embedding_model: str
    retrieved_chunks: List[RetrievedChunk]
    total_results: int
    execution_time_ms: int
    embedding_time_ms: int
    search_time_ms: int
    timestamp: datetime
    top_k: int

    def __post_init__(self):
        if self.total_results != len(self.retrieved_chunks):
            raise ValueError(f"Total results ({self.total_results}) must equal length of retrieved_chunks ({len(self.retrieved_chunks)})")
        if self.total_results > self.top_k:
            raise ValueError(f"Total results ({self.total_results}) must be <= top_k ({self.top_k})")
        if self.execution_time_ms < 0:
            raise ValueError("Execution time must be positive")


@dataclass
class ValidationResult:
    """Represents validation outcome for a retrieval test."""
    validation_id: str
    result_id: str
    metadata_completeness: bool
    metadata_issues: List[str]
    url_valid: bool
    url_invalid: List[str]
    relevance_score: Optional[float]
    relevance_assessment: str
    passes_criteria: bool
    validation_timestamp: datetime

    def __post_init__(self):
        if self.relevance_score is not None and not (0.0 <= self.relevance_score <= 1.0):
            raise ValueError(f"Relevance score must be between 0.0 and 1.0, got {self.relevance_score}")
        if self.relevance_assessment not in ("high", "medium", "low", "none"):
            raise ValueError(f"Relevance assessment must be one of: high, medium, low, none; got '{self.relevance_assessment}'")
        if self.passes_criteria and (not self.metadata_completeness or not self.url_valid):
            raise ValueError("If passes_criteria is True, metadata_completeness and url_valid should be True")


@dataclass
class QuerySession:
    """Represents a complete validation session with multiple queries."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_execution_time_ms: Optional[float]
    avg_relevance_score: Optional[float]
    determinism_verified: bool
    qdrant_collection: str
    collection_vector_count: int

    def __post_init__(self):
        if self.total_queries != self.successful_queries + self.failed_queries:
            raise ValueError(f"Total queries ({self.total_queries}) must equal successful ({self.successful_queries}) + failed ({self.failed_queries})")
        if self.status not in ("running", "completed", "failed"):
            raise ValueError(f"Status must be one of: running, completed, failed; got '{self.status}'")
        if self.total_queries < 0 or self.successful_queries < 0 or self.failed_queries < 0:
            raise ValueError("Count values must be non-negative")


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration loading from environment variables."""

    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("COLLECTION_NAME", "book_vectors")
        self.query_top_k = int(os.getenv("QUERY_TOP_K", "5"))
        self.embedding_model = "embed-english-v3.0"
        self.vector_size = 1024  # Cohere embed-english-v3.0 dimensionality
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))

    def validate(self):
        """Validate required configuration."""
        missing = []
        if not self.cohere_api_key:
            missing.append("COHERE_API_KEY")
        if not self.qdrant_url:
            missing.append("QDRANT_URL")
        if not self.qdrant_api_key:
            missing.append("QDRANT_API_KEY")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True


# ============================================================================
# Retrieval Validator
# ============================================================================

class RetrievalValidator:
    """Validates retrieval from Qdrant vector database using Cohere embeddings."""

    def __init__(self, config: Config):
        self.config = config
        self.cohere_client = None
        self.qdrant_client = None

        config.validate()
        self._init_cohere()
        self._init_qdrant()

    def _init_cohere(self):
        """Initialize Cohere client."""
        try:
            self.cohere_client = cohere.Client(self.config.cohere_api_key)
            logger.info("Cohere client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cohere client: {e}")
            raise ConnectionError(f"Failed to initialize Cohere client: {e}")

    def _init_qdrant(self):
        """Initialize Qdrant client and verify connection."""
        try:
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

            # Verify connection by listing collections
            self.qdrant_client.get_collections()
            logger.info("Qdrant client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise ConnectionError(f"Failed to initialize Qdrant client: {e}")

    def _generate_embedding(self, query_text: str) -> tuple[List[float], int]:
        """
        Generate embedding for query text using Cohere.

        Args:
            query_text: The text to embed.

        Returns:
            Tuple of (embedding_vector, time_taken_ms).
        """
        start_time = time.time()
        try:
            response = self.cohere_client.embed(
                texts=[query_text],
                model=self.config.embedding_model,
                input_type="search_query"
            )
            embedding = response.embeddings[0]
            elapsed_ms = int((time.time() - start_time) * 1000)
            return embedding, elapsed_ms
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    def _validate_url(self, url: str) -> bool:
        """Validate URL format using urlparse."""
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False

    def _assess_relevance(self, chunks: List[RetrievedChunk]) -> tuple[Optional[float], str]:
        """
        Assess relevance based on similarity scores.

        Returns:
            Tuple of (relevance_score, assessment).
        """
        if not chunks:
            return None, "none"

        # Use average similarity score as relevance metric
        avg_score = sum(c.similarity_score for c in chunks) / len(chunks)

        # Normalize to 0-1 range (cosine similarity is already 0-1 for positive vectors)
        normalized_score = max(0.0, min(1.0, avg_score))

        if normalized_score > 0.7:
            assessment = "high"
        elif normalized_score > 0.5:
            assessment = "medium"
        elif normalized_score > 0.3:
            assessment = "low"
        else:
            assessment = "none"

        return normalized_score, assessment

    def execute_query(self, query_text: str, top_k: Optional[int] = None, collection_name: Optional[str] = None) -> RetrievalResult:
        """
        Execute semantic search against Qdrant.

        Args:
            query_text: The search query text.
            top_k: Number of results to return (defaults to config value).
            collection_name: Qdrant collection to search (defaults to config value).

        Returns:
            RetrievalResult with timing and retrieved chunks.

        Raises:
            QueryEmptyError: If query_text is empty.
            CollectionNotFoundError: If collection does not exist.
            EmbeddingError: If embedding generation fails.
        """
        if not query_text or not query_text.strip():
            raise QueryEmptyError("Query text cannot be empty")

        top_k = top_k or self.config.query_top_k
        collection_name = collection_name or self.config.collection_name

        # Verify collection exists
        try:
            collections = self.qdrant_client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                raise CollectionNotFoundError(f"Collection '{collection_name}' not found")
        except CollectionNotFoundError:
            raise
        except Exception as e:
            raise ConnectionError(f"Failed to verify collection: {e}")

        result_id = str(uuid.uuid4())
        overall_start = time.time()

        # Step 1: Generate embedding
        try:
            embedding, embedding_time_ms = self._generate_embedding(query_text)
        except EmbeddingError:
            raise

        # Step 2: Search in Qdrant
        search_start = time.time()
        try:
            search_results = self.qdrant_client.query_points(
                collection_name=collection_name,
                query=embedding,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )

            # Convert to RetrievedChunk objects
            retrieved_chunks = []
            for hit in search_results.points:
                payload = hit.payload or {}
                # Try multiple possible content field names
                content = (payload.get("content") or 
                          payload.get("text") or 
                          payload.get("chunk_content") or 
                          payload.get("page_content") or "")
                
                chunk = RetrievedChunk(
                    chunk_id=str(hit.id),
                    content=content,
                    similarity_score=hit.score,
                    source_url=payload.get("source_url", ""),
                    section=payload.get("section", ""),
                    chunk_index=payload.get("chunk_index", 0),
                    model_used=payload.get("model_used", self.config.embedding_model),
                    generated_at=payload.get("generated_at", ""),
                    vector_id=payload.get("vector_id", str(hit.id))
                )
                retrieved_chunks.append(chunk)

            search_time_ms = int((time.time() - search_start) * 1000)
            total_time_ms = int((time.time() - overall_start) * 1000)

            # Ensure timing consistency
            if total_time_ms != embedding_time_ms + search_time_ms:
                total_time_ms = embedding_time_ms + search_time_ms

            result = RetrievalResult(
                result_id=result_id,
                query_text=query_text,
                query_embedding_model=self.config.embedding_model,
                retrieved_chunks=retrieved_chunks,
                total_results=len(retrieved_chunks),
                execution_time_ms=total_time_ms,
                embedding_time_ms=embedding_time_ms,
                search_time_ms=search_time_ms,
                timestamp=datetime.now(timezone.utc),
                top_k=top_k
            )

            logger.info(f"Query executed successfully: {len(retrieved_chunks)} results in {total_time_ms}ms")
            return result

        except Exception as e:
            logger.error(f"Failed to execute search: {e}")
            raise ConnectionError(f"Failed to execute search: {e}")

    def validate_result(self, retrieval_result: RetrievalResult) -> ValidationResult:
        """
        Validate metadata, URLs, and relevance of retrieval result.

        Args:
            retrieval_result: The RetrievalResult to validate.

        Returns:
            ValidationResult with validation outcomes.
        """
        validation_id = str(uuid.uuid4())
        metadata_issues = []
        url_invalid = []
        metadata_completeness = True
        url_valid = True

        # Validate metadata completeness for each chunk
        for i, chunk in enumerate(retrieval_result.retrieved_chunks):
            chunk_prefix = f"Chunk {i}"

            if not chunk.source_url:
                metadata_issues.append(f"{chunk_prefix}: missing source_url")
                metadata_completeness = False

            if not chunk.section:
                metadata_issues.append(f"{chunk_prefix}: missing section")
                metadata_completeness = False

            if chunk.chunk_index is None or chunk.chunk_index < 0:
                metadata_issues.append(f"{chunk_prefix}: invalid chunk_index")
                metadata_completeness = False

            if not chunk.content or not chunk.content.strip():
                metadata_issues.append(f"{chunk_prefix}: empty content")
                metadata_completeness = False

            # Validate URL format
            if chunk.source_url and not self._validate_url(chunk.source_url):
                url_invalid.append(chunk.source_url)
                url_valid = False

        # Assess relevance
        relevance_score, relevance_assessment = self._assess_relevance(retrieval_result.retrieved_chunks)

        # Determine if result passes all criteria
        passes_criteria = (
            metadata_completeness
            and url_valid
            and len(retrieval_result.retrieved_chunks) > 0
            and relevance_assessment != "none"
        )

        validation = ValidationResult(
            validation_id=validation_id,
            result_id=retrieval_result.result_id,
            metadata_completeness=metadata_completeness,
            metadata_issues=metadata_issues,
            url_valid=url_valid,
            url_invalid=url_invalid,
            relevance_score=relevance_score,
            relevance_assessment=relevance_assessment,
            passes_criteria=passes_criteria,
            validation_timestamp=datetime.now(timezone.utc)
        )

        logger.info(
            f"Validation complete: passes={passes_criteria}, "
            f"relevance={relevance_assessment}, "
            f"metadata_ok={metadata_completeness}, "
            f"urls_ok={url_valid}"
        )
        return validation

    def test_determinism(self, query_text: str, num_runs: int = 5, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Run same query multiple times and verify identical results.

        Args:
            query_text: The search query text.
            num_runs: Number of times to run the query (default 5).
            top_k: Number of results per query.

        Returns:
            Dictionary with determinism test results including:
            - runs: list of (chunk_ids, scores) for each run
            - consistent: boolean indicating if all runs returned same results
            - differences: list of any differences found
        """
        if not query_text or not query_text.strip():
            raise QueryEmptyError("Query text cannot be empty")

        top_k = top_k or self.config.query_top_k
        runs = []
        differences = []

        logger.info(f"Testing determinism: {num_runs} runs for query '{query_text[:50]}...'")

        for i in range(num_runs):
            result = self.execute_query(query_text, top_k=top_k)

            # Extract chunk_ids and scores for comparison
            run_data = {
                "run": i + 1,
                "chunk_ids": [c.chunk_id for c in result.retrieved_chunks],
                "scores": [round(c.similarity_score, 6) for c in result.retrieved_chunks],
                "total_results": result.total_results,
                "execution_time_ms": result.execution_time_ms
            }
            runs.append(run_data)

            # Compare with first run
            if i > 0:
                first_run = runs[0]

                # Compare chunk_ids
                if run_data["chunk_ids"] != first_run["chunk_ids"]:
                    differences.append({
                        "run": i + 1,
                        "type": "chunk_ids_mismatch",
                        "expected": first_run["chunk_ids"],
                        "actual": run_data["chunk_ids"]
                    })

                # Compare scores
                if run_data["scores"] != first_run["scores"]:
                    differences.append({
                        "run": i + 1,
                        "type": "score_mismatch",
                        "expected": first_run["scores"],
                        "actual": run_data["scores"]
                    })

        consistent = len(differences) == 0
        determinism_verified = consistent

        result = {
            "query_text": query_text,
            "num_runs": num_runs,
            "top_k": top_k,
            "runs": runs,
            "consistent": consistent,
            "determinism_verified": determinism_verified,
            "differences": differences,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Determinism test complete: consistent={consistent}, differences={len(differences)}")
        return result

    def _get_collection_vector_count(self, collection_name: str) -> int:
        """Get total number of vectors in a collection."""
        try:
            info = self.qdrant_client.get_collection(collection_name)
            return info.points_count or 0
        except Exception as e:
            logger.warning(f"Failed to get collection vector count: {e}")
            return 0

    def run_validation_session(
        self,
        queries: List[str],
        top_k: Optional[int] = None,
        test_determinism_flag: bool = False
    ) -> QuerySession:
        """
        Run complete validation session with multiple queries.

        Args:
            queries: List of query texts to execute.
            top_k: Number of results per query.
            test_determinism_flag: Whether to test determinism.

        Returns:
            QuerySession with complete session metrics.
        """
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        top_k = top_k or self.config.query_top_k
        collection_name = self.config.collection_name

        logger.info(f"Starting validation session (session_id: {session_id})")
        logger.info(f"Queries: {len(queries)}, top_k: {top_k}")

        successful = 0
        failed = 0
        execution_times = []
        relevance_scores = []
        validation_results = []
        determinism_verified = True

        for i, query_text in enumerate(queries):
            logger.info(f"Executing query {i + 1}/{len(queries)}: '{query_text[:60]}...'")
            try:
                # Execute query
                retrieval_result = self.execute_query(query_text, top_k=top_k)
                execution_times.append(retrieval_result.execution_time_ms)

                # Validate result
                validation = self.validate_result(retrieval_result)
                validation_results.append({
                    "query": query_text,
                    "retrieval": retrieval_result,
                    "validation": validation
                })

                if validation.relevance_score is not None:
                    relevance_scores.append(validation.relevance_score)

                if validation.passes_criteria:
                    successful += 1
                else:
                    failed += 1
                    logger.warning(f"Query {i + 1} failed validation: {validation.metadata_issues}")

                # Test determinism if requested
                if test_determinism_flag and i == 0:
                    logger.info("Running determinism test on first query...")
                    det_result = self.test_determinism(query_text, num_runs=5, top_k=top_k)
                    determinism_verified = det_result["determinism_verified"]

            except Exception as e:
                logger.error(f"Query {i + 1} failed: {e}")
                failed += 1

        end_time = datetime.now(timezone.utc)
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else None

        # Get collection vector count
        collection_vector_count = self._get_collection_vector_count(collection_name)

        status = "completed" if failed == 0 else ("completed" if successful > 0 else "failed")

        session = QuerySession(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
            total_queries=len(queries),
            successful_queries=successful,
            failed_queries=failed,
            avg_execution_time_ms=round(avg_execution_time, 2) if avg_execution_time else None,
            avg_relevance_score=round(avg_relevance, 4) if avg_relevance else None,
            determinism_verified=determinism_verified,
            qdrant_collection=collection_name,
            collection_vector_count=collection_vector_count
        )

        logger.info(
            f"Validation session completed: "
            f"successful={successful}, failed={failed}, "
            f"avg_exec_time={avg_execution_time}ms, "
            f"avg_relevance={avg_relevance}, "
            f"determinism={determinism_verified}"
        )

        return session, validation_results


# ============================================================================
# Console Output Helpers
# ============================================================================

def print_retrieval_result(result: RetrievalResult, validation: ValidationResult):
    """Print formatted retrieval result and validation to console."""
    print("\n" + "=" * 70)
    print(f"QUERY: {result.query_text}")
    print("=" * 70)
    print(f"  Results: {result.total_results} | Top-K: {result.top_k}")
    print(f"  Execution Time: {result.execution_time_ms}ms "
          f"(embedding: {result.embedding_time_ms}ms, search: {result.search_time_ms}ms)")
    print(f"  Relevance: {validation.relevance_assessment} "
          f"(score: {validation.relevance_score:.4f})" if validation.relevance_score else f"  Relevance: {validation.relevance_assessment}")
    print(f"  Metadata Complete: {validation.metadata_completeness}")
    print(f"  URLs Valid: {validation.url_valid}")
    print(f"  Passes Criteria: {validation.passes_criteria}")

    if validation.metadata_issues:
        print(f"  Metadata Issues:")
        for issue in validation.metadata_issues:
            print(f"    - {issue}")

    if validation.url_invalid:
        print(f"  Invalid URLs:")
        for url in validation.url_invalid:
            print(f"    - {url}")

    print("-" * 70)
    for i, chunk in enumerate(result.retrieved_chunks):
        print(f"\n  [{i + 1}] Score: {chunk.similarity_score:.4f}")
        print(f"      Section: {chunk.section}")
        print(f"      Source: {chunk.source_url}")
        content_preview = chunk.content[:120] + "..." if len(chunk.content) > 120 else chunk.content
        print(f"      Content: {content_preview}")

    print("=" * 70)


def print_session_summary(session: QuerySession):
    """Print formatted session summary to console."""
    print("\n" + "=" * 70)
    print("VALIDATION SESSION SUMMARY")
    print("=" * 70)
    print(f"  Session ID: {session.session_id}")
    print(f"  Status: {session.status}")
    print(f"  Collection: {session.qdrant_collection} ({session.collection_vector_count} vectors)")
    print(f"  Total Queries: {session.total_queries}")
    print(f"  Successful: {session.successful_queries}")
    print(f"  Failed: {session.failed_queries}")
    if session.avg_execution_time_ms is not None:
        print(f"  Avg Execution Time: {session.avg_execution_time_ms:.2f}ms")
    if session.avg_relevance_score is not None:
        print(f"  Avg Relevance Score: {session.avg_relevance_score:.4f}")
    print(f"  Determinism Verified: {session.determinism_verified}")
    print("=" * 70)


# ============================================================================
# Default Queries
# ============================================================================

DEFAULT_QUERIES = [
    "What is ROS 2 and how does it work?",
    "Explain the concept of Digital Twin in robotics",
    "How does the AI Brain module process sensory data?",
    "What are VLA modules and their role in robot control?",
    "How do ROS 2 nodes communicate with each other?",
    "What is the architecture of a Digital Twin system?",
    "How does the AI Brain make decisions in autonomous robots?",
    "What are the key components of VLA (Vision-Language-Action) modules?",
    "How to implement real-time synchronization in Digital Twin?",
    "What security considerations apply to ROS 2 deployments?",
]


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI argument parser and entry point for retrieval validation."""
    parser = argparse.ArgumentParser(
        description="Retrieval Validation System for Qdrant Vector Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python retrieved.py --query "What is ROS 2?"
  python retrieved.py --queries-file queries.txt --top-k 10
  python retrieved.py --test-determinism --query "Digital Twin architecture"
  python retrieved.py --output results.json --verbose
        """
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single query text to execute"
    )
    parser.add_argument(
        "--queries-file", "-f",
        type=str,
        help="Path to file containing queries (one per line)"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=None,
        help="Number of results to return per query (default: 5)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Path to JSON output file for results"
    )
    parser.add_argument(
        "--test-determinism", "-d",
        action="store_true",
        help="Test determinism by running same query multiple times"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging"
    )

    args = parser.parse_args()

    # Set verbose logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine queries to run
    queries = []
    if args.query:
        queries.append(args.query)
    elif args.queries_file:
        if not os.path.exists(args.queries_file):
            print(f"Error: Queries file not found: {args.queries_file}")
            return 1
        with open(args.queries_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        if not queries:
            print("Error: No queries found in file")
            return 1
    else:
        # Use default queries
        queries = DEFAULT_QUERIES

    # Initialize
    try:
        config = Config()
        validator = RetrievalValidator(config)
    except Exception as e:
        print(f"Error initializing validator: {e}")
        return 1

    # Execute queries
    all_results = []

    if args.test_determinism and len(queries) == 1:
        # Single query determinism test
        query = queries[0]
        print(f"\nRunning determinism test for: '{query}'")
        det_result = validator.test_determinism(query, num_runs=5, top_k=args.top_k)

        print(f"\nDeterminism Results:")
        print(f"  Query: {det_result['query_text']}")
        print(f"  Runs: {det_result['num_runs']}")
        print(f"  Consistent: {det_result['consistent']}")
        print(f"  Differences: {len(det_result['differences'])}")

        if det_result['differences']:
            print("\n  Differences found:")
            for diff in det_result['differences']:
                print(f"    Run {diff['run']}: {diff['type']}")
        else:
            print("\n  All runs returned identical results!")

        # Also execute and validate the query once
        result = validator.execute_query(query, top_k=args.top_k)
        validation = validator.validate_result(result)
        print_retrieval_result(result, validation)
        all_results.append({"retrieval": result, "validation": validation})

    else:
        # Full validation session
        session, validation_results = validator.run_validation_session(
            queries=queries,
            top_k=args.top_k,
            test_determinism_flag=args.test_determinism
        )

        # Print individual results
        for vr in validation_results:
            print_retrieval_result(vr["retrieval"], vr["validation"])

        # Print session summary
        print_session_summary(session)

        all_results = validation_results

    # Export to JSON if requested
    if args.output:
        output_data = {
            "results": [],
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_used": "embed-english-v3.0",
                "collection": config.collection_name,
            }
        }

        for item in all_results:
            if isinstance(item, dict) and "retrieval" in item:
                retrieval = item["retrieval"]
                validation = item["validation"]

                result_dict = {
                    "query": retrieval.query_text,
                    "result_id": retrieval.result_id,
                    "total_results": retrieval.total_results,
                    "execution_time_ms": retrieval.execution_time_ms,
                    "embedding_time_ms": retrieval.embedding_time_ms,
                    "search_time_ms": retrieval.search_time_ms,
                    "chunks": [
                        {
                            "chunk_id": c.chunk_id,
                            "similarity_score": c.similarity_score,
                            "source_url": c.source_url,
                            "section": c.section,
                            "chunk_index": c.chunk_index,
                            "content_preview": c.content[:200] + "..." if len(c.content) > 200 else c.content
                        }
                        for c in retrieval.retrieved_chunks
                    ],
                    "validation": {
                        "validation_id": validation.validation_id,
                        "metadata_completeness": validation.metadata_completeness,
                        "metadata_issues": validation.metadata_issues,
                        "url_valid": validation.url_valid,
                        "url_invalid": validation.url_invalid,
                        "relevance_score": validation.relevance_score,
                        "relevance_assessment": validation.relevance_assessment,
                        "passes_criteria": validation.passes_criteria
                    }
                }
                output_data["results"].append(result_dict)

        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"\nResults exported to: {args.output}")
        except Exception as e:
            print(f"\nError exporting results: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
