# Lesson 4: Debugging MCP Server Tools

In this task, you'll debug a broken MCP server tool that returns valid JSON but wrong data.

## Preparation

1. Confirm that `mcp-debugging-practice` appears in your account. Alternatively, download it here.
2. Clone the repo locally and open it in your editor.
3. Run baseline tests once (they should fail):

```bash
uv run python -m pytest tests/ -v
```

## Reproduce the bug in MCP Inspector

1. Start MCP Inspector:

```bash
npx -y @modelcontextprotocol/inspector
```

2. Connect to the server via stdio using the command from the README.
3. Call `get_build_history` with:
   - `status: "failed"`
4. Confirm the results are wrong — the tool returns successful builds instead of failed ones.

## Fix the tool

Fix all three issues in `get_build_history`:

- **Inverted filter** (`!=` should be `==`) — the status filter excludes matching builds instead of keeping them
- **Wrong `total_builds`** — must reflect the full dataset size, not the filtered list length
- **Missing list copy** (`builds = list(BUILDS)`) — without copying, the module-level list could be mutated

## Verify

1. Run `pytest` until all tests pass:

```bash
uv run python -m pytest tests/ -v
```

2. Reconnect to MCP Inspector and call:
   - `get_build_history` with `status: "failed"` — returns only failed builds
   - `get_build_history` with no filters — `total_builds` matches the full dataset (10)

## Submission checklist

- [ ] All three bugs in `get_build_history` are fixed
- [ ] `pytest` passes with no failures
- [ ] MCP Inspector confirms correct filtering behavior
