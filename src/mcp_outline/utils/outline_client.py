"""
Client for interacting with Outline API.

A simple client for making requests to the Outline API.
"""
import os
from typing import Any, Dict, List, Optional

import requests


class OutlineError(Exception):
    """Exception for all Outline API errors."""
    pass

class OutlineClient:
    """Simple client for Outline API services."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_url: Optional[str] = None
    ):
        """
        Initialize the Outline client.
        
        Args:
            api_key: Outline API key or from OUTLINE_API_KEY env var.
            api_url: Outline API URL or from OUTLINE_API_URL env var.
        
        Raises:
            OutlineError: If API key is missing.
        """
        # Load configuration from environment variables if not provided
        self.api_key = api_key or os.getenv("OUTLINE_API_KEY")
        self.api_url = api_url or os.getenv("OUTLINE_API_URL", "https://app.getoutline.com/api")
        
        # Ensure API key is provided
        if not self.api_key:
            raise OutlineError("Missing API key. Set OUTLINE_API_KEY env var.")
    
    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request to the Outline API.
        
        Args:
            endpoint: The API endpoint to call.
            data: The request payload.
            
        Returns:
            The parsed JSON response.
            
        Raises:
            OutlineError: If the request fails.
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data or {})
            # Raise exception for 4XX/5XX responses
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OutlineError(f"API request failed: {str(e)}")
    
    def auth_info(self) -> Dict[str, Any]:
        """
        Verify authentication and get user information.
        
        Returns:
            Dict containing user and team information.
        """
        response = self.post("auth.info")
        return response.get("data", {})
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            Document information.
        """
        response = self.post("documents.info", {"id": document_id})
        return response.get("data", {})
    
    def search_documents(
        self, 
        query: str, 
        collection_id: Optional[str] = None, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using keywords.
        
        Args:
            query: Search terms
            collection_id: Optional collection to search within
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with context
        """
        data: Dict[str, Any] = {"query": query, "limit": limit}
        if collection_id:
            data["collectionId"] = collection_id
            
        response = self.post("documents.search", data)
        return response.get("data", [])
    
    def list_collections(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List all available collections.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of collections
        """
        response = self.post("collections.list", {"limit": limit})
        return response.get("data", [])
    
    def get_collection_documents(
        self, collection_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get document structure for a collection.
        
        Args:
            collection_id: The collection ID.
            
        Returns:
            List of document nodes in the collection.
        """
        response = self.post("collections.documents", {"id": collection_id})
        return response.get("data", [])
    
    def list_documents(
        self, 
        collection_id: Optional[str] = None, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List documents with optional filtering.
        
        Args:
            collection_id: Optional collection to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of documents
        """
        data: Dict[str, Any] = {"limit": limit}
        if collection_id:
            data["collectionId"] = collection_id
            
        response = self.post("documents.list", data)
        return response.get("data", [])
    
    def archive_document(self, document_id: str) -> Dict[str, Any]:
        """
        Archive a document by ID.
        
        Args:
            document_id: The document ID to archive.
            
        Returns:
            The archived document data.
        """
        response = self.post("documents.archive", {"id": document_id})
        return response.get("data", {})
    
    def unarchive_document(self, document_id: str) -> Dict[str, Any]:
        """
        Unarchive a document by ID.
        
        Args:
            document_id: The document ID to unarchive.
            
        Returns:
            The unarchived document data.
        """
        response = self.post("documents.unarchive", {"id": document_id})
        return response.get("data", {})
        
    def list_trash(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        List documents in the trash.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of documents in trash
        """
        response = self.post(
            "documents.list", {"limit": limit, "deleted": True}
        )
        return response.get("data", [])
    
    def restore_document(self, document_id: str) -> Dict[str, Any]:
        """
        Restore a document from trash.
        
        Args:
            document_id: The document ID to restore.
            
        Returns:
            The restored document data.
        """
        response = self.post("documents.restore", {"id": document_id})
        return response.get("data", {})
    
    def permanently_delete_document(self, document_id: str) -> bool:
        """
        Permanently delete a document by ID.
        
        Args:
            document_id: The document ID to permanently delete.
            
        Returns:
            Success status.
        """
        response = self.post("documents.delete", {
            "id": document_id,
            "permanent": True
        })
        return response.get("success", False)
    
    # Collection management methods
    def create_collection(
        self, 
        name: str, 
        description: str = "", 
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new collection.
        
        Args:
            name: The name of the collection
            description: Optional description for the collection
            color: Optional hex color code for the collection
            
        Returns:
            The created collection data
        """
        data: Dict[str, Any] = {
            "name": name,
            "description": description
        }
        
        if color:
            data["color"] = color
            
        response = self.post("collections.create", data)
        return response.get("data", {})
    
    def update_collection(
        self, 
        collection_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None, 
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing collection.
        
        Args:
            collection_id: The ID of the collection to update
            name: Optional new name for the collection
            description: Optional new description
            color: Optional new hex color code
            
        Returns:
            The updated collection data
        """
        data: Dict[str, Any] = {"id": collection_id}
        
        if name is not None:
            data["name"] = name
            
        if description is not None:
            data["description"] = description
            
        if color is not None:
            data["color"] = color
            
        response = self.post("collections.update", data)
        return response.get("data", {})
    
    def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection and all its documents.
        
        Args:
            collection_id: The ID of the collection to delete
            
        Returns:
            Success status
        """
        response = self.post("collections.delete", {"id": collection_id})
        return response.get("success", False)
    

    def answer_question(self, 
                       query: str,
                       collection_id: Optional[str] = None, 
                       document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a natural language question about document content.
        
        Args:
            query: The natural language question to answer
            collection_id: Optional collection to search within
            document_id: Optional document to search within
            
        Returns:
            Dictionary containing AI answer and search results
        """
        data: Dict[str, Any] = {"query": query}
        
        if collection_id:
            data["collectionId"] = collection_id
            
        if document_id:
            data["documentId"] = document_id
            
        response = self.post("documents.answerQuestion", data)
        return response
    
    # Document revision methods
    def get_document_revision(self, revision_id: str) -> Dict[str, Any]:
        """
        Get a specific document revision by ID.
        
        Args:
            revision_id: The revision ID to retrieve.
            
        Returns:
            The revision data.
        """
        response = self.post("revisions.info", {"id": revision_id})
        return response.get("data", {})
    
    def list_document_revisions(
        self, 
        document_id: str, 
        limit: int = 25,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all revisions for a document with pagination support.
        
        Args:
            document_id: The document ID to get revisions for.
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of document revisions
        """
        data = {
            "documentId": document_id, 
            "limit": limit
        }
        
        # Add offset for pagination if provided
        if offset > 0:
            data["offset"] = offset
            
        response = self.post("revisions.list", data)
        return response.get("data", [])
    
    # Draft and activity tracking methods
    def list_draft_documents(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        List draft documents for the current user.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of draft documents
        """
        response = self.post("documents.drafts", {"limit": limit})
        return response.get("data", [])
    
    def get_recently_viewed_documents(
        self, 
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Get recently viewed documents for the current user.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of recently viewed documents
        """
        response = self.post("documents.viewed", {"limit": limit})
        return response.get("data", [])
