"""
Integration tests for HTTP transport functionality.

Tests the FastMCP server with streamable-http transport including:
- Server startup with HTTP transport
- HTTP endpoint availability and responsiveness
- Basic HTTP communication
- Port binding and configuration
"""
import asyncio
import json
import os
import signal
import subprocess
import time
from unittest.mock import patch
import pytest
import httpx


class TestHTTPTransportStartup:
    """Test HTTP transport server startup and basic functionality."""
    
    def test_server_startup_with_http_transport(self):
        """Test that server can start with streamable-http transport."""
        # This test uses subprocess to actually start the server briefly
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-key'  # Required for server start
        
        # Start server process
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            # Give server time to start
            time.sleep(2)
            
            # Check if process is still running (not crashed)
            assert process.poll() is None, "Server process terminated unexpectedly"
            
        finally:
            # Clean up process
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
    
    def test_server_startup_with_http_compatibility_mapping(self):
        """Test that server starts when MCP_TRANSPORT=http (maps to streamable-http)."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'http'  # Should map to streamable-http
        env['OUTLINE_API_KEY'] = 'test-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            time.sleep(2)
            assert process.poll() is None, "Server process terminated unexpectedly"
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


class TestHTTPEndpointAvailability:
    """Test HTTP endpoint availability and basic responses."""
    
    @pytest.fixture
    def http_server_process(self):
        """Start HTTP server for testing."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        # Give server time to start
        time.sleep(3)
        
        yield process
        
        # Cleanup
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
    
    @pytest.mark.asyncio
    async def test_http_server_responds_to_requests(self, http_server_process):
        """Test that HTTP server responds to basic requests."""
        # Verify server is running
        assert http_server_process.poll() is None
        
        # Test basic HTTP connectivity on port 3001
        try:
            async with httpx.AsyncClient() as client:
                # Try to connect to the server (may get 404, but should connect)
                response = await client.get("http://localhost:3001/", timeout=5.0)
                
                # Server should respond (even if with an error status)
                # The key is that we get a response, not a connection error
                assert response.status_code in [200, 404, 405, 422]
                
        except httpx.ConnectError:
            pytest.fail("Could not connect to HTTP server on port 3001")
    
    @pytest.mark.asyncio
    async def test_sse_endpoint_availability(self, http_server_process):
        """Test that SSE endpoint is available."""
        assert http_server_process.poll() is None
        
        try:
            async with httpx.AsyncClient() as client:
                # FastMCP typically exposes /sse endpoint
                response = await client.get("http://localhost:3001/sse", timeout=5.0)
                
                # Should get some response (200 for SSE or 405 for method not allowed)
                assert response.status_code in [200, 405, 422]
                
        except httpx.ConnectError:
            pytest.fail("SSE endpoint not accessible")


class TestHTTPTransportConfiguration:
    """Test HTTP transport configuration and port binding."""
    
    def test_http_transport_uses_correct_port(self):
        """Test that HTTP transport binds to port 3001."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            time.sleep(2)
            
            # Check if server is listening on port 3001
            # We can use netstat or ss to check, but subprocess approach is simpler
            check_port = subprocess.run(
                ['netstat', '-ln'], 
                capture_output=True, 
                text=True
            )
            
            # Look for port 3001 in listening ports
            assert ':3001' in check_port.stdout, "Server not listening on port 3001"
            
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


class TestHTTPTransportErrorHandling:
    """Test error handling in HTTP transport mode."""
    
    def test_server_startup_without_api_key(self):
        """Test server behavior when OUTLINE_API_KEY is missing."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        # Don't set OUTLINE_API_KEY
        if 'OUTLINE_API_KEY' in env:
            del env['OUTLINE_API_KEY']
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            # Server might start but tools won't work without API key
            time.sleep(2)
            
            # Check stderr for any API key related warnings
            stdout, stderr = process.communicate(timeout=3)
            
            # Server should handle missing API key gracefully
            # (Either start with warnings or fail cleanly)
            if process.returncode is not None:
                # If it exited, it should be a clean exit
                assert process.returncode in [0, 1]
            
        except subprocess.TimeoutExpired:
            # Server is still running, which is also acceptable
            process.terminate()
            process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


class TestHTTPTransportLogging:
    """Test logging behavior for HTTP transport."""
    
    def test_http_transport_startup_logging(self):
        """Test that HTTP transport logs appropriate startup messages."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            # Let server start and capture initial output
            time.sleep(2)
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            
            # Check for expected log messages
            combined_output = stdout + stderr
            
            # Should log transport mode selection
            assert "streamable-http" in combined_output or "HTTP" in combined_output
            
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


class TestHTTPTransportCompatibility:
    """Test compatibility features for HTTP transport."""
    
    def test_http_maps_to_streamable_http(self):
        """Test that MCP_TRANSPORT=http correctly maps to streamable-http."""
        with patch('mcp_outline.server.mcp.run') as mock_run, \
             patch.dict(os.environ, {'MCP_TRANSPORT': 'http'}):
            
            from mcp_outline.server import main
            main()
            
            # Should call with streamable-http, not http
            mock_run.assert_called_once_with(transport="streamable-http")
    
    def test_backwards_compatibility_maintained(self):
        """Test that existing stdio/sse modes still work."""
        # Test stdio
        with patch('mcp_outline.server.mcp.run') as mock_run, \
             patch.dict(os.environ, {'MCP_TRANSPORT': 'stdio'}):
            
            from mcp_outline.server import main
            main()
            mock_run.assert_called_with(transport="stdio")
        
        # Test sse
        with patch('mcp_outline.server.mcp.run') as mock_run, \
             patch.dict(os.environ, {'MCP_TRANSPORT': 'sse'}):
            
            from mcp_outline.server import main
            main() 
            mock_run.assert_called_with(transport="sse")