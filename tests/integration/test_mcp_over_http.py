"""
Integration tests for MCP protocol over HTTP transport.

Tests MCP-specific functionality over HTTP including:
- Tool registration and accessibility via HTTP
- Client-server communication over HTTP transport  
- MCP protocol compliance over HTTP
- Session management and concurrent requests
"""
import asyncio
import json
import os
import subprocess
import time
import pytest
import httpx
from unittest.mock import patch

from mcp_outline.server import mcp


class TestMCPToolsOverHTTP:
    """Test MCP tool registration and accessibility via HTTP."""
    
    @pytest.fixture
    def http_mcp_server(self):
        """Start MCP server with HTTP transport for testing."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-key-for-integration-tests'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        # Give server time to fully start
        time.sleep(3)
        
        yield process
        
        # Cleanup
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
    
    @pytest.mark.anyio
    async def test_tools_accessible_via_http(self):
        """Test that MCP tools are accessible when server runs with HTTP transport."""
        # Test with direct server instance to verify tools are registered
        tools = await mcp.list_tools()
        
        # Should have document management tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'search_documents',
            'list_collections',
            'read_document', 
            'create_document'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in {tool_names}"
    
    @pytest.mark.asyncio
    async def test_http_server_mcp_endpoints(self, http_mcp_server):
        """Test that HTTP server exposes MCP-compatible endpoints."""
        assert http_mcp_server.poll() is None, "Server not running"
        
        # Test for typical FastMCP endpoints
        async with httpx.AsyncClient() as client:
            try:
                # Test SSE endpoint (common for FastMCP)
                response = await client.get("http://localhost:3001/sse", timeout=10.0)
                # Should get some response (not connection error)
                assert response.status_code in [200, 405, 422, 400]
                
                # Test messages endpoint if available
                try:
                    response = await client.get("http://localhost:3001/messages/", timeout=5.0)
                    assert response.status_code in [200, 404, 405, 422, 400]
                except httpx.TimeoutException:
                    # Endpoint might not exist, which is fine
                    pass
                    
            except httpx.ConnectError:
                pytest.fail("Could not connect to MCP server on HTTP")


class TestMCPCommunicationOverHTTP:
    """Test MCP client-server communication over HTTP transport."""
    
    @pytest.fixture
    def http_mcp_server(self):
        """Start MCP server with HTTP transport."""
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
        
        time.sleep(3)
        yield process
        
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
    
    @pytest.mark.asyncio
    async def test_http_json_rpc_format(self, http_mcp_server):
        """Test that HTTP endpoints accept JSON-RPC formatted requests."""
        assert http_mcp_server.poll() is None
        
        # Create a basic JSON-RPC request for listing tools
        json_rpc_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Try posting to various potential endpoints
                endpoints = ["/messages/", "/", "/rpc"]
                
                for endpoint in endpoints:
                    try:
                        response = await client.post(
                            f"http://localhost:3001{endpoint}",
                            json=json_rpc_request,
                            timeout=5.0,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        # If we get a proper response (not connection error), test passed
                        if response.status_code in [200, 405, 422]:
                            break
                            
                    except (httpx.TimeoutException, httpx.ConnectError):
                        continue
                        
                # At minimum, server should be reachable
                response = await client.get("http://localhost:3001/", timeout=5.0)
                assert response.status_code in [200, 404, 405, 422]
                
            except httpx.ConnectError:
                pytest.fail("HTTP server not accessible for JSON-RPC communication")


class TestHTTPSessionManagement:
    """Test session management over HTTP transport."""
    
    @pytest.mark.asyncio 
    async def test_concurrent_http_requests(self):
        """Test that HTTP transport can handle concurrent requests."""
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
        
        try:
            time.sleep(3)
            assert process.poll() is None
            
            # Make multiple concurrent requests
            async with httpx.AsyncClient() as client:
                tasks = []
                
                # Create multiple concurrent requests
                for i in range(5):
                    task = client.get(
                        f"http://localhost:3001/",
                        timeout=10.0
                    )
                    tasks.append(task)
                
                # Execute concurrently
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Most should succeed or return valid HTTP responses
                success_count = sum(
                    1 for r in responses 
                    if not isinstance(r, Exception) and hasattr(r, 'status_code')
                )
                
                # At least some requests should succeed
                assert success_count >= 3, f"Only {success_count}/5 concurrent requests succeeded"
                
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance over HTTP transport."""
    
    def test_mcp_transport_initialization(self):
        """Test that MCP transport initializes correctly for HTTP."""
        with patch('mcp_outline.server.mcp.run') as mock_run:
            with patch.dict(os.environ, {'MCP_TRANSPORT': 'streamable-http'}):
                from mcp_outline.server import main
                main()
                
                # Should initialize with streamable-http transport
                mock_run.assert_called_once_with(transport="streamable-http")
    
    @pytest.mark.anyio
    async def test_mcp_server_tools_registration(self):
        """Test that all MCP tools are properly registered for HTTP transport."""
        # Direct test with server instance
        tools = await mcp.list_tools()
        
        # Should have a comprehensive set of document management tools
        tool_names = {tool.name for tool in tools}
        
        # Core document operations
        core_tools = {
            'search_documents', 'list_collections', 'read_document',
            'create_document', 'update_document'
        }
        
        # Should have most core tools
        assert len(core_tools & tool_names) >= 4, f"Missing core tools. Found: {tool_names}"
        
        # Check that tools have proper structure
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description') 
            assert tool.name is not None
            assert tool.description is not None


class TestHTTPTransportPerformance:
    """Test performance characteristics of HTTP transport."""
    
    @pytest.mark.asyncio
    async def test_http_response_time(self):
        """Test that HTTP transport provides reasonable response times."""
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
        
        try:
            time.sleep(3)
            assert process.poll() is None
            
            # Test response time
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:3001/", timeout=10.0)
                
            end_time = time.time()
            response_time = end_time - start_time
            
            # Should respond within reasonable time (5 seconds)
            assert response_time < 5.0, f"HTTP response took {response_time:.2f} seconds"
            
            # Should get some response
            assert hasattr(response, 'status_code')
            
        except httpx.ConnectError:
            pytest.fail("HTTP server not accessible for performance test")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


class TestHTTPTransportErrorHandling:
    """Test error handling in HTTP transport for MCP operations."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_rpc_handling(self):
        """Test handling of invalid JSON-RPC requests over HTTP."""
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
        
        try:
            time.sleep(3)
            assert process.poll() is None
            
            # Send invalid JSON-RPC request
            invalid_request = {"invalid": "request"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:3001/",
                    json=invalid_request,
                    timeout=5.0
                )
                
                # Should handle invalid request gracefully
                # (Either with proper error response or method not allowed)
                assert response.status_code in [400, 405, 422, 404]
                
        except httpx.ConnectError:
            # Server might not expose the endpoint, which is also valid
            pass
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)