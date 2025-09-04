"""
Tests for the Outline API client.
"""
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from mcp_outline.utils.outline_client import OutlineClient, OutlineError

# Test data
MOCK_API_KEY = "test_api_key"
MOCK_API_URL = "https://test.outline.com/api"

class TestOutlineClient:
    """Test suite for OutlineClient."""
    
    def setup_method(self):
        """Set up test environment."""
        # Save original environment variables
        self.original_api_key = os.environ.get("OUTLINE_API_KEY")
        self.original_api_url = os.environ.get("OUTLINE_API_URL")
        
        # Set test environment variables
        os.environ["OUTLINE_API_KEY"] = MOCK_API_KEY
        os.environ["OUTLINE_API_URL"] = MOCK_API_URL
    
    def teardown_method(self):
        """Restore original environment."""
        # Restore original environment variables
        if self.original_api_key is not None:
            os.environ["OUTLINE_API_KEY"] = self.original_api_key
        else:
            os.environ.pop("OUTLINE_API_KEY", None)
            
        if self.original_api_url is not None:
            os.environ["OUTLINE_API_URL"] = self.original_api_url
        else:
            os.environ.pop("OUTLINE_API_URL", None)
    
    def test_init_from_env_variables(self):
        """Test initialization from environment variables."""
        client = OutlineClient()
        assert client.api_key == MOCK_API_KEY
        assert client.api_url == MOCK_API_URL
    
    def test_init_from_arguments(self):
        """Test initialization from constructor arguments."""
        custom_key = "custom_key"
        custom_url = "https://custom.outline.com/api"
        
        client = OutlineClient(api_key=custom_key, api_url=custom_url)
        assert client.api_key == custom_key
        assert client.api_url == custom_url
    
    def test_init_missing_api_key(self):
        """Test error when API key is missing."""
        os.environ.pop("OUTLINE_API_KEY", None)
        
        with pytest.raises(OutlineError):
            OutlineClient(api_key=None)
    
    @patch("requests.post")
    def test_post_request(self, mock_post):
        """Test POST request method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_post.return_value = mock_response
        
        # Create client and make request
        client = OutlineClient()
        data = {"param": "value"}
        result = client.post("test_endpoint", data)
        
        # Verify request was made correctly
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/test_endpoint",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=data
        )
        
        assert result == {"data": {"test": "value"}}
    
    @patch("requests.post")
    def test_error_handling(self, mock_post):
        """Test error handling for request exceptions."""
        # Setup mock to raise an exception
        error_msg = "Connection error"
        mock_post.side_effect = requests.exceptions.RequestException(error_msg)
        
        # Create client and test exception handling
        client = OutlineClient()
        
        with pytest.raises(OutlineError) as exc_info:
            client.post("test_endpoint")
        
        assert "API request failed" in str(exc_info.value)
    
    @patch("requests.post")
    def test_get_document_revision(self, mock_post):
        """Test get_document_revision method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "rev123", "title": "Test Rev"}}
        mock_post.return_value = mock_response
        
        client = OutlineClient()
        result = client.get_document_revision("rev123")
        
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/revisions.info",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={"id": "rev123"}
        )
        
        assert result == {"id": "rev123", "title": "Test Rev"}
    
    @patch("requests.post")
    def test_list_document_revisions(self, mock_post):
        """Test list_document_revisions method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "rev1"}, {"id": "rev2"}]}
        mock_post.return_value = mock_response
        
        client = OutlineClient()
        result = client.list_document_revisions("doc123", 10, 5)
        
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/revisions.list",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={"documentId": "doc123", "limit": 10, "offset": 5}
        )
        
        assert result == [{"id": "rev1"}, {"id": "rev2"}]
    
    @patch("requests.post")
    def test_list_draft_documents(self, mock_post):
        """Test list_draft_documents method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "draft1"}, {"id": "draft2"}]}
        mock_post.return_value = mock_response
        
        client = OutlineClient()
        result = client.list_draft_documents(20)
        
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/documents.drafts",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={"limit": 20}
        )
        
        assert result == [{"id": "draft1"}, {"id": "draft2"}]
    
    @patch("requests.post")
    def test_get_recently_viewed_documents(self, mock_post):
        """Test get_recently_viewed_documents method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "viewed1"}, {"id": "viewed2"}]}
        mock_post.return_value = mock_response
        
        client = OutlineClient()
        result = client.get_recently_viewed_documents(15)
        
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/documents.viewed",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={"limit": 15}
        )
        
        assert result == [{"id": "viewed1"}, {"id": "viewed2"}]
    
    @patch("requests.post")
    def test_import_document(self, mock_post):
        """Test import_document method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "imported1", "title": "Imported Doc"}}
        mock_post.return_value = mock_response
        
        client = OutlineClient()
        result = client.import_document(
            title="Test Import",
            text="Test content",
            collection_id="col1",
            parent_document_id="parent1",
            format="markdown"
        )
        
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/documents.import",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "title": "Test Import",
                "text": "Test content",
                "format": "markdown",
                "collectionId": "col1",
                "parentDocumentId": "parent1"
            }
        )
        
        assert result == {"id": "imported1", "title": "Imported Doc"}
    
    @patch("requests.post")
    def test_import_document_minimal(self, mock_post):
        """Test import_document method with minimal parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "imported2", "title": "Minimal Import"}}
        mock_post.return_value = mock_response
        
        client = OutlineClient()
        result = client.import_document(
            title="Minimal Import",
            text="Minimal content"
        )
        
        mock_post.assert_called_once_with(
            f"{MOCK_API_URL}/documents.import",
            headers={
                "Authorization": f"Bearer {MOCK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "title": "Minimal Import",
                "text": "Minimal content",
                "format": "markdown"
            }
        )
        
        assert result == {"id": "imported2", "title": "Minimal Import"}
