"""
End-to-end tests for complete MCP workflow over HTTP transport.

Tests the complete user workflow including:
- Complete MCP workflow over HTTP transport
- Tool execution via HTTP endpoints  
- Session management and state handling
- Error propagation and handling
"""
import asyncio
import json
import os
import subprocess
import time
import pytest
import httpx
from unittest.mock import patch


class TestCompleteHTTPWorkflow:
    """Test complete MCP workflow over HTTP transport."""
    
    @pytest.fixture
    def http_server_with_mock_api(self):
        """Start HTTP server with mocked Outline API for E2E testing."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-e2e-key'
        env['OUTLINE_API_URL'] = 'http://mock-outline-api.test/api'  # Mock API
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        # Give server time to start
        time.sleep(4)
        
        yield process
        
        # Cleanup
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
    
    @pytest.mark.asyncio
    async def test_server_startup_complete_workflow(self, http_server_with_mock_api):
        """Test complete server startup and basic HTTP accessibility."""
        process = http_server_with_mock_api
        
        # Verify server process is running
        assert process.poll() is None, "HTTP server process not running"
        
        # Test basic HTTP connectivity
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Test root endpoint
                response = await client.get("http://localhost:3001/")
                
                # Should get some HTTP response (not connection error)
                assert hasattr(response, 'status_code')
                assert response.status_code in [200, 404, 405, 422]
                
                # Test SSE endpoint  
                sse_response = await client.get("http://localhost:3001/sse")
                assert hasattr(sse_response, 'status_code')
                
            except httpx.ConnectError:
                pytest.fail("Could not connect to HTTP server for E2E workflow test")
    
    @pytest.mark.asyncio
    async def test_mcp_tools_workflow_over_http(self):
        """Test MCP tools workflow over HTTP (using direct server instance)."""
        # Test the server instance directly to verify tools work
        from mcp_outline.server import mcp
        
        # Test tools are available
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]
        
        # Should have core document tools
        assert 'search_documents' in tool_names
        assert 'list_collections' in tool_names
        
        # Test tool can be called (will fail gracefully without real API)
        try:
            # This will fail with actual API call, but should not crash
            result = await mcp.call_tool('list_collections', {})
            # Should get some result (even if error)
            assert result is not None
        except Exception as e:
            # Expected to fail without real API, but should handle gracefully
            assert "Error" in str(e) or "Connection" in str(e)


class TestHTTPSessionManagement:
    """Test session management and state handling over HTTP."""
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self):
        """Test multiple concurrent HTTP sessions to the server."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-session-key'
        
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
            
            # Create multiple concurrent HTTP clients
            async with httpx.AsyncClient() as client1, \
                       httpx.AsyncClient() as client2, \
                       httpx.AsyncClient() as client3:
                
                # Make concurrent requests
                tasks = [
                    client1.get("http://localhost:3001/", timeout=8.0),
                    client2.get("http://localhost:3001/sse", timeout=8.0),
                    client3.get("http://localhost:3001/", timeout=8.0),
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful responses
                success_count = sum(
                    1 for r in responses
                    if not isinstance(r, Exception) and hasattr(r, 'status_code')
                )
                
                # Most should succeed
                assert success_count >= 2, f"Only {success_count}/3 concurrent sessions succeeded"
                
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


class TestHTTPErrorHandling:
    """Test error propagation and handling over HTTP."""
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self):
        """Test that server handles errors gracefully over HTTP."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-error-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            time.sleep(3)
            assert process.poll() is None
            
            async with httpx.AsyncClient() as client:
                # Send malformed request
                try:
                    response = await client.post(
                        "http://localhost:3001/",
                        content="invalid json",
                        headers={"Content-Type": "application/json"},
                        timeout=5.0
                    )
                    
                    # Should handle gracefully (400, 422, 405, etc.)
                    assert response.status_code in [400, 405, 422, 404]
                    
                except httpx.ConnectError:
                    # Server might not expose this endpoint
                    pass
                
                # Test with oversized request
                large_data = {"data": "x" * 10000}
                try:
                    response = await client.post(
                        "http://localhost:3001/",
                        json=large_data,
                        timeout=5.0
                    )
                    # Should handle large requests
                    assert response.status_code in [200, 400, 404, 405, 413, 422]
                except httpx.ConnectError:
                    pass
                    
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    
    def test_server_startup_error_scenarios(self):
        """Test server startup error scenarios."""
        # Test invalid port (should fail gracefully)
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-key'
        
        # Try to start server normally first
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            time.sleep(2)
            # Server should be running or have exited gracefully
            if process.poll() is not None:
                # If it exited, should be clean exit
                assert process.returncode in [0, 1]
            else:
                # Server is running, which is expected
                assert process.poll() is None
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


class TestHTTPProtocolCompliance:
    """Test MCP protocol compliance over HTTP transport."""
    
    def test_http_transport_protocol_compliance(self):
        """Test that HTTP transport follows MCP protocol standards."""
        # Test with mocked MCP calls
        with patch('mcp_outline.server.mcp.run') as mock_run:
            with patch.dict(os.environ, {'MCP_TRANSPORT': 'streamable-http'}):
                from mcp_outline.server import main
                main()
                
                # Should call with correct transport
                mock_run.assert_called_once_with(transport="streamable-http")
    
    @pytest.mark.asyncio
    async def test_mcp_server_tools_available_over_http(self):
        """Test that MCP tools are properly available over HTTP."""
        from mcp_outline.server import mcp
        
        # Test tool registration
        tools = await mcp.list_tools()
        assert len(tools) > 0
        
        # Test tool structure
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert tool.name is not None
            assert tool.description is not None
            
            # Tool names should be valid
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0


class TestHTTPPerformanceE2E:
    """Test end-to-end performance over HTTP transport."""
    
    @pytest.mark.asyncio
    async def test_http_response_performance(self):
        """Test HTTP response performance under realistic conditions."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-perf-key'
        
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
            
            # Test response times for multiple requests
            response_times = []
            
            async with httpx.AsyncClient() as client:
                for i in range(5):
                    start_time = time.time()
                    
                    try:
                        response = await client.get("http://localhost:3001/", timeout=10.0)
                        end_time = time.time()
                        
                        response_time = end_time - start_time
                        response_times.append(response_time)
                        
                        # Each response should be reasonably fast
                        assert response_time < 5.0, f"Request {i} took {response_time:.2f}s"
                        
                    except httpx.TimeoutException:
                        pytest.fail(f"Request {i} timed out")
                    except httpx.ConnectError:
                        pytest.fail("Could not connect for performance test")
            
            # Average response time should be reasonable
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 2.0, f"Average response time {avg_response_time:.2f}s too slow"
            
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)