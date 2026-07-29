"""
Tests for text extraction and chunking functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from main import BookIngestionPipeline, Config, BookContent, TextChunk


class TestTextExtraction(unittest.TestCase):
    """Test text extraction from HTML content"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    def test_extract_text_content_docusaurus(self):
        """Test extracting text from Docusaurus-style HTML"""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav class="navbar">Navigation Menu</nav>
                <div class="sidebar">Sidebar Content</div>
                <article class="theme-doc-markdown">
                    <h1>Chapter 1: Introduction</h1>
                    <p>This is the main content of the chapter.</p>
                    <p>It contains multiple paragraphs and information.</p>
                </article>
                <footer class="footer">Footer Content</footer>
            </body>
        </html>
        """
        
        book_content = BookContent(
            url="https://example.com/docs/test",
            html_content=html_content,
            title="Test Page",
            fetched_at=datetime.now(timezone.utc),
            status_code=200,
            content_hash="abc123"
        )
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        text = pipeline.extract_text_content(book_content)
        
        # Should contain main content but not navigation
        self.assertIn("Chapter 1: Introduction", text)
        self.assertIn("main content of the chapter", text)
        # Should not contain navigation elements (or they should be minimal)
        self.assertNotIn("Navigation Menu", text)
        self.assertNotIn("Sidebar Content", text)
        self.assertNotIn("Footer Content", text)
    
    def test_extract_text_content_clean_text(self):
        """Test that extracted text is clean and normalized"""
        html_content = """
        <html>
            <body>
                <article class="markdown">
                    <h1>Title</h1>
                    <p>Paragraph with   multiple    spaces.</p>
                    <p>Another paragraph.</p>
                </article>
            </body>
        </html>
        """
        
        book_content = BookContent(
            url="https://example.com/docs/test",
            html_content=html_content,
            title="Test",
            fetched_at=datetime.now(timezone.utc),
            status_code=200,
            content_hash="abc123"
        )
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        text = pipeline.extract_text_content(book_content)
        
        # Should normalize whitespace
        self.assertNotIn("   ", text)  # No multiple spaces
        text = text.strip()
        self.assertTrue(len(text) > 0)


class TestTextChunking(unittest.TestCase):
    """Test text chunking functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
        self.config.chunk_size = 500
        self.config.chunk_overlap = 50
    
    def test_chunk_text_small_content(self):
        """Test chunking small content that fits in one chunk"""
        text = "This is a short paragraph with some content. " * 10
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        chunks = pipeline.chunk_text(
            text,
            source_url="https://example.com/docs/test",
            section="docs/test"
        )
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # Verify chunk structure
        chunk = chunks[0]
        self.assertIsInstance(chunk, TextChunk)
        self.assertIsNotNone(chunk.id)
        self.assertIsNotNone(chunk.content)
        self.assertEqual(chunk.source_url, "https://example.com/docs/test")
        self.assertEqual(chunk.section, "docs/test")
        self.assertEqual(chunk.chunk_index, 0)
        self.assertGreater(chunk.word_count, 0)
        self.assertGreater(chunk.char_count, 0)
        self.assertIsInstance(chunk.created_at, datetime)
    
    def test_chunk_text_large_content(self):
        """Test chunking large content that requires multiple chunks"""
        text = "This is a long paragraph with content. " * 100  # Creates large text
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        chunks = pipeline.chunk_text(
            text,
            source_url="https://example.com/docs/test",
            section="docs/test"
        )
        
        # Should create multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk.chunk_index, i)
    
    def test_chunk_text_minimum_size(self):
        """Test that chunks below minimum size are not created"""
        text = "Short text."  # Too short to meet minimum 100 chars
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        chunks = pipeline.chunk_text(
            text,
            source_url="https://example.com/docs/test",
            section="docs/test"
        )
        
        # Should create no chunks (too short)
        self.assertEqual(len(chunks), 0)
    
    def test_chunk_text_with_overlap(self):
        """Test that chunking includes overlap for context continuity"""
        text = "Word " * 200  # Create content that will split into chunks
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        chunks = pipeline.chunk_text(
            text,
            source_url="https://example.com/docs/test",
            section="docs/test"
        )
        
        if len(chunks) > 1:
            # Verify overlap exists (chunks share some content)
            chunk1_words = set(chunks[0].content.split())
            chunk2_words = set(chunks[1].content.split())
            overlap = chunk1_words & chunk2_words
            # There should be some overlap
            self.assertGreater(len(overlap), 0)


class TestSectionExtraction(unittest.TestCase):
    """Test section name extraction from URLs"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    def test_extract_section_from_url_deep_path(self):
        """Test extracting section from deep URL path"""
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        section = pipeline._extract_section_from_url(
            "https://example.com/docs/module1/chapter1",
            "https://example.com/"
        )
        
        self.assertEqual(section, "docs/module1")
    
    def test_extract_section_from_url_shallow_path(self):
        """Test extracting section from shallow URL path"""
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        section = pipeline._extract_section_from_url(
            "https://example.com/docs/intro",
            "https://example.com/"
        )
        
        # Returns first two parts when available
        self.assertEqual(section, "docs/intro")
    
    def test_extract_section_from_url_root(self):
        """Test extracting section from root URL"""
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        section = pipeline._extract_section_from_url(
            "https://example.com/",
            "https://example.com/"
        )
        
        # Returns empty string for root (no path after base)
        self.assertEqual(section, "")


if __name__ == '__main__':
    unittest.main()
