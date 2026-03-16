You are working on an MCP server called "git-activity-analyzer". The `get_build_history` tool has three bugs. Your task is to find and fix them.

1. **Run baseline tests** — `uv run python -m pytest tests/ -v`. Observe the failures.

2. **Open `tools.py`** and find the `get_build_history` function. Fix these three bugs:

   - **Inverted status filter:** Line with `b["status"] != status` should be `b["status"] == status` — currently it excludes matching builds instead of keeping them.
   - **Wrong `total_builds` calculation:** `total = len(builds)` is computed after filtering. It should reflect the full dataset size before any filters. Add `total = len(builds)` right after `builds = list(BUILDS)`, before the filter conditions.
   - **Missing list copy:** `builds = BUILDS` directly references the module-level list. Change to `builds = list(BUILDS)` so filtering doesn't mutate the shared data.

3. **Run tests again** — `uv run python -m pytest tests/ -v` — all tests should now pass.
