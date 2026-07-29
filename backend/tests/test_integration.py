"""
Integration test for complete pipeline execution
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from main import BookIngestionPipeline, Config, IngestionRun


class TestIntegrationPipeline(unittest.TestCase):
    """Integration tests for complete pipeline execution"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.cohere_api_key = "test_key"
        self.config.qdrant_url = "https://test.qdrant.io"
        self.config.qdrant_api_key = "test_qdrant_key"
        self.config.book_base_url = "https://example.com/"
        self.config.collection_name = "test_collection"
        self.config.chunk_size = 500
        self.config.chunk_overlap = 50
    
    @patch('main.QdrantClient')
    @patch('main.cohere.Client')
    @patch('main.requests.get')
    def test_complete_pipeline_success(self, mock_requests_get, mock_cohere_client, mock_qdrant_client):
        """Test complete pipeline execution from URL discovery to storage"""
        
        # Mock sitemap XML
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/docs/intro</loc>
            </url>
            <url>
                <loc>https://example.com/docs/module1</loc>
            </url>
        </urlset>"""
        
        # Mock HTML content
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav>Navigation</nav>
                <article class="theme-doc-markdown">
                    <h1>Introduction</h1>
                    <p>This is comprehensive documentation content for testing. </p>
                    <p>It contains multiple paragraphs with sufficient text for chunking. </p>
                    <p>The content needs to be long enough to meet minimum chunk requirements. </p>
                    <p>Additional content to ensure we have enough characters for processing. </p>
                    <p>More text to guarantee we exceed the minimum threshold for chunks. </p>
                    <p>Final paragraph with enough content to complete the test requirements. </p>
                </article>
                <footer>Footer</footer>
            </body>
        </html>
        """
        
        # Mock requests for sitemap and HTML
        def mock_get(url, *args, **kwargs):
            mock_response = Mock()
            if 'sitemap.xml' in url:
                mock_response.content = sitemap_xml
                mock_response.raise_for_status = Mock()
            else:
                mock_response.text = html_content
                mock_response.content = html_content.encode('utf-8')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.headers = {'content-type': 'text/html'}
            return mock_response
        
        mock_requests_get.side_effect = mock_get
        
        # Mock Cohere embeddings
        def mock_embed(*args, **kwargs):
            mock_response = Mock()
            texts = kwargs.get('texts', [])
            mock_response.embeddings = [[0.1] * 1024 for _ in texts]
            return mock_response
        
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.side_effect = mock_embed
        mock_cohere_client.return_value = mock_cohere_instance
        
        # Mock Qdrant
        mock_collections_response = Mock()
        mock_collections_response.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections_response
        mock_qdrant_client.upsert = Mock()
        
        # Create and run pipeline
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.cohere_client = mock_cohere_instance
            pipeline.qdrant_client = mock_qdrant_client
            
            run = pipeline.run_ingestion_pipeline("https://example.com/")
        
        # Verify pipeline completed successfully
        self.assertIsInstance(run, IngestionRun)
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.pages_fetched, 2)
        self.assertEqual(run.pages_failed, 0)
        self.assertGreater(run.chunks_created, 0)
        self.assertGreater(run.vectors_stored, 0)
        self.assertIsNotNone(run.total_duration_ms)
        self.assertGreater(run.total_duration_ms, 0)
        
        # Verify Qdrant operations
        mock_qdrant_client.create_collection.assert_called_once()
        mock_qdrant_client.upsert.assert_called_once()
        
        # Verify Cohere operations
        self.assertGreater(mock_cohere_instance.embed.call_count, 0)
    
    @patch('main.QdrantClient')
    @patch('main.cohere.Client')
    @patch('main.requests.get')
    def test_pipeline_with_failed_urls(self, mock_requests_get, mock_cohere_client, mock_qdrant_client):
        """Test pipeline handling of failed URLs"""
        
        # Mock sitemap with multiple URLs
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/docs/page1</loc></url>
            <url><loc>https://example.com/docs/page2</loc></url>
            <url><loc>https://example.com/docs/page3</loc></url>
        </urlset>"""
        
        # Mock requests - page2 fails
        def mock_get(url, *args, **kwargs):
            mock_response = Mock()
            if 'sitemap.xml' in url:
                mock_response.content = sitemap_xml
                mock_response.raise_for_status = Mock()
            elif 'page2' in url:
                mock_response.raise_for_status = Mock(side_effect=Exception("Connection timeout"))
            else:
                html = "<html><body><article class='markdown'><h1>Test</h1><p>Content with sufficient text for testing the pipeline execution. </p>" * 5 + "</article></body></html>"
                mock_response.text = html
                mock_response.content = html.encode('utf-8')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
            return mock_response
        
        mock_requests_get.side_effect = mock_get
        
        # Mock Cohere
        def mock_embed(*args, **kwargs):
            mock_response = Mock()
            texts = kwargs.get('texts', [])
            mock_response.embeddings = [[0.1] * 1024 for _ in texts]
            return mock_response
        
        mock_cohere_instance = Mock()
        mock_cohere_instance.embed.side_effect = mock_embed
        mock_cohere_client.return_value = mock_cohere_instance
        
        # Mock Qdrant
        mock_collections_response = Mock()
        mock_collections_response.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections_response
        mock_qdrant_client.upsert = Mock()
        
        # Run pipeline
        with patch('main.BookIngestionPipeline._init_cohere'), \
             patch('main.BookIngestionPipeline._init_qdrant'):
            pipeline = BookIngestionPipeline(self.config)
            pipeline.cohere_client = mock_cohere_instance
            pipeline.qdrant_client = mock_qdrant_client
            
            run = pipeline.run_ingestion_pipeline("https://example.com/")
        
        # Verify pipeline handled failures gracefully
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.pages_fetched, 2)  # page1 and page3
        self.assertEqual(run.pages_failed, 1)  # page2 failed
        self.assertGreater(run.chunks_created, 0)


if __name__ == '__main__':
    unittest.main()
