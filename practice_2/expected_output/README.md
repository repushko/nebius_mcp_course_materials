# MCP Hotspots Handler: Thin Handler + Structured Errors

In this task, you'll turn a real repo-analysis task into a production-ready MCP tool.

You'll implement `analyze_hotspots` as a thin handler and make it fail cleanly with structured errors.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
uv sync
```

## Key Files

- `server.py` — server setup + wiring
- `tools.py` — tool registration via `@server.tool()` (you'll implement here)
- `git_utils.py` — GitRepository adapter (data access layer)
- `analysis.py` — risk scoring + ranking (analysis layer)
- `mock_git_utils.py` — mock data for testing without a real repo

## Task Steps

### Step 1: Implement `analyze_hotspots` as a thin handler

Implement the MCP tool handler `analyze_hotspots` in `tools.py`.

Requirements:

- Register it with `@server.tool()`
- It must be `async`
- Parameters:
  - `repo_path: str`
  - `days: int = 30`
  - `limit: int = 10`

Inside the handler:

1. Instantiate the adapter: `repo = GitRepository(repo_path)`
2. Delegate to analysis: `results = analysis.analyze_hotspots(repo, days=days, limit=limit)`
3. Return structured JSON as MCP `TextContent`.

### Step 2: Add structured error handling

Your handler must fail cleanly with MCP structured errors.

#### Input validation errors -> InvalidParams

Validate business rules (not types):

- If `repo_path` does not exist -> raise `McpError` with `INVALID_PARAMS`
- If `repo_path` exists but is not a git repo (no `.git`) -> raise `McpError` with `INVALID_PARAMS`

#### Runtime errors -> InternalError

Wrap the analysis call:

- If analysis raises a git operation error -> raise `McpError` with `INTERNAL_ERROR`
- If analysis raises any other exception -> raise `McpError` with `INTERNAL_ERROR` and message like "Analysis failed"

### Step 3: Run tests and fix until green

```bash
uv run pytest
```

## Submission Checklist

- [x] `analyze_hotspots` is registered with `@server.tool()`
- [x] Handler is async and has correct defaults (`days=30`, `limit=10`)
- [x] Handler is a thin wrapper (delegates to `git_utils` + `analysis` layers)
- [x] `InvalidParams` errors for non-existent repo and non-git folders
- [x] `InternalError` errors for analysis/runtime failures
- [x] Output is valid JSON with a ranked list
- [x] `pytest` runs green

## Running the Server

```bash
uv run python server.py
```

## Running Tests

```bash
uv run pytest
```
