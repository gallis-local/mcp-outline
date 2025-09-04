"""
Tests for document import and activity tracking tools.
"""
from unittest.mock import MagicMock, patch

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_import import (
    _format_documents_list,
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
SAMPLE_DRAFT_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Draft Document 1",
        "updatedAt": "2023-12-01T10:00:00Z",
        "createdAt": "2023-11-30T09:00:00Z"
    },
    {
        "id": "doc2",
        "title": "Draft Document 2",
        "updatedAt": "2023-12-02T11:00:00Z",
        "createdAt": "2023-12-01T10:00:00Z"
    }
]

SAMPLE_VIEWED_DOCUMENTS = [
    {
        "id": "doc3",
        "title": "Recently Viewed Doc 1",
        "updatedAt": "2023-12-03T12:00:00Z"
    },
    {
        "id": "doc4",
        "title": "Recently Viewed Doc 2",
        "updatedAt": "2023-12-02T11:30:00Z"
    }
]




class TestDocumentImportFormatters:
    """Test the formatting functions for document import and activity tracking."""
    
    def test_format_documents_list_with_data(self):
        """Test formatting documents list with data."""
        result = _format_documents_list(SAMPLE_DRAFT_DOCUMENTS, "Draft Documents")
        
        assert "# Draft Documents (2 found)" in result
        assert "1. Draft Document 1" in result
        assert "2. Draft Document 2" in result
        assert "doc1" in result
        assert "doc2" in result
        assert "2023-12-01T10:00:00Z" in result
    
    def test_format_documents_list_empty(self):
        """Test formatting empty documents list."""
        result = _format_documents_list([], "Draft Documents")
        
        assert "No draft documents found" in result
    
    def test_format_documents_list_missing_fields(self):
        """Test formatting documents list with missing fields."""
        partial_docs = [{"id": "doc6", "title": "Partial Doc"}]
        result = _format_documents_list(partial_docs, "Test Documents")
        
        assert "# Test Documents (1 found)" in result
        assert "doc6" in result
        assert "Partial Doc" in result


class TestDocumentImportTools:
    """Test the document import and activity tracking MCP tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MockMCP()
        
        # Import and register tools with mock MCP
        from mcp_outline.features.documents import document_import
        document_import.register_tools(self.mock_mcp)
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_list_draft_documents_success(self, mock_get_client):
        """Test successful draft documents listing."""
        mock_client = MagicMock()
        mock_client.list_draft_documents.return_value = SAMPLE_DRAFT_DOCUMENTS
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['list_draft_documents']
        result = tool(25)
        
        assert "# Draft Documents (2 found)" in result
        assert "Draft Document 1" in result
        assert "Draft Document 2" in result
        mock_client.list_draft_documents.assert_called_once_with(25)
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_list_draft_documents_empty(self, mock_get_client):
        """Test draft documents listing with no results."""
        mock_client = MagicMock()
        mock_client.list_draft_documents.return_value = []
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['list_draft_documents']
        result = tool()
        
        assert "No draft documents found" in result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_list_draft_documents_client_error(self, mock_get_client):
        """Test draft documents listing with client error."""
        mock_get_client.side_effect = OutlineClientError("API Error")
        
        tool = self.mock_mcp.tools['list_draft_documents']
        result = tool()
        
        assert "Error retrieving draft documents: API Error" in result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_get_recently_viewed_documents_success(self, mock_get_client):
        """Test successful recently viewed documents retrieval."""
        mock_client = MagicMock()
        mock_client.get_recently_viewed_documents.return_value = SAMPLE_VIEWED_DOCUMENTS
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['get_recently_viewed_documents']
        result = tool(25)
        
        assert "# Recently Viewed Documents (2 found)" in result
        assert "Recently Viewed Doc 1" in result
        assert "Recently Viewed Doc 2" in result
        mock_client.get_recently_viewed_documents.assert_called_once_with(25)
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_get_recently_viewed_documents_client_error(self, mock_get_client):
        """Test recently viewed documents with client error."""
        mock_get_client.side_effect = OutlineClientError("API Error")
        
        tool = self.mock_mcp.tools['get_recently_viewed_documents']
        result = tool()
        
        assert "Error retrieving recently viewed documents: API Error" in result