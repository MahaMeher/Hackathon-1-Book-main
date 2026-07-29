"""
Tests for chunking configuration and parameters
"""

import unittest
from unittest.mock import patch

from main import BookIngestionPipeline, Config


class TestChunkingConfiguration(unittest.TestCase):
    """Test chunking configuration parameters"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    def test_default_chunk_size(self):
        """Test default chunk size is 3000 characters"""
        self.assertEqual(self.config.chunk_size, 3000)
    
    def test_default_chunk_overlap(self):
        """Test default chunk overlap is 200 characters"""
        self.assertEqual(self.config.chunk_overlap, 200)
    
    def test_custom_chunk_size(self):
        """Test custom chunk size configuration"""
        import os
        os.environ['CHUNK_SIZE'] = '2000'
        
        config = Config()
        self.assertEqual(config.chunk_size, 2000)
        
        # Clean up
        del os.environ['CHUNK_SIZE']
    
    def test_custom_chunk_overlap(self):
        """Test custom chunk overlap configuration"""
        import os
        os.environ['CHUNK_OVERLAP'] = '100'
        
        config = Config()
        self.assertEqual(config.chunk_overlap, 100)
        
        # Clean up
        del os.environ['CHUNK_OVERLAP']


if __name__ == '__main__':
    unittest.main()
