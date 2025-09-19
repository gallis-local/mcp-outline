"""
Unit tests for transport mode selection and validation logic.

Tests the streamable HTTP functionality implementation including:
- Transport mode validation 
- Environment variable parsing
- HTTP compatibility mapping
- Error handling for invalid transport modes
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from mcp_outline.server import main


class TestTransportModeValidation:
    """Test transport mode validation logic."""
    
    def test_default_transport_mode_stdio(self):
        """Test that default transport mode is stdio when MCP_TRANSPORT not set."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="stdio")
    
    def test_valid_transport_mode_stdio(self):
        """Test stdio transport mode is accepted."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'stdio'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="stdio")
    
    def test_valid_transport_mode_sse(self):
        """Test sse transport mode is accepted."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'sse'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="sse")
    
    def test_valid_transport_mode_streamable_http(self):
        """Test streamable-http transport mode is accepted."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'streamable-http'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="streamable-http")
    
    def test_http_compatibility_mapping(self):
        """Test that 'http' maps to 'streamable-http' for compatibility."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'http'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="streamable-http")
    
    def test_case_insensitive_transport_mode(self):
        """Test transport mode is case insensitive."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'SSE'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="sse")
        
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'STREAMABLE-HTTP'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="streamable-http")
    
    def test_invalid_transport_mode_fallback(self):
        """Test invalid transport mode falls back to stdio."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'invalid'}), \
             patch('mcp_outline.server.mcp.run') as mock_run, \
             patch('mcp_outline.server.logging') as mock_logging:
            
            main()
            
            # Should log error and fallback to stdio
            mock_logging.error.assert_called_once()
            error_call_args = mock_logging.error.call_args[0][0]
            assert "Invalid transport mode: invalid" in error_call_args
            assert "Must be one of: ['stdio', 'sse', 'streamable-http']" in error_call_args
            
            mock_run.assert_called_once_with(transport="stdio")
    
    def test_empty_transport_mode_fallback(self):
        """Test empty transport mode falls back to stdio."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': ''}), \
             patch('mcp_outline.server.mcp.run') as mock_run, \
             patch('mcp_outline.server.logging') as mock_logging:
            
            main()
            
            # Empty string should be invalid and fallback to stdio
            mock_logging.error.assert_called_once()
            mock_run.assert_called_once_with(transport="stdio")


class TestTransportLogging:
    """Test logging behavior for different transport modes."""
    
    def test_transport_mode_logging(self):
        """Test that transport mode selection is logged."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'streamable-http'}), \
             patch('mcp_outline.server.mcp.run'), \
             patch('mcp_outline.server.logging') as mock_logging:
            
            main()
            
            # Should log the selected transport mode
            log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert "Starting MCP Outline server with transport mode: streamable-http" in log_calls
    
    def test_http_transport_specific_logging(self):
        """Test specific logging for HTTP transport mode."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'streamable-http'}), \
             patch('mcp_outline.server.mcp.run'), \
             patch('mcp_outline.server.logging') as mock_logging:
            
            main()
            
            # Should have specific log message for HTTP transport
            log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert any("HTTP server will start on default configuration" in msg for msg in log_calls)
    
    def test_compatibility_mapping_logging(self):
        """Test logging when http maps to streamable-http."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'http'}), \
             patch('mcp_outline.server.mcp.run'), \
             patch('mcp_outline.server.logging') as mock_logging:
            
            main()
            
            # Should log the mapped transport mode, not the original
            log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            assert "Starting MCP Outline server with transport mode: streamable-http" in log_calls


class TestEnvironmentVariableParsing:
    """Test environment variable parsing behavior."""
    
    @pytest.mark.parametrize("transport_value,expected_transport", [
        ("stdio", "stdio"),
        ("sse", "sse"), 
        ("streamable-http", "streamable-http"),
        ("http", "streamable-http"),  # compatibility mapping
        ("STDIO", "stdio"),  # case insensitive
        ("Http", "streamable-http"),  # case insensitive + mapping
    ])
    def test_environment_variable_parsing(self, transport_value, expected_transport):
        """Test various environment variable values are parsed correctly."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': transport_value}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport=expected_transport)
    
    def test_missing_environment_variable(self):
        """Test behavior when MCP_TRANSPORT environment variable is missing."""
        # Ensure MCP_TRANSPORT is not set
        with patch.dict(os.environ, {}, clear=True), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            mock_run.assert_called_once_with(transport="stdio")


class TestServerInitializationBranching:
    """Test the different code paths for server initialization."""
    
    def test_streamable_http_initialization_path(self):
        """Test that streamable-http uses the correct initialization path."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'streamable-http'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            
            # Should call run with streamable-http transport
            mock_run.assert_called_once_with(transport="streamable-http")
    
    def test_sse_initialization_path(self):
        """Test that sse uses the correct initialization path.""" 
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'sse'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            
            # Should call run with sse transport
            mock_run.assert_called_once_with(transport="sse")
    
    def test_stdio_initialization_path(self):
        """Test that stdio uses the correct initialization path."""
        with patch.dict(os.environ, {'MCP_TRANSPORT': 'stdio'}), \
             patch('mcp_outline.server.mcp.run') as mock_run:
            
            main()
            
            # Should call run with stdio transport
            mock_run.assert_called_once_with(transport="stdio")