"""
Tests for validation functionality
"""

import unittest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from retrieved import (
    RetrievalValidator, Config, RetrievalResult, RetrievedChunk, ValidationResult
)


class TestValidateResult(unittest.TestCase):
    """Test validate_result functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
        
        # Create a sample RetrievalResult for testing
        self.sample_chunks = [
            RetrievedChunk(
                chunk_id="chunk-001",
                content="ROS 2 is a flexible framework for robot software development.",
                similarity_score=0.75,
                source_url="https://example.com/docs/ros2-intro",
                section="docs/module1",
                chunk_index=0,
                model_used="embed-english-v3.0",
                generated_at=datetime.now(timezone.utc)
            ),
            RetrievedChunk(
                chunk_id="chunk-002",
                content="ROS 2 provides several communication mechanisms.",
                similarity_score=0.68,
                source_url="https://example.com/docs/ros2-communication",
                section="docs/module1",
                chunk_index=1,
                model_used="embed-english-v3.0",
                generated_at=datetime.now(timezone.utc)
            )
        ]
        
        self.sample_result = RetrievalResult(
            result_id="result-001",
            query_text="What is ROS 2?",
            query_embedding_model="embed-english-v3.0",
            retrieved_chunks=self.sample_chunks,
            total_results=2,
            execution_time_ms=850,
            embedding_time_ms=300,
            search_time_ms=550,
            timestamp=datetime.now(timezone.utc),
            top_k=5
        )
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_validate_result_metadata_complete(self, mock_qdrant, mock_cohere):
        """Test validation with complete metadata"""
        mock_cohere_instance = Mock()
        mock_cohere.return_value = mock_cohere_instance
        
        mock_qdrant_instance = Mock()
        mock_collection = Mock()
        mock_collection.vectors_count = 53
        mock_qdrant_instance.get_collection.return_value = mock_collection
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        validation = validator.validate_result(self.sample_result)
        
        self.assertIsInstance(validation, ValidationResult)
        self.assertTrue(validation.metadata_completeness)
        self.assertTrue(validation.url_valid)
        self.assertEqual(len(validation.metadata_issues), 0)
        self.assertEqual(len(validation.url_invalid), 0)
        self.assertEqual(validation.relevance_assessment, "high")
        self.assertTrue(validation.passes_criteria)
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_validate_result_metadata_incomplete(self, mock_qdrant, mock_cohere):
        """Test validation with incomplete metadata"""
        # Create chunk with missing metadata
        incomplete_chunks = [
            RetrievedChunk(
                chunk_id="chunk-001",
                content="Test content",
                similarity_score=0.7,
                source_url="",  # Missing URL
                section="",  # Missing section
                chunk_index=0,
                model_used="embed-english-v3.0",
                generated_at=datetime.now(timezone.utc)
            )
        ]
        
        incomplete_result = RetrievalResult(
            result_id="result-002",
            query_text="Test query",
            query_embedding_model="embed-english-v3.0",
            retrieved_chunks=incomplete_chunks,
            total_results=1,
            execution_time_ms=500,
            embedding_time_ms=200,
            search_time_ms=300,
            timestamp=datetime.now(timezone.utc),
            top_k=5
        )
        
        mock_cohere_instance = Mock()
        mock_cohere.return_value = mock_cohere_instance
        
        mock_qdrant_instance = Mock()
        mock_collection = Mock()
        mock_collection.vectors_count = 53
        mock_qdrant_instance.get_collection.return_value = mock_collection
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        validation = validator.validate_result(incomplete_result)
        
        self.assertFalse(validation.metadata_completeness)
        self.assertGreater(len(validation.metadata_issues), 0)
        self.assertFalse(validation.passes_criteria)
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_validate_result_low_similarity(self, mock_qdrant, mock_cohere):
        """Test validation with low similarity scores"""
        low_score_chunks = [
            RetrievedChunk(
                chunk_id="chunk-001",
                content="Unrelated content",
                similarity_score=0.2,  # Low score
                source_url="https://example.com/docs/test",
                section="docs/test",
                chunk_index=0,
                model_used="embed-english-v3.0",
                generated_at=datetime.now(timezone.utc)
            )
        ]
        
        low_score_result = RetrievalResult(
            result_id="result-003",
            query_text="Test query",
            query_embedding_model="embed-english-v3.0",
            retrieved_chunks=low_score_chunks,
            total_results=1,
            execution_time_ms=500,
            embedding_time_ms=200,
            search_time_ms=300,
            timestamp=datetime.now(timezone.utc),
            top_k=5
        )
        
        mock_cohere_instance = Mock()
        mock_cohere.return_value = mock_cohere_instance
        
        mock_qdrant_instance = Mock()
        mock_collection = Mock()
        mock_collection.vectors_count = 53
        mock_qdrant_instance.get_collection.return_value = mock_collection
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        validation = validator.validate_result(low_score_result)
        
        self.assertEqual(validation.relevance_assessment, "none")
        self.assertFalse(validation.passes_criteria)


class TestDeterminismTesting(unittest.TestCase):
    """Test determinism verification functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_determinism_verified(self, mock_qdrant, mock_cohere):
        """Test that deterministic results are verified"""
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
        
        # Create consistent mock results
        mock_point = Mock()
        mock_point.id = "consistent-uuid"
        mock_point.score = 0.75
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
        result = validator.test_determinism("What is ROS 2?", num_runs=5, top_k=5)
        
        self.assertTrue(result['determinism_verified'])
        self.assertTrue(result['consistent'])
        self.assertEqual(len(result['differences']), 0)
        self.assertEqual(result['num_runs'], 5)

    @patch('retrieved.cohere.Client')
    @patch('retrieved.QdrantClient')
    def test_determinism_mismatch_detected(self, mock_qdrant, mock_cohere):
        """Test that mismatches are detected"""
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
        
        # Create varying mock results
        call_count = [0]
        def mock_query(*args, **kwargs):
            call_count[0] += 1
            mock_point = Mock()
            mock_point.id = f"uuid-{call_count[0]}"  # Different UUID each time
            mock_point.score = 0.75
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
            return mock_search_result
        
        mock_qdrant_instance.query_points.side_effect = mock_query
        mock_qdrant.return_value = mock_qdrant_instance
        
        validator = RetrievalValidator(self.config)
        time.sleep(0.01)  # Ensure positive timing
        result = validator.test_determinism("What is ROS 2?", num_runs=3, top_k=5)
        
        self.assertFalse(result['determinism_verified'])
        self.assertFalse(result['consistent'])
        self.assertGreater(len(result['differences']), 0)


if __name__ == '__main__':
    unittest.main()
