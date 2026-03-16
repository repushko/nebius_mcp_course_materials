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

## Task Steps

### Step 1: Run baseline tests

Run the test suite — some tests should fail:

```bash
uv run python -m pytest tests/ -v
```

### Step 2: Smoke test with MCP Inspector

1. Start MCP Inspector:
   ```bash
   npx -y @modelcontextprotocol/inspector
   ```
2. In the Inspector UI, connect to the server via stdio:
   ```bash
   uv run python server.py
   ```
3. Confirm:
   - Status shows Connected (green)
   - Tools list is populated

### Step 3: Test Tool A — `analyze_hotspots`

- Run it with parameters (example: `days: 30`, `top_n: 5`).
- Verify the output makes sense:
  - file paths look real
  - risk/commit counts look plausible
  - results are ranked by risk score

### Step 4: Test Tool B — `get_build_history`

- Run it with no arguments first, then try filtering by `status` and `branch`.
- Observe the bugs:
  - When filtering by `status: "failed"`, the tool returns successful builds instead of failed ones
  - `total_builds` reflects the filtered count instead of the full dataset size
  - The module-level `BUILDS` list could be mutated between calls

### Step 5: Fix the bugs

Fix all three issues in `get_build_history` inside `tools.py`:

- **Inverted filter** (`!=` should be `==`) — the status filter excludes matching builds instead of keeping them
- **Wrong `total_builds`** — must reflect the full dataset size, not the filtered list length
- **Missing list copy** (`builds = list(BUILDS)`) — without copying, the module-level list could be mutated

### Step 6: Verify your fixes

1. Run `pytest` until all tests pass:

```bash
uv run python -m pytest tests/ -v
```

2. Reconnect to MCP Inspector and call:
   - `get_build_history` with `status: "failed"` — returns only failed builds
   - `get_build_history` with no filters — `total_builds` matches the full dataset (10)

### Step 7 (Optional): Test in a coding agent

1. Add the MCP server to Claude Code/Cursor config (use the same stdio command as in Inspector).
2. Ask: "What are the hotspot files in this repo?"
3. Confirm the agent calls `analyze_hotspots` and produces a useful answer based on tool output.

## Submission Checklist

- [ ] MCP Inspector connected (green) with tools list visible
- [ ] `analyze_hotspots` returns correct ranked results
- [ ] All three bugs in `get_build_history` are fixed
- [ ] `get_build_history` filters by status correctly
- [ ] `get_build_history` reports correct total count
- [ ] `get_build_history` doesn't mutate shared data between calls
- [ ] `pytest` runs green

## Running the Server

```bash
uv run python server.py
```

## Running Tests

```bash
uv run pytest
```
