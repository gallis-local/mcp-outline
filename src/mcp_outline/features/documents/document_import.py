"""
Document import and activity tracking tools for the MCP Outline server.

This module provides MCP tools for importing documents and tracking user
activity.
"""
from typing import Any, Dict, List

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_documents_list(documents: List[Dict[str, Any]], title: str) -> str:
    """Format a list of documents into readable text."""
    if not documents:
        return f"No {title.lower()} found."
    
    output = f"# {title} ({len(documents)} found)\n\n"
    
    for i, document in enumerate(documents, 1):
        doc_title = document.get("title", "Untitled")
        doc_id = document.get("id", "")
        updated_at = document.get("updatedAt", "")
        created_at = document.get("createdAt", "")
        
        output += f"## {i}. {doc_title}\n"
        output += f"ID: {doc_id}\n"
        if updated_at:
            output += f"Last Updated: {updated_at}\n"
        if created_at:
            output += f"Created: {created_at}\n"
        output += "\n"
    
    return output





def register_tools(mcp):
    """Register document import and activity tracking tools with the MCP
    server."""
    
    @mcp.tool()
    def list_draft_documents(limit: int = 25) -> str:
        """
        List draft documents for the current user.
        
        Args:
            limit: Maximum number of draft documents to return (default: 25)
            
        Returns:
            Formatted list of draft documents
        """
        try:
            client = get_outline_client()
            drafts = client.list_draft_documents(limit)
            return _format_documents_list(drafts, "Draft Documents")
        except OutlineClientError as e:
            return f"Error retrieving draft documents: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_recently_viewed_documents(limit: int = 25) -> str:
        """
        Get recently viewed documents for the current user.
        
        Args:
            limit: Maximum number of recently viewed documents to return (default: 25)
            
        Returns:
            Formatted list of recently viewed documents
        """
        try:
            client = get_outline_client()
            viewed_docs = client.get_recently_viewed_documents(limit)
            return _format_documents_list(viewed_docs, "Recently Viewed Documents")
        except OutlineClientError as e:
            return f"Error retrieving recently viewed documents: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"