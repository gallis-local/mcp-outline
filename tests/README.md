# MCP Outline Test Suite

Comprehensive test suite for the MCP Outline server, including full coverage for the streamable HTTP transport functionality.

## Test Structure

### Unit Tests (`tests/unit/`)
Tests individual components and functions in isolation:
- **`test_transport_selection.py`** - Transport mode validation, environment parsing, HTTP compatibility
- **`test_server_initialization.py`** - FastMCP server setup, configuration, feature registration

### Integration Tests (`tests/integration/`)  
Tests component interaction and HTTP transport integration:
- **`test_http_transport.py`** - HTTP server startup, endpoint availability, configuration
- **`test_mcp_over_http.py`** - MCP protocol over HTTP, tool accessibility, JSON-RPC communication

### End-to-End Tests (`tests/e2e/`)
Tests complete user workflows and system behavior:
- **`test_http_workflow.py`** - Complete MCP workflows over HTTP, session management, error handling
- **`test_performance.py`** - Performance benchmarks, response times, memory usage, concurrency

### Docker Tests (`tests/docker/`)
Tests containerized deployment scenarios:
- **`test_container_http.py`** - Docker builds, container startup, port binding, health checks
- **`docker-compose.test.yml`** - Multi-container test scenarios with different transport modes

### Existing Tests
- **`tests/features/`** - Feature-specific tests for document management tools
- **`tests/utils/`** - Utility and client tests
- **`test_server.py`** - Basic server functionality tests

## Running Tests

### All Tests
```bash
python -m pytest tests/
```

### By Category
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests  
python -m pytest tests/integration/

# End-to-end tests
python -m pytest tests/e2e/

# Docker tests (requires Docker)
python -m pytest tests/docker/

# Performance tests only
python -m pytest tests/ -m performance
```

### Specific Test Areas
```bash
# HTTP transport functionality
python -m pytest tests/unit/test_transport_selection.py tests/integration/test_http_transport.py

# Server initialization
python -m pytest tests/unit/test_server_initialization.py

# Complete HTTP workflow
python -m pytest tests/e2e/test_http_workflow.py
```

## Test Coverage

### Transport Modes Tested
- ✅ `stdio` (default) - Standard input/output transport
- ✅ `sse` - Server-Sent Events transport  
- ✅ `streamable-http` - HTTP transport for web integration
- ✅ `http` → `streamable-http` compatibility mapping

### Key Scenarios Covered
- ✅ Environment variable configuration (`MCP_TRANSPORT`)
- ✅ Transport mode validation and error handling
- ✅ Server startup and initialization
- ✅ HTTP endpoint availability and responsiveness
- ✅ MCP tool registration and execution
- ✅ Concurrent request handling
- ✅ Session management and state handling
- ✅ Performance benchmarks and resource usage
- ✅ Docker container deployment
- ✅ Error propagation and graceful handling

## Performance Benchmarks

Performance tests measure:
- **Response Time**: Average < 1000ms, Median < 500ms
- **Concurrency**: Handles 20+ concurrent requests
- **Memory Usage**: < 500MB under load
- **Connection Reuse**: HTTP keep-alive efficiency

## Docker Testing

Docker tests cover:
- Image building and container startup
- Environment variable configuration
- Port binding and network accessibility  
- Health checks and graceful shutdown
- Multi-container scenarios with Docker Compose

## Notes

- Docker tests require Docker to be available
- Performance tests are marked with `@pytest.mark.performance`
- Integration tests may start actual HTTP servers (brief startup time)
- All tests maintain backward compatibility with existing functionality

## Test Statistics

- **Total Test Methods**: 151+ (83 existing + 68 new)
- **New HTTP Tests**: 68 methods across 7 files
- **Coverage Areas**: Unit, Integration, E2E, Docker, Performance
- **Transport Modes**: Full coverage of stdio, sse, streamable-http