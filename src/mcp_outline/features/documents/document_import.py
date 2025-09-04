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


def _format_import_result(result: Dict[str, Any]) -> str:
    """Format document import result into readable text."""
    if not result:
        return "Import failed - no result returned."
    
    doc_title = result.get("title", "Untitled")
    doc_id = result.get("id", "")
    created_at = result.get("createdAt", "")
    collection = result.get("collection", {})
    collection_name = (
        collection.get("name", "Unknown") if collection else "Unknown"
    )
    
    output = "# Document Import Successful\n\n"
    output += f"**Title:** {doc_title}\n"
    output += f"**Document ID:** {doc_id}\n"
    output += f"**Collection:** {collection_name}\n"
    if created_at:
        output += f"**Created:** {created_at}\n"
    
    return output


def _validate_import_format(format_type: str) -> bool:
    """Validate that the import format is supported."""
    supported_formats = ["markdown", "text", "html"]
    return format_type.lower() in supported_formats


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
    
    @mcp.tool()
    def import_document(
        title: str,
        text: str,
        collection_id: str = "",
        parent_document_id: str = "",
        format: str = "markdown"
    ) -> str:
        """
        Import a document from external content.
        
        Args:
            title: The title for the imported document
            text: The content to import
            collection_id: Optional collection ID to import into
            parent_document_id: Optional parent document ID
            format: Import format - must be 'markdown', 'text', or 'html' (default: 'markdown')
            
        Returns:
            Formatted result of the document import operation
        """
        try:
            # Validate format
            if not _validate_import_format(format):
                return f"Error: Unsupported format '{format}'. Must be one of: markdown, text, html"
            
            # Validate required fields
            if not title.strip():
                return "Error: Document title is required and cannot be empty."
            
            if not text.strip():
                return "Error: Document content is required and cannot be empty."
            
            client = get_outline_client()
            
            # Convert empty strings to None for optional parameters
            collection_id_param = collection_id if collection_id.strip() else None
            parent_document_id_param = parent_document_id if parent_document_id.strip() else None
            
            result = client.import_document(
                title=title,
                text=text,
                collection_id=collection_id_param,
                parent_document_id=parent_document_id_param,
                format=format.lower()
            )
            
            return _format_import_result(result)
            
        except OutlineClientError as e:
            return f"Error importing document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def import_document_from_file_content(
        title: str,
        file_content: str,
        file_extension: str = "md",
        collection_id: str = "",
        parent_document_id: str = ""
    ) -> str:
        """
        Import a document by automatically detecting format from file extension.
        
        Args:
            title: The title for the imported document
            file_content: The file content to import
            file_extension: File extension to determine format (md, txt, html) (default: 'md')
            collection_id: Optional collection ID to import into
            parent_document_id: Optional parent document ID
            
        Returns:
            Formatted result of the document import operation
        """
        try:
            # Map file extensions to formats
            extension_to_format = {
                "md": "markdown",
                "markdown": "markdown", 
                "txt": "text",
                "text": "text",
                "html": "html",
                "htm": "html"
            }
            
            # Determine format from extension
            ext = file_extension.lower().lstrip(".")
            format_type = extension_to_format.get(ext, "text")
            
            # Use the main import function
            return import_document(
                title=title,
                text=file_content,
                collection_id=collection_id,
                parent_document_id=parent_document_id,
                format=format_type
            )
            
        except Exception as e:
            return f"Error importing document from file content: {str(e)}"