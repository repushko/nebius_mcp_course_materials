You are working on an MCP server called "git-activity-analyzer". The server has several tools implemented, but `get_build_history` has three bugs that need to be found and fixed.

Do the following:

1. **Run baseline tests** — `uv run python -m pytest tests/ -v`. Some tests should fail.

2. **Find and fix the three bugs in `get_build_history`** in `tools.py`:
   - **Bug 1 — Inverted status filter:** The status filter uses `!=` instead of `==`, which excludes matching builds instead of keeping them. Change `b["status"] != status` to `b["status"] == status`.
   - **Bug 2 — Wrong `total_builds`:** The `total` is computed after filtering (`total = len(builds)`), but it should reflect the full dataset size. Move `total = len(builds)` to before the filtering, or better yet, use `total = len(BUILDS)` directly after making a copy.
   - **Bug 3 — Missing list copy:** The code assigns `builds = BUILDS` which means filtering mutates the module-level list. Change to `builds = list(BUILDS)` to work on a copy.

3. **Verify fixes:**
   - Run `uv run python -m pytest tests/ -v` — all tests should pass
   - In MCP Inspector, `get_build_history` with `status: "failed"` should return only failed builds
   - `total_builds` should always be 10 regardless of filters
