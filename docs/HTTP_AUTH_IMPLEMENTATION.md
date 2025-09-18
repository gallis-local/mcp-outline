# HTTP Transport and Authentication Implementation

## Overview

This implementation adds HTTP transport support to the MCP Outline server with API key authentication via HTTP headers. This enables the server to run as a web service and accept API keys through HTTP headers instead of just environment variables.

## Features Implemented

### 1. HTTP Transport Support
- **Transport Mapping**: `MCP_TRANSPORT=http` maps to `streamable-http` transport
- **Port Configuration**: Server runs on port 3001 by default (FastMCP default)
- **Backward Compatibility**: Maintains support for `stdio` and `sse` transports

### 2. HTTP Header Authentication
- **Multiple Header Formats**:
  - `Authorization: Bearer <token>`
  - `X-Outline-API-Key: <token>`
  - `Outline-API-Key: <token>`
- **Fallback Chain**: Headers → Environment variables
- **Context-Aware**: Uses MCP context to access HTTP request headers

### 3. Enhanced Client Factory
- **Dual Methods**:
  - `get_outline_client()`: Standard method (env vars only)
  - `get_outline_client_from_context(context)`: Context-aware method (headers + env vars)
- **Automatic Fallback**: Headers not available → environment variables

## Usage Examples

### Server Startup
```bash
# Start server with HTTP transport
export MCP_TRANSPORT=http
export OUTLINE_API_KEY=fallback_key  # Optional fallback
python src/mcp_outline/server.py
```

### Client Authentication
```bash
# Using curl with Bearer token
curl -X POST http://127.0.0.1:3001/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-outline-api-key" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"test_auth_context","arguments":{}}}'

# Using custom header
curl -X POST http://127.0.0.1:3001/messages \
  -H "Content-Type: application/json" \
  -H "X-Outline-API-Key: your-outline-api-key" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"test_auth_context","arguments":{}}}'
```

### Python Client Example
```python
import httpx
import asyncio

async def call_mcp_tool():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:3001/messages",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer your-outline-api-key"
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "search_documents",
                    "arguments": {"query": "project plan"}
                }
            }
        )
        return response.json()
```

## Development Patterns

### Adding New Tools with Auth Support
```python
@mcp.tool()
def my_new_tool(query: str) -> str:
    """My new tool with HTTP auth support."""
    try:
        # Use context-aware client for HTTP header auth
        context = mcp.get_context()
        client = get_outline_client_from_context(context)
        
        # Use the client normally
        results = client.search_documents(query)
        return format_results(results)
        
    except OutlineClientError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"
```

### Environment Variable Fallback
```python
# Priority order:
# 1. Explicit parameter: get_outline_client(api_key="explicit_key")
# 2. HTTP header: get_outline_client_from_context(context)
# 3. Environment variable: OUTLINE_API_KEY
```

## Testing

### Test Authentication
Use the built-in test tool:
```bash
# Start server
export MCP_TRANSPORT=http
python src/mcp_outline/server.py

# Test with headers (separate terminal)
python test_http_auth.py
```

### Smoke Test
```bash
# Test all tools are available
python test_mcp.py
```

## Architecture Benefits

1. **Flexibility**: Supports both environment variables and HTTP headers
2. **Security**: API keys can be passed per-request instead of stored in environment
3. **Multi-tenant**: Different clients can use different API keys in the same server instance
4. **Backward Compatible**: Existing env var setup continues to work
5. **Transport Agnostic**: Tools work the same way regardless of transport mode

## Files Modified

- `src/mcp_outline/server.py`: Added HTTP transport support
- `src/mcp_outline/features/documents/common.py`: Added context-aware client factory
- `src/mcp_outline/features/documents/document_search.py`: Added test tool
- `.github/copilot-instructions.md`: Updated documentation
- `test_http_auth.py`: HTTP authentication test script (new)

## Future Enhancements

1. **Middleware**: Add authentication middleware for request validation
2. **Rate Limiting**: Per-API-key rate limiting
3. **Logging**: Enhanced logging with API key context (masked)
4. **Health Checks**: Authentication status endpoints
5. **Documentation**: OpenAPI/Swagger documentation for HTTP API