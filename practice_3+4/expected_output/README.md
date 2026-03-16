# Validating & Debugging MCP Server Tools

In this task, you'll validate an MCP server using MCP Inspector, discover bugs by testing tool behavior, and fix the broken code.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js (for MCP Inspector)

## Setup

```bash
uv sync
```

## Key Files

- `server.py` — server entry point (stdio + SSE transports)
- `app.py` — FastMCP server initialization
- `tools.py` — tool handlers (`analyze_hotspots`, `analyze_file_activity`, `get_build_history`, etc.)
- `analysis.py` — core analysis functions
- `git_utils.py` — GitRepository adapter
- `tests/` — existing test suite

## Submission Checklist

- [x] MCP Inspector connected (green) with tools list visible
- [x] `analyze_hotspots` returns correct ranked results
- [x] All three bugs in `get_build_history` are fixed
- [x] `get_build_history` filters by status correctly
- [x] `get_build_history` reports correct total count
- [x] `get_build_history` doesn't mutate shared data between calls
- [x] `pytest` runs green

## Running the Server

```bash
uv run python server.py
```

## Running Tests

```bash
uv run pytest
```
