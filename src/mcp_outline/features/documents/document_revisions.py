"""
Document revision tools for the MCP Outline server.

This module provides MCP tools for managing document revisions and version history.
"""
from typing import Any, Dict, List

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_revision_info(revision: Dict[str, Any]) -> str:
    """Format revision information into readable text."""
    if not revision:
        return "No revision information found."
    
    revision_id = revision.get("id", "Unknown")
    title = revision.get("title", "Untitled")
    created_at = revision.get("createdAt", "Unknown")
    created_by = revision.get("createdBy", {})
    author_name = created_by.get("name", "Unknown") if created_by else "Unknown"
    
    output = f"# Document Revision\n\n"
    output += f"**Revision ID:** {revision_id}\n"
    output += f"**Title:** {title}\n"
    output += f"**Created:** {created_at}\n"
    output += f"**Author:** {author_name}\n"
    
    # Add text content if available (truncated for readability)
    text = revision.get("text", "")
    if text:
        if len(text) > 500:
            text = text[:500] + "..."
        output += f"\n**Content:**\n{text}\n"
    
    return output


def _format_revisions_list(revisions: List[Dict[str, Any]]) -> str:
    """Format a list of revisions into readable text."""
    if not revisions:
        return "No revisions found for this document."
    
    output = f"# Document Revisions ({len(revisions)} found)\n\n"
    
    for i, revision in enumerate(revisions, 1):
        revision_id = revision.get("id", "Unknown")
        title = revision.get("title", "Untitled")
        created_at = revision.get("createdAt", "Unknown")
        created_by = revision.get("createdBy", {})
        author_name = created_by.get("name", "Unknown") if created_by else "Unknown"
        
        output += f"## {i}. {title}\n"
        output += f"ID: {revision_id}\n"
        output += f"Created: {created_at}\n"
        output += f"Author: {author_name}\n\n"
    
    return output


def register_tools(mcp):
    """Register document revision tools with the MCP server."""
    
    @mcp.tool()
    def get_document_revision(revision_id: str) -> str:
        """
        Get a specific document revision by ID.
        
        Args:
            revision_id: The revision ID to retrieve
            
        Returns:
            Formatted revision information including content and metadata
        """
        try:
            client = get_outline_client()
            revision = client.get_document_revision(revision_id)
            return _format_revision_info(revision)
        except OutlineClientError as e:
            return f"Error retrieving revision: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def list_document_revisions(document_id: str, limit: int = 25) -> str:
        """
        List all revisions for a document.
        
        Args:
            document_id: The document ID to get revisions for
            limit: Maximum number of revisions to return (default: 25)
            
        Returns:
            Formatted list of document revisions with metadata
        """
        try:
            client = get_outline_client()
            revisions = client.list_document_revisions(document_id, limit)
            return _format_revisions_list(revisions)
        except OutlineClientError as e:
            return f"Error retrieving revisions: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def compare_document_revisions(revision_id_1: str, revision_id_2: str) -> str:
        """
        Compare two document revisions and show their differences.
        
        Args:
            revision_id_1: The first revision ID to compare
            revision_id_2: The second revision ID to compare
            
        Returns:
            Formatted comparison showing differences between revisions
        """
        try:
            client = get_outline_client()
            revision_1 = client.get_document_revision(revision_id_1)
            revision_2 = client.get_document_revision(revision_id_2)
            
            if not revision_1 or not revision_2:
                return "One or both revisions could not be found."
            
            # Basic comparison output
            output = "# Revision Comparison\n\n"
            
            # Compare metadata
            title_1 = revision_1.get("title", "Untitled")
            title_2 = revision_2.get("title", "Untitled")
            created_1 = revision_1.get("createdAt", "Unknown")
            created_2 = revision_2.get("createdAt", "Unknown")
            
            output += f"## Revision 1 ({revision_id_1})\n"
            output += f"**Title:** {title_1}\n"
            output += f"**Created:** {created_1}\n\n"
            
            output += f"## Revision 2 ({revision_id_2})\n"
            output += f"**Title:** {title_2}\n"
            output += f"**Created:** {created_2}\n\n"
            
            # Compare content lengths
            text_1 = revision_1.get("text", "")
            text_2 = revision_2.get("text", "")
            
            output += f"## Content Comparison\n"
            output += f"**Revision 1 length:** {len(text_1)} characters\n"
            output += f"**Revision 2 length:** {len(text_2)} characters\n"
            output += f"**Difference:** {len(text_2) - len(text_1)} characters\n\n"
            
            if title_1 != title_2:
                output += f"**Title changed:** '{title_1}' → '{title_2}'\n"
            
            return output
            
        except OutlineClientError as e:
            return f"Error comparing revisions: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"