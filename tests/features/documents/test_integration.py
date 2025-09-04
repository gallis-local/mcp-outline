"""
Integration tests for document revision and import workflows.
"""
from unittest.mock import MagicMock, patch


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


# Sample test data for integration tests
SAMPLE_DOCUMENT_WITH_REVISIONS = {
    "id": "doc123",
    "title": "Document with History",
    "text": "Current version of the document",
    "updatedAt": "2023-12-04T12:00:00Z"
}

SAMPLE_REVISION_HISTORY = [
    {
        "id": "rev3",
        "title": "Document with History",
        "text": "Third version of the document",
        "createdAt": "2023-12-04T12:00:00Z",
        "createdBy": {"id": "user1", "name": "John Doe"}
    },
    {
        "id": "rev2", 
        "title": "Document with History",
        "text": "Second version",
        "createdAt": "2023-12-04T11:00:00Z",
        "createdBy": {"id": "user1", "name": "John Doe"}
    },
    {
        "id": "rev1",
        "title": "Document with History",
        "text": "First version",
        "createdAt": "2023-12-04T10:00:00Z",
        "createdBy": {"id": "user1", "name": "John Doe"}
    }
]


class TestRevisionAndImportIntegration:
    """Integration tests for revision management and import workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MockMCP()
        
        # Import and register tools from both modules
        from mcp_outline.features.documents import (
            document_import,
            document_revisions,
        )
        document_revisions.register_tools(self.mock_mcp)
        document_import.register_tools(self.mock_mcp)
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_revision_workflow_integration(self, mock_get_client_import, mock_get_client_revision):
        """Test complete revision analysis workflow."""
        # Setup common mock client
        mock_client = MagicMock()
        mock_get_client_revision.return_value = mock_client
        mock_get_client_import.return_value = mock_client
        
        # Mock revision operations
        mock_client.list_document_revisions.return_value = SAMPLE_REVISION_HISTORY
        mock_client.get_document_revision.side_effect = lambda rev_id: next(
            (rev for rev in SAMPLE_REVISION_HISTORY if rev["id"] == rev_id), None
        )
        
        # Test workflow: List revisions -> Get specific revision -> Compare revisions
        
        # 1. List document revisions
        list_tool = self.mock_mcp.tools['list_document_revisions']
        list_result = list_tool("doc123", 10, 0)
        
        assert "# Document Revisions (3 found)" in list_result
        assert "rev3" in list_result
        assert "rev2" in list_result  
        assert "rev1" in list_result
        assert "John Doe" in list_result
        
        # 2. Get specific revision with metadata
        get_tool = self.mock_mcp.tools['get_document_revision_with_metadata']
        get_result = get_tool("rev2")
        
        assert "# Document Revision" in get_result
        assert "rev2" in get_result
        assert "Second version" in get_result
        assert "Revision Statistics" in get_result
        assert "characters" in get_result
        
        # 3. Compare two revisions
        compare_tool = self.mock_mcp.tools['compare_document_revisions']
        compare_result = compare_tool("rev1", "rev2")
        
        assert "# Detailed Revision Comparison" in compare_result
        assert "rev1" in compare_result
        assert "rev2" in compare_result
        assert "Changes Summary" in compare_result
        
        # 4. Get revision history summary
        summary_tool = self.mock_mcp.tools['get_revision_history_summary']
        summary_result = summary_tool("doc123", 10)
        
        assert "# Revision History Summary" in summary_result
        assert "**Analyzed Revisions:** 3" in summary_result
        assert "**Contributors:** 1 unique author(s)" in summary_result
        assert "John Doe" in summary_result
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_workflow_integration(self, mock_get_client):
        """Test complete document import workflow."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock import result
        import_result = {
            "id": "imported_doc1",
            "title": "Imported Document",
            "createdAt": "2023-12-04T13:00:00Z",
            "collection": {"id": "col1", "name": "Test Collection"}
        }
        mock_client.import_document.return_value = import_result
        
        # Mock draft and viewed documents
        mock_client.list_draft_documents.return_value = [
            {"id": "draft1", "title": "Draft Document 1"}
        ]
        mock_client.get_recently_viewed_documents.return_value = [
            {"id": "viewed1", "title": "Recently Viewed Doc 1"}
        ]
        
        # Test workflow: Check drafts -> Import document -> Check result
        
        # 1. List draft documents
        draft_tool = self.mock_mcp.tools['list_draft_documents']
        draft_result = draft_tool(25)
        
        assert "# Draft Documents (1 found)" in draft_result
        assert "Draft Document 1" in draft_result
        
        # 2. Import document
        import_tool = self.mock_mcp.tools['import_document']
        import_result_str = import_tool(
            title="Imported Document",
            text="# Imported Content\n\nThis is imported content.",
            collection_id="col1",
            parent_document_id="",
            format="markdown"
        )
        
        assert "# Document Import Successful" in import_result_str
        assert "Imported Document" in import_result_str
        assert "imported_doc1" in import_result_str
        assert "Test Collection" in import_result_str
        
        # 3. Import document from file content
        file_import_tool = self.mock_mcp.tools['import_document_from_file_content']
        file_import_result = file_import_tool(
            title="File Import Test",
            file_content="# Markdown File\n\nContent from file.",
            file_extension="md",
            collection_id="col1"
        )
        
        assert "# Document Import Successful" in file_import_result
        
        # 4. Get recently viewed documents
        viewed_tool = self.mock_mcp.tools['get_recently_viewed_documents']
        viewed_result = viewed_tool(25)
        
        assert "# Recently Viewed Documents (1 found)" in viewed_result
        assert "Recently Viewed Doc 1" in viewed_result
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_caching_workflow(self, mock_get_cached, mock_get_client):
        """Test caching functionality in revision tools."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # First call: cache miss, then cache hit
        mock_get_cached.side_effect = [None, SAMPLE_REVISION_HISTORY[0]]
        mock_client.get_document_revision.return_value = SAMPLE_REVISION_HISTORY[0]
        
        get_tool = self.mock_mcp.tools['get_document_revision']
        
        # First call - should hit the API
        result1 = get_tool("rev3")
        assert "# Document Revision" in result1
        assert "Third version" in result1
        mock_client.get_document_revision.assert_called_once_with("rev3")
        
        # Second call - should use cache
        result2 = get_tool("rev3")
        assert "# Document Revision" in result2
        assert "Third version" in result2
        assert "*[Retrieved from cache]*" in result2
        
        # Should still only have been called once (cached second time)
        assert mock_client.get_document_revision.call_count == 1
    
    @patch('mcp_outline.features.documents.document_import.get_outline_client')
    def test_import_validation_workflow(self, mock_get_client):
        """Test import validation and error handling."""
        import_tool = self.mock_mcp.tools['import_document']
        
        # Test invalid format
        result1 = import_tool(
            title="Test",
            text="Content",
            format="pdf"
        )
        assert "Error: Unsupported format 'pdf'" in result1
        
        # Test empty title
        result2 = import_tool(
            title="",
            text="Content"
        )
        assert "Error: Document title is required" in result2
        
        # Test empty content
        result3 = import_tool(
            title="Test Title",
            text=""
        )
        assert "Error: Document content is required" in result3
        
        # Verify no API calls were made for validation errors
        mock_get_client.assert_not_called()