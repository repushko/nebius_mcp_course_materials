You are working on an MCP server called "git-activity-analyzer". The server is already functional with tools like `analyze_hotspots` and `analyze_file_activity`. Your task is to validate it using MCP Inspector and confirm correct behavior.

Do the following:

1. **Smoke test with MCP Inspector:**
   - The server starts via `uv run python server.py` (stdio transport)
   - Confirm the Inspector shows "Connected" status and lists all tools

2. **Test `analyze_hotspots`:**
   - Run it with a real git repo path and parameters like `days: 30`, `top_n: 5`
   - Verify output has file paths, risk scores, and commit counts ranked by risk

3. **Test `get_build_history`:**
   - Run with no filters — should return all 10 builds
   - Run with `status: "failed"` — should return only failed builds
   - Verify `total_builds` reflects the full dataset size (10), not the filtered count

4. **Fix any bugs found** — run `uv run pytest` and fix until all tests pass

Note: This practice focuses on validation and testing workflow, not writing new code. The server code should already work correctly.
