# Validating MCP Servers

In this task, you'll validate an MCP server, then confirm end-to-end behavior in an AI coding agent.

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

### Step 1: Smoke test with MCP Inspector

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

### Step 2: Test Tool A — `analyze_hotspots`

- Run it with parameters (example: `days: 30`, `top_n: 5`).
- Verify the output makes sense:
  - file paths look real
  - risk/commit counts look plausible
  - results are ranked by risk score

### Step 3: Test Tool B — `get_build_history`

- Run it with no arguments first, then try filtering by `status` and `branch`.
- Verify the output makes sense:
  - When filtering by `status: "failed"`, only failed builds should appear
  - `total_builds` should reflect the total count before pagination (not after filtering)
  - Results should not be mutated between calls

### Step 4: Fix any bugs you find

- If a tool returns unexpected results, investigate and fix the code.
- Run the test suite to confirm your fixes:
  ```bash
  uv run pytest
  ```

### Step 5 (Optional): Test in a coding agent

1. Add the MCP server to Claude Code/Cursor config (use the same stdio command as in Inspector).
2. Ask: "What are the hotspot files in this repo?"
3. Confirm the agent calls `analyze_hotspots` and produces a useful answer based on tool output.

## Submission Checklist

- [ ] MCP Inspector connected (green) with tools list visible
- [ ] `analyze_hotspots` returns correct ranked results
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
