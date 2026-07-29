"""
Tests for retrieval functionality
"""

import unittest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from retrieved import (
    RetrievalValidator, Config, RetrievedChunk, RetrievalResult,
    QueryEmptyError, ConnectionError
)


class TestExecuteQuery(unittest.TestCase):
    """Test execute_query functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_execute_query_success(self, mock_qdrant, mock_cohere):
        """Test successful query execution"""
        # Mock Cohere response
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.return_value = Mock(
            embeddings=[[0.1] * 1024]
        )
        mock_cohere.return_value = mock_cohere_instance
        
        # Mock Qdrant response
        mock_qdrant_instance = Mock()
        mock_collection = Mock()
        mock_collection.vectors_count = 53
        mock_collection.name = "book_vectors"
        mock_qdrant_instance.get_collection.return_value = mock_collection
        
        # Mock get_collections to return a list with our collection
        mock_collections_response = Mock()
        mock_collections_response.collections = [mock_collection]
        mock_qdrant_instance.get_collections.return_value = mock_collections_response
        
        # Mock search result
        mock_point = Mock()
        mock_point.id = "test-uuid-123"
        mock_point.score = 0.75
        mock_point.payload = {
            "source_url": "https://example.com/docs/test",
            "section": "docs/test",
            "chunk_index": 0,
            "model_used": "embed-english-v3.0",
            "generated_at": "2026-04-13T00:52:20Z",
            "content": "Test content about ROS 2"
        }
        mock_point.vector = [0.1] * 1024
        
        mock_search_result = Mock()
        mock_search_result.points = [mock_point]
        mock_qdrant_instance.query_points.return_value = mock_search_result
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        time.sleep(0.01)  # Ensure positive timing
        result = validator.execute_query("What is ROS 2?", top_k=5)
        
        self.assertIsInstance(result, RetrievalResult)
        self.assertEqual(result.query_text, "What is ROS 2?")
        self.assertEqual(result.top_k, 5)
        self.assertGreater(result.total_results, 0)
        self.assertIsInstance(result.execution_time_ms, int)
        self.assertGreaterEqual(result.execution_time_ms, 0)
        self.assertEqual(len(result.retrieved_chunks), 1)
        
        # Check retrieved chunk
        chunk = result.retrieved_chunks[0]
        self.assertIsInstance(chunk, RetrievedChunk)
        self.assertEqual(chunk.similarity_score, 0.75)
        self.assertEqual(chunk.source_url, "https://example.com/docs/test")
        self.assertEqual(chunk.section, "docs/test")
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_execute_query_empty(self, mock_qdrant, mock_cohere):
        """Test empty query raises QueryEmptyError"""
        mock_cohere_instance = Mock()
        mock_cohere.return_value = mock_cohere_instance
        
        mock_qdrant_instance = Mock()
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        
        with self.assertRaises(QueryEmptyError):
            validator.execute_query("", top_k=5)
        
        with self.assertRaises(QueryEmptyError):
            validator.execute_query("   ", top_k=5)


class TestPerformanceMeasurement(unittest.TestCase):
    """Test performance measurement functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_query_execution_time_measured(self, mock_qdrant, mock_cohere):
        """Test that execution time is properly measured"""
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.return_value = Mock(
            embeddings=[[0.1] * 1024]
        )
        mock_cohere.return_value = mock_cohere_instance
        
        mock_qdrant_instance = Mock()
        mock_collection = Mock()
        mock_collection.vectors_count = 53
        mock_collection.name = "book_vectors"
        mock_qdrant_instance.get_collection.return_value = mock_collection
        
        # Mock get_collections
        mock_collections_response = Mock()
        mock_collections_response.collections = [mock_collection]
        mock_qdrant_instance.get_collections.return_value = mock_collections_response
        
        mock_point = Mock()
        mock_point.id = "test-uuid"
        mock_point.score = 0.8
        mock_point.payload = {
            "source_url": "https://example.com/docs/test",
            "section": "docs/test",
            "chunk_index": 0,
            "model_used": "embed-english-v3.0",
            "generated_at": "2026-04-13T00:52:20Z",
            "content": "Test content"
        }
        mock_point.vector = [0.1] * 1024
        
        mock_search_result = Mock()
        mock_search_result.points = [mock_point]
        mock_qdrant_instance.query_points.return_value = mock_search_result
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        time.sleep(0.01)  # Ensure positive timing
        result = validator.execute_query("Test query", top_k=5)

        # Verify timing is properly recorded
        self.assertIsInstance(result.execution_time_ms, int)
        self.assertIsInstance(result.embedding_time_ms, int)
        self.assertIsInstance(result.search_time_ms, int)
        self.assertGreaterEqual(result.execution_time_ms, 0)
        self.assertGreaterEqual(result.embedding_time_ms, 0)
        self.assertGreaterEqual(result.search_time_ms, 0)

        # Execution time should be approximately embedding + search
        total = result.embedding_time_ms + result.search_time_ms
        # Allow some margin for overhead
        self.assertAlmostEqual(result.execution_time_ms, total, delta=100)


if __name__ == '__main__':
    unittest.main()
