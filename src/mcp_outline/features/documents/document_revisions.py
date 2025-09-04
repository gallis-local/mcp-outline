"""
Document revision tools for the MCP Outline server.

This module provides MCP tools for managing document revisions and version history.
"""
from typing import Any, Dict, List
import time

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


# Simple in-memory cache for frequently accessed revisions
_revision_cache = {}
_cache_expiry = 300  # 5 minutes


def _get_cached_revision(revision_id: str) -> Dict[str, Any] | None:
    """Get revision from cache if available and not expired."""
    if revision_id in _revision_cache:
        cached_data, timestamp = _revision_cache[revision_id]
        if time.time() - timestamp < _cache_expiry:
            return cached_data
        else:
            del _revision_cache[revision_id]
    return None


def _cache_revision(revision_id: str, revision_data: Dict[str, Any]) -> None:
    """Cache revision data with timestamp."""
    _revision_cache[revision_id] = (revision_data, time.time())


def _clear_expired_cache() -> None:
    """Clear expired cache entries."""
    current_time = time.time()
    expired_keys = [
        key for key, (_, timestamp) in _revision_cache.items()
        if current_time - timestamp >= _cache_expiry
    ]
    for key in expired_keys:
        del _revision_cache[key]


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


def _format_revisions_list(revisions: List[Dict[str, Any]], pagination_info: str = "") -> str:
    """Format a list of revisions into readable text."""
    if not revisions:
        return "No revisions found for this document."
    
    output = f"# Document Revisions ({len(revisions)} found)\n"
    if pagination_info:
        output += f"{pagination_info}\n"
    output += "\n"
    
    for i, revision in enumerate(revisions, 1):
        revision_id = revision.get("id", "Unknown")
        title = revision.get("title", "Untitled")
        created_at = revision.get("createdAt", "Unknown")
        created_by = revision.get("createdBy", {})
        author_name = created_by.get("name", "Unknown") if created_by else "Unknown"
        author_email = created_by.get("email", "") if created_by else ""
        
        # Calculate content length if available
        text = revision.get("text", "")
        content_length = len(text) if text else 0
        
        output += f"## {i}. {title}\n"
        output += f"**ID:** {revision_id}\n"
        output += f"**Created:** {created_at}\n"
        output += f"**Author:** {author_name}"
        if author_email:
            output += f" ({author_email})"
        output += "\n"
        output += f"**Content Length:** {content_length} characters\n\n"
    
    return output


def _analyze_text_changes(text1: str, text2: str) -> Dict[str, Any]:
    """Analyze changes between two text versions."""
    lines1 = text1.split('\n') if text1 else []
    lines2 = text2.split('\n') if text2 else []
    
    # Basic line-level analysis
    added_lines = len(lines2) - len(lines1)
    
    # Word-level analysis
    words1 = text1.split() if text1 else []
    words2 = text2.split() if text2 else []
    added_words = len(words2) - len(words1)
    
    # Character-level analysis
    char_change = len(text2) - len(text1)
    
    return {
        "lines_added": added_lines,
        "words_added": added_words,
        "chars_added": char_change,
        "total_lines_1": len(lines1),
        "total_lines_2": len(lines2),
        "total_words_1": len(words1),
        "total_words_2": len(words2),
        "total_chars_1": len(text1),
        "total_chars_2": len(text2)
    }


def _enrich_revision_metadata(revision: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich revision data with calculated metadata."""
    enriched = revision.copy()
    
    # Add content statistics
    text = revision.get("text", "")
    enriched["contentLength"] = len(text)
    enriched["wordCount"] = len(text.split()) if text else 0
    enriched["lineCount"] = text.count('\n') + 1 if text else 0
    
    # Parse and format creation date
    created_at = revision.get("createdAt", "")
    if created_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            enriched["createdAtFormatted"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, ImportError):
            enriched["createdAtFormatted"] = created_at
    
    return enriched
    """Enrich revision data with calculated metadata."""
    enriched = revision.copy()
    
    # Add content statistics
    text = revision.get("text", "")
    enriched["contentLength"] = len(text)
    enriched["wordCount"] = len(text.split()) if text else 0
    enriched["lineCount"] = text.count('\n') + 1 if text else 0
    
    # Parse and format creation date
    created_at = revision.get("createdAt", "")
    if created_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            enriched["createdAtFormatted"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, ImportError):
            enriched["createdAtFormatted"] = created_at
    
    return enriched


def register_tools(mcp):
    """Register document revision tools with the MCP server."""
    
    @mcp.tool()
    def get_document_revision(revision_id: str) -> str:
        """
        Get a specific document revision by ID with caching.
        
        Args:
            revision_id: The revision ID to retrieve
            
        Returns:
            Formatted revision information including content and metadata
        """
        try:
            # Check cache first
            cached_revision = _get_cached_revision(revision_id)
            if cached_revision:
                return _format_revision_info(cached_revision) + "\n*[Retrieved from cache]*"
            
            # Clear expired cache entries periodically
            _clear_expired_cache()
            
            client = get_outline_client()
            revision = client.get_document_revision(revision_id)
            
            # Cache the result
            if revision:
                _cache_revision(revision_id, revision)
            
            return _format_revision_info(revision)
        except OutlineClientError as e:
            return f"Error retrieving revision: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def list_document_revisions(document_id: str, limit: int = 25, offset: int = 0) -> str:
        """
        List all revisions for a document with pagination support.
        
        Args:
            document_id: The document ID to get revisions for
            limit: Maximum number of revisions to return (default: 25, max: 100)
            offset: Number of revisions to skip for pagination (default: 0)
            
        Returns:
            Formatted list of document revisions with metadata and pagination info
        """
        try:
            # Validate parameters
            if limit > 100:
                limit = 100
            if offset < 0:
                offset = 0
                
            client = get_outline_client()
            revisions = client.list_document_revisions(document_id, limit, offset)
            
            # Create pagination info
            pagination_info = f"Showing {len(revisions)} revisions"
            if offset > 0:
                pagination_info += f" (starting from #{offset + 1})"
            if len(revisions) == limit:
                pagination_info += f". Use offset={offset + limit} to see more."
            
            return _format_revisions_list(revisions, pagination_info)
        except OutlineClientError as e:
            return f"Error retrieving revisions: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_document_revision_with_metadata(revision_id: str) -> str:
        """
        Get a specific document revision with enriched metadata.
        
        Args:
            revision_id: The revision ID to retrieve
            
        Returns:
            Formatted revision information with enriched metadata including content statistics
        """
        try:
            client = get_outline_client()
            revision = client.get_document_revision(revision_id)
            
            if not revision:
                return "No revision found with the specified ID."
            
            # Enrich with metadata
            enriched_revision = _enrich_revision_metadata(revision)
            
            # Format with additional metadata
            output = _format_revision_info(revision)
            
            # Add enriched metadata section
            output += "\n## Revision Statistics\n"
            output += f"**Content Length:** {enriched_revision.get('contentLength', 0)} characters\n"
            output += f"**Word Count:** {enriched_revision.get('wordCount', 0)} words\n"
            output += f"**Line Count:** {enriched_revision.get('lineCount', 0)} lines\n"
            
            formatted_date = enriched_revision.get('createdAtFormatted')
            if formatted_date:
                output += f"**Created (formatted):** {formatted_date}\n"
            
            return output
            
        except OutlineClientError as e:
            return f"Error retrieving revision: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def compare_document_revisions(revision_id_1: str, revision_id_2: str) -> str:
        """
        Compare two document revisions and show their differences with detailed analysis.
        
        Args:
            revision_id_1: The first revision ID to compare
            revision_id_2: The second revision ID to compare
            
        Returns:
            Formatted comparison showing differences between revisions with detailed statistics
        """
        try:
            client = get_outline_client()
            
            # Try to get from cache first
            revision_1 = _get_cached_revision(revision_id_1)
            if not revision_1:
                revision_1 = client.get_document_revision(revision_id_1)
                if revision_1:
                    _cache_revision(revision_id_1, revision_1)
            
            revision_2 = _get_cached_revision(revision_id_2)
            if not revision_2:
                revision_2 = client.get_document_revision(revision_id_2)
                if revision_2:
                    _cache_revision(revision_id_2, revision_2)
            
            if not revision_1 or not revision_2:
                return "One or both revisions could not be found."
            
            # Check if revisions have required data
            if not isinstance(revision_1, dict) or not isinstance(revision_2, dict):
                return "One or both revisions could not be found."
            
            # Enhanced comparison output
            output = "# Detailed Revision Comparison\n\n"
            
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
            
            # Analyze content changes
            text_1 = revision_1.get("text", "")
            text_2 = revision_2.get("text", "")
            
            changes = _analyze_text_changes(text_1, text_2)
            
            output += "## Content Analysis\n"
            output += f"**Revision 1:** {changes['total_chars_1']} chars, {changes['total_words_1']} words, {changes['total_lines_1']} lines\n"
            output += f"**Revision 2:** {changes['total_chars_2']} chars, {changes['total_words_2']} words, {changes['total_lines_2']} lines\n\n"
            
            output += "## Changes Summary\n"
            output += f"**Characters:** {changes['chars_added']:+d} ({abs(changes['chars_added'])} {'added' if changes['chars_added'] >= 0 else 'removed'})\n"
            output += f"**Words:** {changes['words_added']:+d} ({abs(changes['words_added'])} {'added' if changes['words_added'] >= 0 else 'removed'})\n"
            output += f"**Lines:** {changes['lines_added']:+d} ({abs(changes['lines_added'])} {'added' if changes['lines_added'] >= 0 else 'removed'})\n\n"
            
            # Title change detection
            if title_1 != title_2:
                output += f"**Title changed:** '{title_1}' → '{title_2}'\n\n"
            
            # Change magnitude assessment
            if changes['total_chars_1'] > 0:
                change_percentage = abs(changes['chars_added']) / changes['total_chars_1'] * 100
                output += f"**Change magnitude:** {change_percentage:.1f}% of original content\n"
                
                if change_percentage < 5:
                    output += "*Minor changes*\n"
                elif change_percentage < 25:
                    output += "*Moderate changes*\n"
                else:
                    output += "*Major changes*\n"
            
            return output
            
        except OutlineClientError as e:
            return f"Error comparing revisions: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_revision_history_summary(document_id: str, limit: int = 10) -> str:
        """
        Get a summary of revision history for a document with change analysis.
        
        Args:
            document_id: The document ID to analyze revision history for
            limit: Maximum number of recent revisions to analyze (default: 10)
            
        Returns:
            Formatted summary showing revision history patterns and statistics
        """
        try:
            client = get_outline_client()
            revisions = client.list_document_revisions(document_id, limit)
            
            if not revisions:
                return "No revisions found for this document."
            
            if len(revisions) < 2:
                return "Insufficient revision history for analysis (need at least 2 revisions)."
            
            output = f"# Revision History Summary\n"
            output += f"**Document ID:** {document_id}\n"
            output += f"**Analyzed Revisions:** {len(revisions)}\n\n"
            
            # Analyze patterns
            total_authors = set()
            revision_sizes = []
            time_gaps = []
            
            for i, revision in enumerate(revisions):
                # Track authors
                created_by = revision.get("createdBy", {})
                if created_by:
                    author_name = created_by.get("name")
                    if author_name:
                        total_authors.add(author_name)
                
                # Track content sizes
                text = revision.get("text", "")
                revision_sizes.append(len(text))
                
                # Calculate time gaps between revisions
                if i > 0:
                    try:
                        from datetime import datetime
                        current_time = revision.get("createdAt", "")
                        previous_time = revisions[i-1].get("createdAt", "")
                        
                        if current_time and previous_time:
                            dt1 = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                            dt2 = datetime.fromisoformat(previous_time.replace('Z', '+00:00'))
                            gap_hours = abs((dt1 - dt2).total_seconds() / 3600)
                            time_gaps.append(gap_hours)
                    except (ValueError, ImportError):
                        pass
            
            # Summary statistics
            output += "## Activity Summary\n"
            output += f"**Contributors:** {len(total_authors)} unique author(s)\n"
            if total_authors:
                output += f"**Authors:** {', '.join(sorted(total_authors))}\n"
            
            if revision_sizes:
                avg_size = sum(revision_sizes) / len(revision_sizes)
                output += f"**Average content size:** {avg_size:.0f} characters\n"
                output += f"**Content size range:** {min(revision_sizes)} - {max(revision_sizes)} characters\n"
            
            if time_gaps:
                avg_gap = sum(time_gaps) / len(time_gaps)
                output += f"**Average time between revisions:** {avg_gap:.1f} hours\n"
                
                if avg_gap < 1:
                    output += "*Rapid editing pattern*\n"
                elif avg_gap < 24:
                    output += "*Active editing pattern*\n"
                else:
                    output += "*Infrequent editing pattern*\n"
            
            # Change magnitude analysis
            if len(revision_sizes) >= 2:
                output += "\n## Change Analysis\n"
                size_changes = []
                for i in range(1, len(revision_sizes)):
                    change = revision_sizes[i-1] - revision_sizes[i]  # Newer to older
                    size_changes.append(change)
                
                if size_changes:
                    total_change = sum(abs(change) for change in size_changes)
                    avg_change = total_change / len(size_changes)
                    output += f"**Average change size:** {avg_change:.0f} characters per revision\n"
                    
                    additions = sum(change for change in size_changes if change > 0)
                    deletions = sum(abs(change) for change in size_changes if change < 0)
                    output += f"**Total additions:** {additions} characters\n"
                    output += f"**Total deletions:** {deletions} characters\n"
                    output += f"**Net change:** {additions - deletions:+d} characters\n"
            
            return output
            
        except OutlineClientError as e:
            return f"Error analyzing revision history: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"