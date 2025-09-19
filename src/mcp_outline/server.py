"""
Outline MCP Server

A simple MCP server that provides document outline capabilities.
"""
import logging
import os
from typing import Literal, cast

from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all

# Create a FastMCP server instance with a name and port configuration
mcp = FastMCP("Document Outline", port=3001)

# Register all features
register_all(mcp)


def main():
    # Get transport mode from environment variable, default to stdio for backward compatibility
    transport_mode = os.getenv('MCP_TRANSPORT', 'stdio').lower()

    # Map 'http' to 'streamable-http' for compatibility
    if transport_mode == 'http':
        transport_mode = 'streamable-http'

    # Validate transport mode
    valid_transports = ['stdio', 'sse', 'streamable-http']
    if transport_mode not in valid_transports:
        logging.error(f"Invalid transport mode: {transport_mode}. Must be one of: {valid_transports}")
        transport_mode = 'stdio'

    logging.info(f"Starting MCP Outline server with transport mode: {transport_mode}")

    # Start the server with the specified transport
    if transport_mode == 'streamable-http':
        # For HTTP transport, we need to use the run method without host/port
        # The FastMCP server will handle HTTP configuration internally
        logging.info("HTTP server will start on default configuration")
        mcp.run(transport="streamable-http")
    elif transport_mode == 'sse':
        mcp.run(transport="sse")
    else:  # stdio (default)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
