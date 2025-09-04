"""
Tests for document import and activity tracking tools.
"""
from unittest.mock import MagicMock, patch

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_import import (
    _format_documents_list,
    _format_import_result,
    _validate_import_format,
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

SAMPLE_IMPORT_RESULT = {
    "id": "doc5",
    "title": "Imported Document",
    "createdAt": "2023-12-04T13:00:00Z",
    "collection": {
        "id": "col1",
        "name": "Test Collection"
    }
}


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
    
    def test_format_import_result_success(self):
        """Test formatting successful import result."""
        result = _format_import_result(SAMPLE_IMPORT_RESULT)
        
        assert "# Document Import Successful" in result
        assert "Imported Document" in result
        assert "doc5" in result
        assert "Test Collection" in result
        assert "2023-12-04T13:00:00Z" in result
    
    def test_format_import_result_empty(self):
        """Test formatting empty import result."""
        result = _format_import_result({})
        
        assert "Import failed - no result returned" in result
    
    def test_format_import_result_missing_fields(self):
        """Test formatting import result with missing fields."""
        partial_result = {"id": "doc7", "title": "Partial Import"}
        result = _format_import_result(partial_result)
        
        assert "# Document Import Successful" in result
        assert "doc7" in result
        assert "Partial Import" in result
        assert "Unknown" in result  # For missing collection
    
    def test_validate_import_format_valid(self):
        """Test validation of valid import formats."""
        assert _validate_import_format("markdown") is True
        assert _validate_import_format("text") is True
        assert _validate_import_format("html") is True
        assert _validate_import_format("MARKDOWN") is True  # Case insensitive
    
    def test_validate_import_format_invalid(self):
        """Test validation of invalid import formats."""
        assert _validate_import_format("pdf") is False
        assert _validate_import_format("docx") is False
        assert _validate_import_format("") is False
        assert _validate_import_format("invalid") is False


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
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_success(self, mock_get_client):
        """Test successful document import."""
        mock_client = MagicMock()
        mock_client.import_document.return_value = SAMPLE_IMPORT_RESULT
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['import_document']
        result = tool(
            title="Test Import",
            text="# Test Content\n\nThis is imported content.",
            collection_id="col1",
            parent_document_id="",
            format="markdown"
        )
        
        assert "# Document Import Successful" in result
        assert "Imported Document" in result
        mock_client.import_document.assert_called_once_with(
            title="Test Import",
            text="# Test Content\n\nThis is imported content.",
            collection_id="col1",
            parent_document_id=None,
            format="markdown"
        )
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_invalid_format(self, mock_get_client):
        """Test document import with invalid format."""
        tool = self.mock_mcp.tools['import_document']
        result = tool(
            title="Test Import",
            text="Test content",
            format="pdf"
        )
        
        assert "Error: Unsupported format 'pdf'" in result
        assert "markdown, text, html" in result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_empty_title(self, mock_get_client):
        """Test document import with empty title."""
        tool = self.mock_mcp.tools['import_document']
        result = tool(
            title="",
            text="Test content"
        )
        
        assert "Error: Document title is required" in result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_empty_text(self, mock_get_client):
        """Test document import with empty text."""
        tool = self.mock_mcp.tools['import_document']
        result = tool(
            title="Test Title",
            text=""
        )
        
        assert "Error: Document content is required" in result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_client_error(self, mock_get_client):
        """Test document import with client error."""
        mock_client = MagicMock()
        mock_client.import_document.side_effect = OutlineClientError("Import failed")
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['import_document']
        result = tool(
            title="Test Import",
            text="Test content"
        )
        
        assert "Error importing document: Import failed" in result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_from_file_content_markdown(self, mock_get_client):
        """Test importing document from file content with markdown extension."""
        mock_client = MagicMock()
        mock_client.import_document.return_value = SAMPLE_IMPORT_RESULT
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['import_document_from_file_content']
        result = tool(
            title="Test MD Import",
            file_content="# Markdown Content\n\nThis is markdown.",
            file_extension="md",
            collection_id="col1"
        )
        
        assert "# Document Import Successful" in result
        mock_client.import_document.assert_called_once_with(
            title="Test MD Import",
            text="# Markdown Content\n\nThis is markdown.",
            collection_id="col1",
            parent_document_id=None,
            format="markdown"
        )
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_from_file_content_text(self, mock_get_client):
        """Test importing document from file content with text extension."""
        mock_client = MagicMock()
        mock_client.import_document.return_value = SAMPLE_IMPORT_RESULT
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['import_document_from_file_content']
        result = tool(
            title="Test TXT Import",
            file_content="Plain text content.",
            file_extension="txt"
        )
        
        assert "# Document Import Successful" in result
        mock_client.import_document.assert_called_once_with(
            title="Test TXT Import",
            text="Plain text content.",
            collection_id=None,
            parent_document_id=None,
            format="text"
        )
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_from_file_content_html(self, mock_get_client):
        """Test importing document from file content with HTML extension."""
        mock_client = MagicMock()
        mock_client.import_document.return_value = SAMPLE_IMPORT_RESULT
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['import_document_from_file_content']
        result = tool(
            title="Test HTML Import",
            file_content="<h1>HTML Content</h1><p>This is HTML.</p>",
            file_extension="html"
        )
        
        assert "# Document Import Successful" in result
        mock_client.import_document.assert_called_once_with(
            title="Test HTML Import",
            text="<h1>HTML Content</h1><p>This is HTML.</p>",
            collection_id=None,
            parent_document_id=None,
            format="html"
        )
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_document_from_file_content_unknown_extension(self, mock_get_client):
        """Test importing document from file content with unknown extension defaults to text."""
        mock_client = MagicMock()
        mock_client.import_document.return_value = SAMPLE_IMPORT_RESULT
        mock_get_client.return_value = mock_client
        
        tool = self.mock_mcp.tools['import_document_from_file_content']
        result = tool(
            title="Test Unknown Import",
            file_content="Unknown format content.",
            file_extension="xyz"
        )
        
        assert "# Document Import Successful" in result
        mock_client.import_document.assert_called_once_with(
            title="Test Unknown Import",
            text="Unknown format content.",
            collection_id=None,
            parent_document_id=None,
            format="text"
        )