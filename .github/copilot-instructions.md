# Copilot instructions for mcp-outline

Use this as a quick-start guide to contribute productively with minimal context switching. Follow existing patterns, keep outputs readable, and validate with a fast smoke test.

## Big picture
- MCP server that exposes Outline (getoutline.com) features as MCP tools.
- Transports: `MCP_TRANSPORT=stdio` (default) or `sse` (HTTP/SSE on port 3001).
- Flow: `server.py` creates `FastMCP` → registers tools under `features/documents` → tools call Outline via `OutlineClient`.

## Key files
- `src/mcp_outline/server.py`: Entry. Reads `MCP_TRANSPORT`, sets port=3001, `mcp.run(...)`.
- `src/mcp_outline/features/__init__.py`: `register_all(mcp)` delegates to documents features.
- `src/mcp_outline/features/documents/*.py`: Tool modules; each has `register_tools(mcp)` and `@mcp.tool()` functions. See `document_search.py` for formatters and tool patterns.
- `src/mcp_outline/features/documents/common.py`: `get_outline_client()` (env → `OutlineClient`), wraps errors as `OutlineClientError`.
- `src/mcp_outline/utils/outline_client.py`: Thin HTTP client (`post`, `auth_info`, search/list/create/etc). Reads `OUTLINE_API_KEY`, optional `OUTLINE_API_URL`.
- Tests: `tests/**` (e.g., `tests/features/documents/test_document_search.py`).

## Conventions
- Tools return short, human-readable strings (often Markdown headings, IDs, brief context).
- Catch `OutlineClientError` in tools and return an informative message; catch generic `Exception` as fallback.
- Keep tools small; delegate formatting to `_format_*` helpers; delegate HTTP to `OutlineClient`.
- Style: PEP8-ish, 79-char lines, type hints, import order stdlib → third-party → local.
- Avoid noisy stdout/stderr in tools (server startup logs are fine).

## Dev workflow
- Install dev deps: `uv pip install -e ".[dev]"`
- Run server (stdio): `mcp dev src/mcp_outline/server.py` or `./start_server.sh` (loads `.env`).
- Run server (sse): `export MCP_TRANSPORT=sse; mcp-outline` → HTTP on `:3001` (`/sse`, `/messages/`).
- Docker: `sudo docker buildx build -t mcp-outline .` then use MCP Inspector with the built image.
- Tests: `uv sync --extra dev; uv run pytest -q`.
- Smoke test: `uv run python test_mcp.py` (spawns stdio server and lists tools).

## Extending
- New tool in existing module:
  1) Add `@mcp.tool()` function → get client via `get_outline_client()` → call `client.post(...)` or specific method.
  2) Format with a `_format_*` helper and return a concise string.
- New module:
  1) Create `src/mcp_outline/features/documents/my_feature.py` with `register_tools(mcp)`.
  2) Import and call it from `features/documents/__init__.py::register`.

## Integration assumptions
- `OUTLINE_API_KEY` is required. `OUTLINE_API_URL` defaults to `https://app.getoutline.com/api` (override for self-hosted).
- Use `stdio` for local CLI; `sse` for container/HTTP scenarios.

## Gotchas
- Keep responses skimmable (titles, IDs, minimal context) to help agents chain tools.
- Mirror existing error messages and formatting for consistency.
