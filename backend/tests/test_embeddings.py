"""
Tests for embedding generation functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from main import BookIngestionPipeline, Config, TextChunk, EmbeddingVector


class TestEmbeddingGeneration(unittest.TestCase):
    """Test embedding generation with Cohere"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
        self.config.embedding_model = "embed-english-v3.0"
        self.config.vector_size = 1024
        
        # Create sample chunks for testing
        self.sample_chunks = [
            TextChunk(
                id="chunk_001",
                content="This is test content for embedding generation.",
                source_url="https://example.com/docs/test",
                section="docs/test",
                chunk_index=0,
                word_count=8,
                char_count=48,
                created_at=datetime.now(timezone.utc)
            ),
            TextChunk(
                id="chunk_002",
                content="Another piece of test content for testing embeddings.",
                source_url="https://example.com/docs/test",
                section="docs/test",
                chunk_index=1,
                word_count=9,
                char_count=54,
                created_at=datetime.now(timezone.utc)
            )
        ]
    
    @patch('main.cohere.Client')
    def test_generate_embeddings_success(self, mock_cohere_client):
        """Test successful embedding generation"""
        # Mock Cohere response
        mock_embeddings = [
            [0.1] * 1024,  # 1024-dimensional vector
            [0.2] * 1024
        ]
        
        mock_response = Mock()
        mock_response.embeddings = mock_embeddings
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.return_value = mock_response
        mock_cohere_client.return_value = mock_cohere_instance
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.cohere_client = mock_cohere_instance
        
        embeddings = pipeline.generate_embeddings(self.sample_chunks)
        
        self.assertEqual(len(embeddings), 2)
        
        # Verify first embedding structure
        embedding = embeddings[0]
        self.assertIsInstance(embedding, EmbeddingVector)
        self.assertEqual(len(embedding.vector), 1024)
        self.assertEqual(embedding.text_chunk_id, "chunk_001")
        self.assertEqual(embedding.source_url, "https://example.com/docs/test")
        self.assertEqual(embedding.section, "docs/test")
        self.assertEqual(embedding.chunk_index, 0)
        self.assertEqual(embedding.model_used, "embed-english-v3.0")
        self.assertIsInstance(embedding.generated_at, datetime)
        
        # Verify Cohere API was called correctly
        mock_cohere_instance.embed.assert_called_once()
        call_args = mock_cohere_instance.embed.call_args
        self.assertEqual(call_args.kwargs['model'], "embed-english-v3.0")
        self.assertEqual(call_args.kwargs['input_type'], "search_document")
    
    @patch('main.cohere.Client')
    def test_generate_embeddings_batch_processing(self, mock_cohere_client):
        """Test batch processing of embeddings"""
        # Create many chunks to test batching
        many_chunks = [
            TextChunk(
                id=f"chunk_{i:03d}",
                content=f"Test content number {i}. " * 10,
                source_url="https://example.com/docs/test",
                section="docs/test",
                chunk_index=i,
                word_count=50,
                char_count=250,
                created_at=datetime.now(timezone.utc)
            )
            for i in range(200)  # More than batch size (96)
        ]
        
        # Mock multiple API calls for batches
        def mock_embed(*args, **kwargs):
            mock_response = Mock()
            texts = kwargs.get('texts', [])
            mock_response.embeddings = [[0.1] * 1024 for _ in texts]
            return mock_response
        
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.side_effect = mock_embed
        mock_cohere_client.return_value = mock_cohere_instance
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.cohere_client = mock_cohere_instance
        
        embeddings = pipeline.generate_embeddings(many_chunks)
        
        # Should process all chunks
        self.assertEqual(len(embeddings), 200)
        
        # Should make multiple API calls (200 chunks / 96 batch size = 3 calls)
        self.assertGreaterEqual(mock_cohere_instance.embed.call_count, 2)
    
    @patch('main.cohere.Client')
    def test_generate_embeddings_api_error(self, mock_cohere_client):
        """Test handling of Cohere API errors"""
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.side_effect = Exception("API rate limit exceeded")
        mock_cohere_client.return_value = mock_cohere_instance
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.cohere_client = mock_cohere_instance
        
        with self.assertRaises(Exception) as context:
            pipeline.generate_embeddings(self.sample_chunks)
        
        self.assertIn("API rate limit exceeded", str(context.exception))


if __name__ == '__main__':
    unittest.main()
