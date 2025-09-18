"""
Common utilities for document outline features.

This module provides shared functionality used by both tools and resources.
"""
import os
from typing import Optional

from mcp_outline.utils.outline_client import OutlineClient, OutlineError


class OutlineClientError(Exception):
    """Exception raised for errors in document outline client operations."""
    pass


def get_outline_client(api_key: Optional[str] = None, api_url: Optional[str] = None) -> OutlineClient:
    """
    Get the document outline client.
    
    Args:
        api_key: Optional API key. If not provided, will use environment variables.
        api_url: Optional API URL. If not provided, will use environment variable or default.
    
    Returns:
        OutlineClient instance
        
    Raises:
        OutlineClientError: If client creation fails
    """
    try:
        # Priority order for API key:
        # 1. Explicitly passed parameter
        # 2. Environment variable
        final_api_key = api_key or os.getenv("OUTLINE_API_KEY")
        final_api_url = api_url or os.getenv("OUTLINE_API_URL")
        
        # Create an instance of the outline client
        client = OutlineClient(api_key=final_api_key, api_url=final_api_url)
        
        # Test the connection by attempting to get auth info
        _ = client.auth_info()
        
        return client
    except OutlineError as e:
        raise OutlineClientError(f"Outline client error: {str(e)}")
    except Exception as e:
        raise OutlineClientError(f"Unexpected error: {str(e)}")


def get_outline_client_from_context(context) -> OutlineClient:
    """
    Get the document outline client using context (for HTTP header authentication).
    
    Extracts API key from HTTP headers when available, with fallback to environment variables.
    
    Supported header formats:
    - Authorization: Bearer <token>
    - X-Outline-API-Key: <token>
    - Outline-API-Key: <token>
    
    Args:
        context: MCP context object containing request information
    
    Returns:
        OutlineClient instance
        
    Raises:
        OutlineClientError: If client creation fails
    """
    api_key = None
    
    try:
        # Try to extract API key from HTTP headers if we have a request context
        if hasattr(context, 'request') and context.request is not None:
            headers = context.request.headers
            
            # Try Authorization: Bearer <token>
            auth_header = headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Try custom Outline API key headers
            if not api_key:
                for header_name in ['x-outline-api-key', 'outline-api-key']:
                    api_key = headers.get(header_name)
                    if api_key:
                        break
                        
    except Exception:
        # If we can't access headers, fall back to environment variables
        pass
    
    # Use the context-extracted API key or fall back to standard method
    return get_outline_client(api_key=api_key)
