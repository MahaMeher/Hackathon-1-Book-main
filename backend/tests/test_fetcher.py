"""
Tests for URL discovery and content fetching functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import requests

from main import BookIngestionPipeline, Config, BookContent


class TestURLDiscovery(unittest.TestCase):
    """Test URL discovery from sitemap"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    @patch('main.requests.get')
    def test_discover_book_urls_success(self, mock_get):
        """Test successful URL discovery from sitemap"""
        # Mock sitemap XML response
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/docs/intro</loc>
            </url>
            <url>
                <loc>https://example.com/docs/module1</loc>
            </url>
            <url>
                <loc>https://example.com/docs/module1/chapter1</loc>
            </url>
        </urlset>"""
        
        mock_response = Mock()
        mock_response.content = sitemap_xml
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create pipeline with mocked clients
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        urls = pipeline.discover_book_urls("https://example.com/")
        
        self.assertEqual(len(urls), 3)
        self.assertIn("https://example.com/docs/intro.html", urls)
        self.assertIn("https://example.com/docs/module1.html", urls)
        self.assertIn("https://example.com/docs/module1/chapter1.html", urls)
    
    @patch('main.requests.get')
    def test_discover_book_urls_empty_sitemap(self, mock_get):
        """Test URL discovery with empty sitemap"""
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        </urlset>"""
        
        mock_response = Mock()
        mock_response.content = sitemap_xml
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        urls = pipeline.discover_book_urls("https://example.com/")
        
        self.assertEqual(len(urls), 0)
    
    @patch('main.requests.get')
    def test_discover_book_urls_request_failure(self, mock_get):
        """Test URL discovery with request failure"""
        mock_get.side_effect = requests.RequestException("Connection error")
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        with self.assertRaises(requests.RequestException):
            pipeline.discover_book_urls("https://example.com/")


class TestContentFetching(unittest.TestCase):
    """Test content fetching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
        self.config.max_retries = 2
        self.config.request_timeout = 5
    
    @patch('main.requests.get')
    def test_fetch_book_content_success(self, mock_get):
        """Test successful content fetching"""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>This is test content.</p>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.content = html_content.encode('utf-8')
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        result = pipeline.fetch_book_content("https://example.com/docs/test")
        
        self.assertIsInstance(result, BookContent)
        self.assertEqual(result.url, "https://example.com/docs/test")
        self.assertEqual(result.title, "Test Page")
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.content_hash)
        self.assertIsInstance(result.fetched_at, datetime)
    
    @patch('main.requests.get')
    def test_fetch_book_content_retry_success(self, mock_get):
        """Test content fetching with retry before success"""
        # First call fails, second succeeds
        html_content = "<html><head><title>Retry Page</title></head><body>Content</body></html>"
        
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status = Mock(side_effect=requests.Timeout("Timeout"))
        
        mock_response_success = Mock()
        mock_response_success.text = html_content
        mock_response_success.content = html_content.encode('utf-8')
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        result = pipeline.fetch_book_content("https://example.com/docs/test")
        
        self.assertIsInstance(result, BookContent)
        self.assertEqual(mock_get.call_count, 2)  # Verify retry happened
    
    @patch('main.requests.get')
    def test_fetch_book_content_all_retries_fail(self, mock_get):
        """Test content fetching when all retries fail"""
        mock_get.side_effect = requests.Timeout("Timeout")
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        with self.assertRaises(requests.Timeout):
            pipeline.fetch_book_content("https://example.com/docs/test")
        
        self.assertEqual(mock_get.call_count, self.config.max_retries)


class TestTitleExtraction(unittest.TestCase):
    """Test title extraction from HTML"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
    
    def test_extract_title_from_title_tag(self):
        """Test extracting title from <title> tag"""
        html = "<html><head><title>Page Title</title></head><body></body></html>"
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        title = pipeline._extract_title(html)
        self.assertEqual(title, "Page Title")
    
    def test_extract_title_from_h1_tag(self):
        """Test extracting title from <h1> tag as fallback"""
        html = "<html><head></head><body><h1>H1 Title</h1></body></html>"
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        title = pipeline._extract_title(html)
        self.assertEqual(title, "H1 Title")
    
    def test_extract_title_no_title_found(self):
        """Test returning 'Untitled' when no title found"""
        html = "<html><head></head><body></body></html>"
        
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
        
        title = pipeline._extract_title(html)
        self.assertEqual(title, "Untitled")


if __name__ == '__main__':
    unittest.main()
