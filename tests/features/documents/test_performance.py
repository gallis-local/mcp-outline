"""
Basic performance tests for document revision tools.
"""
import time
from unittest.mock import MagicMock, patch

import pytest


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


def generate_large_revision_history(count: int = 100):
    """Generate a large number of test revisions."""
    revisions = []
    for i in range(count):
        revisions.append({
            "id": f"rev{i:03d}",
            "title": f"Document Version {i+1}",
            "text": f"Content for revision {i+1}. " * (10 + i % 50),  # Variable content size
            "createdAt": f"2023-12-{(i % 30) + 1:02d}T{(i % 24):02d}:00:00Z",
            "createdBy": {
                "id": f"user{(i % 5) + 1}",
                "name": f"Author {(i % 5) + 1}"
            }
        })
    return revisions


class TestRevisionPerformance:
    """Performance tests for revision tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MockMCP()
        
        # Import and register tools
        from mcp_outline.features.documents import document_revisions
        document_revisions.register_tools(self.mock_mcp)
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_large_revision_list_performance(self, mock_get_client):
        """Test performance with large revision lists."""
        # Generate 100 revisions
        large_revision_history = generate_large_revision_history(100)
        
        mock_client = MagicMock()
        mock_client.list_document_revisions.return_value = large_revision_history
        mock_get_client.return_value = mock_client
        
        list_tool = self.mock_mcp.tools['list_document_revisions']
        
        # Measure performance
        start_time = time.time()
        result = list_tool("doc123", 100, 0)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify results
        assert "# Document Revisions (100 found)" in result
        assert "rev000" in result
        assert "rev099" in result
        
        # Performance assertion - should process 100 revisions quickly
        assert processing_time < 1.0, f"Processing 100 revisions took too long: {processing_time:.2f}s"
        
        print(f"Processed 100 revisions in {processing_time:.3f} seconds")
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    def test_revision_history_summary_performance(self, mock_get_client):
        """Test performance of revision history analysis with large datasets."""
        # Generate 50 revisions for analysis
        large_revision_history = generate_large_revision_history(50)
        
        mock_client = MagicMock()
        mock_client.list_document_revisions.return_value = large_revision_history
        mock_get_client.return_value = mock_client
        
        summary_tool = self.mock_mcp.tools['get_revision_history_summary']
        
        # Measure performance
        start_time = time.time()
        result = summary_tool("doc123", 50)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify results
        assert "# Revision History Summary" in result
        assert "**Analyzed Revisions:** 50" in result
        assert "## Activity Summary" in result
        assert "## Change Analysis" in result
        
        # Performance assertion - should analyze 50 revisions quickly
        assert processing_time < 1.0, f"Analyzing 50 revisions took too long: {processing_time:.2f}s"
        
        print(f"Analyzed 50 revisions in {processing_time:.3f} seconds")
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_caching_performance_benefit(self, mock_get_cached, mock_get_client):
        """Test that caching improves performance for repeated requests."""
        sample_revision = {
            "id": "rev001",
            "title": "Test Document",
            "text": "Large content " * 1000,  # 13KB of text
            "createdAt": "2023-12-01T10:00:00Z",
            "createdBy": {"id": "user1", "name": "Test User"}
        }
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        get_tool = self.mock_mcp.tools['get_document_revision']
        
        # First call - cache miss
        mock_get_cached.return_value = None
        mock_client.get_document_revision.return_value = sample_revision
        
        start_time = time.time()
        result1 = get_tool("rev001")
        first_call_time = time.time() - start_time
        
        # Second call - cache hit
        mock_get_cached.return_value = sample_revision
        
        start_time = time.time()
        result2 = get_tool("rev001")
        second_call_time = time.time() - start_time
        
        # Verify both calls succeeded
        assert "# Document Revision" in result1
        assert "# Document Revision" in result2
        assert "*[Retrieved from cache]*" in result2
        
        # Cache should provide significant speedup
        speedup_ratio = first_call_time / second_call_time if second_call_time > 0 else float('inf')
        
        print(f"First call: {first_call_time:.4f}s, Second call: {second_call_time:.4f}s")
        print(f"Cache speedup: {speedup_ratio:.1f}x")
        
        # Should be at least 2x faster (conservative estimate)
        assert speedup_ratio > 2.0, f"Cache didn't provide expected speedup: {speedup_ratio:.1f}x"
    
    @patch('mcp_outline.features.documents.document_revisions.get_outline_client')
    @patch('mcp_outline.features.documents.document_revisions._get_cached_revision')
    def test_comparison_performance_with_large_content(self, mock_get_cached, mock_get_client):
        """Test revision comparison performance with large content."""
        # Create large revisions
        large_text_1 = "Version 1 content. " * 5000  # ~95KB
        large_text_2 = "Version 2 content with changes. " * 5000  # ~160KB
        
        revision_1 = {
            "id": "rev001",
            "title": "Large Document v1",
            "text": large_text_1,
            "createdAt": "2023-12-01T10:00:00Z",
            "createdBy": {"id": "user1", "name": "Test User"}
        }
        
        revision_2 = {
            "id": "rev002", 
            "title": "Large Document v2",
            "text": large_text_2,
            "createdAt": "2023-12-01T11:00:00Z",
            "createdBy": {"id": "user1", "name": "Test User"}
        }
        
        mock_get_cached.side_effect = [None, None]  # No cache
        mock_client = MagicMock()
        mock_client.get_document_revision.side_effect = [revision_1, revision_2]
        mock_get_client.return_value = mock_client
        
        compare_tool = self.mock_mcp.tools['compare_document_revisions']
        
        # Measure performance
        start_time = time.time()
        result = compare_tool("rev001", "rev002")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify results
        assert "# Detailed Revision Comparison" in result
        assert "Changes Summary" in result
        assert "chars" in result
        
        # Should handle large content efficiently
        assert processing_time < 2.0, f"Comparing large revisions took too long: {processing_time:.2f}s"
        
        print(f"Compared large revisions ({len(large_text_1)} + {len(large_text_2)} chars) in {processing_time:.3f} seconds")


@pytest.mark.performance  
class TestDocumentImportPerformance:
    """Performance tests for document listing and activity tracking tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mcp = MockMCP()
        
        # Import and register tools
        from mcp_outline.features.documents import document_import
        document_import.register_tools(self.mock_mcp)


if __name__ == "__main__":
    # Run performance tests manually
    test_revision = TestRevisionPerformance()
    test_revision.setup_method()
    
    print("Running performance tests...")
    
    try:
        test_revision.test_large_revision_list_performance()
        print("✓ Large revision list performance test passed")
    except Exception as e:
        print(f"✗ Large revision list performance test failed: {e}")
    
    try:
        test_revision.test_revision_history_summary_performance()
        print("✓ Revision history summary performance test passed")
    except Exception as e:
        print(f"✗ Revision history summary performance test failed: {e}")
    
    print("Performance tests completed!")