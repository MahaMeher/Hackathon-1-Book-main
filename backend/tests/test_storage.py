"""
Tests for vector storage in Qdrant
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from main import BookIngestionPipeline, Config, EmbeddingVector


class TestVectorStorage(unittest.TestCase):
    """Test vector storage in Qdrant"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
        self.config.collection_name = "test_collection"
        self.config.vector_size = 1024
        
        # Create sample embeddings for testing
        self.sample_embeddings = [
            EmbeddingVector(
                vector_id="vec_001",
                vector=[0.1] * 1024,
                text_chunk_id="chunk_001",
                source_url="https://example.com/docs/test",
                section="docs/test",
                chunk_index=0,
                model_used="embed-english-v3.0",
                generated_at=datetime.now(timezone.utc)
            ),
            EmbeddingVector(
                vector_id="vec_002",
                vector=[0.2] * 1024,
                text_chunk_id="chunk_002",
                source_url="https://example.com/docs/test",
                section="docs/test",
                chunk_index=1,
                model_used="embed-english-v3.0",
                generated_at=datetime.now(timezone.utc)
            )
        ]
    
    @patch('main.QdrantClient')
    def test_create_collection_new(self, mock_qdrant_client):
        """Test creating a new Qdrant collection"""
        # Mock existing collections (empty - no existing collection)
        mock_collections_response = Mock()
        mock_collections_response.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections_response
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.qdrant_client = mock_qdrant_client
        
        pipeline.create_collection("new_collection")
        
        # Verify create_collection was called
        mock_qdrant_client.create_collection.assert_called_once()
        call_args = mock_qdrant_client.create_collection.call_args
        self.assertEqual(call_args.kwargs['collection_name'], "new_collection")
        self.assertEqual(call_args.kwargs['vectors_config'].size, 1024)
    
    @patch('main.QdrantClient')
    def test_create_collection_already_exists(self, mock_qdrant_client):
        """Test creating a collection that already exists"""
        # Mock existing collection
        mock_collection = Mock()
        mock_collection.name = "existing_collection"
        mock_collections_response = Mock()
        mock_collections_response.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections_response
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.qdrant_client = mock_qdrant_client
        
        pipeline.create_collection("existing_collection")
        
        # Verify create_collection was NOT called (already exists)
        mock_qdrant_client.create_collection.assert_not_called()
    
    @patch('main.QdrantClient')
    def test_store_vectors_in_qdrant_success(self, mock_qdrant_client):
        """Test successful vector storage in Qdrant"""
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.qdrant_client = mock_qdrant_client
        
        pipeline.store_vectors_in_qdrant(self.sample_embeddings, "test_collection")
        
        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        self.assertEqual(call_args.kwargs['collection_name'], "test_collection")
        
        # Verify points structure
        points = call_args.kwargs['points']
        self.assertEqual(len(points), 2)
        
        # Verify first point structure
        point = points[0]
        # ID is a UUID derived from vector_id, not the raw string
        self.assertIsInstance(point.id, str)
        self.assertNotEqual(point.id, "vec_001")  # Should be UUID, not raw ID
        self.assertIn("-", point.id)  # UUID format check
        self.assertEqual(len(point.vector), 1024)
        self.assertEqual(point.payload['text_chunk_id'], "chunk_001")
        self.assertEqual(point.payload['source_url'], "https://example.com/docs/test")
        self.assertEqual(point.payload['section'], "docs/test")
        self.assertEqual(point.payload['chunk_index'], 0)
        self.assertEqual(point.payload['model_used'], "embed-english-v3.0")
    
    @patch('main.QdrantClient')
    def test_store_vectors_in_qdrant_error(self, mock_qdrant_client):
        """Test handling of Qdrant storage errors"""
        mock_qdrant_client.upsert.side_effect = Exception("Qdrant connection failed")
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.qdrant_client = mock_qdrant_client
        
        with self.assertRaises(Exception) as context:
            pipeline.store_vectors_in_qdrant(self.sample_embeddings, "test_collection")
        
        self.assertIn("Qdrant connection failed", str(context.exception))


if __name__ == '__main__':
    unittest.main()
