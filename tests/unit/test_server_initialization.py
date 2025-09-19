"""
Unit tests for server initialization with different transport modes.

Tests the FastMCP server initialization logic including:
- Server instance creation
- Port configuration
- Feature registration
- Transport mode handling
"""
import pytest
from unittest.mock import patch, MagicMock

from mcp_outline.server import mcp
from mcp_outline import server


class TestFastMCPServerInitialization:
    """Test FastMCP server instance creation and configuration."""
    
    def test_server_instance_creation(self):
        """Test that FastMCP server is created with correct name and port."""
        assert mcp.name == "Document Outline"
        # FastMCP port configuration is in settings
        assert hasattr(mcp, 'settings')
        assert hasattr(mcp.settings, 'port')
    
    def test_server_port_configuration(self):
        """Test server is configured with port 3001."""
        # The server should be configured for port 3001
        assert mcp.settings.port == 3001
    
    @pytest.mark.anyio
    async def test_feature_registration(self):
        """Test that features are registered with the server."""
        # Verify tools are registered (should be > 0 after register_all)
        tools = await mcp.list_tools()
        assert len(tools) > 0
        
        # Verify we have expected document management tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'search_documents',
            'list_collections', 
            'read_document',
            'create_document'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_register_all_import(self):
        """Test that register_all can be imported and called."""
        from mcp_outline.features import register_all
        
        # Should not raise an exception
        mock_mcp = MagicMock()
        register_all(mock_mcp)
        
        # Should have called methods on the mock MCP instance
        assert mock_mcp.tool.call_count > 0


class TestServerModuleStructure:
    """Test server module structure and imports."""
    
    def test_required_imports(self):
        """Test that all required modules can be imported."""
        # These should not raise ImportError
        import logging
        import os
        from typing import Literal, cast
        from mcp.server.fastmcp import FastMCP
        from mcp_outline.features import register_all
        
        # Verify types exist
        assert Literal is not None
        assert cast is not None
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from mcp_outline.server import main
        assert callable(main)
    
    def test_module_level_server_instance(self):
        """Test that server instance is created at module level."""
        from mcp_outline.server import mcp as server_mcp
        
        # Should be the same instance
        assert server_mcp is mcp
        assert server_mcp.name == "Document Outline"


class TestTransportModeHandling:
    """Test how different transport modes are handled during initialization."""
    
    def test_valid_transports_list(self):
        """Test the valid transports list contains expected values."""
        # We need to inspect the source or mock to test this
        with patch('mcp_outline.server.os.getenv', return_value='invalid'), \
             patch('mcp_outline.server.mcp.run'), \
             patch('mcp_outline.server.logging') as mock_logging:
            
            server.main()
            
            # Error message should contain the valid transports
            error_call = mock_logging.error.call_args[0][0]
            assert "['stdio', 'sse', 'streamable-http']" in error_call
    
    def test_transport_type_casting(self):
        """Test that transport mode is properly type cast."""
        # This is mainly for type safety - verify the cast function works
        from typing import cast, Literal
        
        transport = cast(Literal['stdio', 'sse', 'streamable-http'], 'stdio')
        assert transport == 'stdio'
        
        transport = cast(Literal['stdio', 'sse', 'streamable-http'], 'sse')
        assert transport == 'sse'


class TestServerStartupFlow:
    """Test the complete server startup flow."""
    
    def test_startup_flow_stdio(self):
        """Test complete startup flow for stdio transport."""
        with patch.dict('os.environ', {'MCP_TRANSPORT': 'stdio'}), \
             patch('mcp_outline.server.mcp.run') as mock_run, \
             patch('mcp_outline.server.logging') as mock_logging:
            
            server.main()
            
            # Verify logging sequence
            info_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert "Starting MCP Outline server with transport mode: stdio" in info_calls
            
            # Verify server start
            mock_run.assert_called_once_with(transport="stdio")
    
    def test_startup_flow_sse(self):
        """Test complete startup flow for sse transport."""
        with patch.dict('os.environ', {'MCP_TRANSPORT': 'sse'}), \
             patch('mcp_outline.server.mcp.run') as mock_run, \
             patch('mcp_outline.server.logging') as mock_logging:
            
            server.main()
            
            # Verify logging
            info_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert "Starting MCP Outline server with transport mode: sse" in info_calls
            
            # Verify server start
            mock_run.assert_called_once_with(transport="sse")
    
    def test_startup_flow_streamable_http(self):
        """Test complete startup flow for streamable-http transport."""
        with patch.dict('os.environ', {'MCP_TRANSPORT': 'streamable-http'}), \
             patch('mcp_outline.server.mcp.run') as mock_run, \
             patch('mcp_outline.server.logging') as mock_logging:
            
            server.main()
            
            # Verify logging sequence
            info_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert "Starting MCP Outline server with transport mode: streamable-http" in info_calls
            assert "HTTP server will start on default configuration" in info_calls
            
            # Verify server start
            mock_run.assert_called_once_with(transport="streamable-http")
    
    def test_startup_flow_error_handling(self):
        """Test startup flow with invalid transport mode."""
        with patch.dict('os.environ', {'MCP_TRANSPORT': 'invalid'}), \
             patch('mcp_outline.server.mcp.run') as mock_run, \
             patch('mcp_outline.server.logging') as mock_logging:
            
            server.main()
            
            # Verify error logging
            mock_logging.error.assert_called_once()
            error_msg = mock_logging.error.call_args[0][0]
            assert "Invalid transport mode: invalid" in error_msg
            
            # Should still log startup with fallback
            info_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert "Starting MCP Outline server with transport mode: stdio" in info_calls
            
            # Should start with stdio fallback
            mock_run.assert_called_once_with(transport="stdio")


class TestServerConfiguration:
    """Test server configuration and setup."""
    
    def test_server_name_configuration(self):
        """Test server is configured with correct name."""
        assert mcp.name == "Document Outline"
    
    def test_server_port_configuration_value(self):
        """Test server port is set to 3001."""
        assert mcp.settings.port == 3001
    
    @pytest.mark.anyio
    async def test_tools_registration_count(self):
        """Test that a reasonable number of tools are registered."""
        tools = await mcp.list_tools()
        
        # Should have at least 10 tools based on the feature set
        assert len(tools) >= 10
        
        # Should not have an excessive number (sanity check)
        assert len(tools) <= 50