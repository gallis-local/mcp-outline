"""
Tests for document revision tools.
"""
from unittest.mock import MagicMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_revisions import (
    _format_revision_info,
    _format_revisions_list,
)


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


# Sample test data
SAMPLE_REVISION = {
    "id": "rev123",
    "title": "Test Document v2",
    "text": "This is the second version of the test document with some changes.",
    "createdAt": "2023-12-01T10:00:00Z",
    "createdBy": {
        "id": "user1",
        "name": "John Doe"
    }
}

SAMPLE_REVISIONS = [
    {
        "id": "rev123",
        "title": "Test Document v2",
        "createdAt": "2023-12-01T10:00:00Z",
        "createdBy": {
            "id": "user1",
            "name": "John Doe"
        }
    },
    {
        "id": "rev122",
        "title": "Test Document v1",
        "createdAt": "2023-11-30T09:00:00Z",
        "createdBy": {
            "id": "user1",
            "name": "John Doe"
        }
    }
]

SAMPLE_LONG_TEXT_REVISION = {
    "id": "rev124",
    "title": "Long Document",
    "text": "This is a very long document. " * 50,  # 1500 characters
    "createdAt": "2023-12-02T11:00:00Z",
    "createdBy": {
        "id": "user2",
        "name": "Jane Smith"
    }
}


class TestDocumentRevisionFormatters:
    """Test the formatting functions for document revisions."""
    
    def test_format_revision_info_with_data(self):
        """Test formatting revision info with complete data."""
        result = _format_revision_info(SAMPLE_REVISION)
        
        assert "# Document Revision" in result
        assert "rev123" in result
        assert "Test Document v2" in result
        assert "2023-12-01T10:00:00Z" in result
        assert "John Doe" in result
        assert "This is the second version" in result
    
    def test_format_revision_info_with_long_text(self):
        """Test formatting revision info with long text gets truncated."""
        result = _format_revision_info(SAMPLE_LONG_TEXT_REVISION)
        
        assert "# Document Revision" in result
        assert "rev124" in result
        assert "Long Document" in result
        assert "Jane Smith" in result
        # Should be truncated with ellipsis
        assert "..." in result
        assert len(result) < 1000  # Should be much shorter than full text
    
    def test_format_revision_info_empty(self):
        """Test formatting empty revision data."""
        result = _format_revision_info({})
        
        assert "No revision information found" in result
    
    def test_format_revision_info_missing_fields(self):
        """Test formatting revision with missing fields."""
        partial_revision = {"id": "rev125", "title": "Partial Doc"}
        result = _format_revision_info(partial_revision)
        
        assert "rev125" in result
        assert "Partial Doc" in result
        assert "Unknown" in result  # For missing created_at and author
    
    def test_format_revisions_list_with_data(self):
        """Test formatting revisions list with data."""
        result = _format_revisions_list(SAMPLE_REVISIONS)
        
        assert "# Document Revisions (2 found)" in result
        assert "1. Test Document v2" in result
        assert "2. Test Document v1" in result
        assert "rev123" in result
        assert "rev122" in result
        assert "John Doe" in result
    
    def test_format_revisions_list_empty(self):
        """Test formatting empty revisions list."""
        result = _format_revisions_list([])
        
        assert "No revisions found" in result
    
    def test_format_revisions_list_missing_fields(self):
        """Test formatting revisions list with missing fields."""
        partial_revisions = [{"id": "rev126"}]
        result = _format_revisions_list(partial_revisions)
        
        assert "# Document Revisions (1 found)" in result
        assert "rev126" in result
        assert "Untitled" in result
        assert "Unknown" in result


class TestDocumentRevisionTools:
    """Test the document revision MCP tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MockMCP()
        
        # Import and register tools with mock MCP
        from mcp_outline.features.documents import document_revisions
        document_revisions.register_tools(self.mock_mcp)
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_get_document_revision_success(self, mock_get_client):
        """Test successful revision retrieval."""
        mock_client = MagicMock()
        mock_client.get_document_revision.return_value = SAMPLE_REVISION
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['get_document_revision']
        result = tool("rev123")
        
        assert "# Document Revision" in result
        assert "rev123" in result
        assert "Test Document v2" in result
        mock_client.get_document_revision.assert_called_once_with("rev123")
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_get_document_revision_client_error(self, mock_get_cached, mock_get_client):
        """Test revision retrieval with client error."""
        mock_get_cached.return_value = None  # No cache
        mock_get_client.side_effect = OutlineClientError("API Error")
        
        tool = self.mock_mcp.tools['get_document_revision']
        result = tool("rev123")
        
        assert "Error retrieving revision: API Error" in result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_get_document_revision_unexpected_error(self, mock_get_cached, mock_get_client):
        """Test revision retrieval with unexpected error."""
        mock_get_cached.return_value = None  # No cache
        mock_get_client.side_effect = Exception("Unexpected error")
        
        tool = self.mock_mcp.tools['get_document_revision']
        result = tool("rev123")
        
        assert "Unexpected error: Unexpected error" in result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_list_document_revisions_success(self, mock_get_client):
        """Test successful revisions listing."""
        mock_client = MagicMock()
        mock_client.list_document_revisions.return_value = SAMPLE_REVISIONS
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['list_document_revisions']
        result = tool("doc123", 25, 0)
        
        assert "# Document Revisions (2 found)" in result
        assert "rev123" in result
        assert "rev122" in result
        assert "Showing 2 revisions" in result
        mock_client.list_document_revisions.assert_called_once_with("doc123", 25, 0)
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_list_document_revisions_empty(self, mock_get_client):
        """Test revisions listing with no results."""
        mock_client = MagicMock()
        mock_client.list_document_revisions.return_value = []
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['list_document_revisions']
        result = tool("doc123")
        
        assert "No revisions found" in result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_list_document_revisions_client_error(self, mock_get_client):
        """Test revisions listing with client error."""
        mock_get_client.side_effect = OutlineClientError("API Error")
        
        tool = self.mock_mcp.tools['list_document_revisions']
        result = tool("doc123")
        
        assert "Error retrieving revisions: API Error" in result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_compare_document_revisions_success(self, mock_get_cached, mock_get_client):
        """Test successful revision comparison."""
        mock_get_cached.side_effect = [None, None]  # No cache for both calls
        mock_client = MagicMock()
        revision_1 = {**SAMPLE_REVISIONS[0], "text": "First version content"}
        revision_2 = {**SAMPLE_REVISIONS[1], "text": "Second version content with more text"}
        mock_client.get_document_revision.side_effect = [revision_1, revision_2]
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['compare_document_revisions']
        result = tool("rev123", "rev122")
        
        assert "# Detailed Revision Comparison" in result
        assert "Revision 1 (rev123)" in result
        assert "Revision 2 (rev122)" in result
        assert "Content Analysis" in result
        assert "Changes Summary" in result
        assert "chars" in result
        assert "words" in result
        assert "lines" in result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_compare_document_revisions_missing_revision(self, mock_get_cached, mock_get_client):
        """Test revision comparison with missing revision."""
        mock_get_cached.side_effect = [None, None]  # No cache for both calls
        mock_client = MagicMock()
        mock_client.get_document_revision.side_effect = [SAMPLE_REVISIONS[0], None]
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['compare_document_revisions']
        result = tool("rev123", "rev999")
        
        assert "One or both revisions could not be found" in result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_compare_document_revisions_client_error(self, mock_get_client):
        """Test revision comparison with client error."""
        mock_get_client.side_effect = OutlineClientError("API Error")
        
        tool = self.mock_mcp.tools['compare_document_revisions']
        result = tool("rev123", "rev122")
        
        assert "Error comparing revisions: API Error" in result