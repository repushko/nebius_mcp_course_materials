You are working on an MCP (Model Context Protocol) server called "git-activity-analyzer" that lets a coding agent query Git repository data (history, hotspots, CI, ownership) as structured resources and tools.

The project already has a `pyproject.toml` with dependencies (`gitpython`, `mcp`). You need to build the full server from scratch.

Do the following:

1. **Create `docs/interface.md`** with:
   - 5-8 host questions the server should answer (e.g. "Which files are risky to change?", "What's the ownership schema?", "What changed most in the last 30 days?", "Who are the top contributors?", "Are there any commit pattern anomalies?", "What is the team structure?", "What is the CI/CD build health?", "What are the recent deployments?")
   - Under each question, list the minimum data needed to answer it
   - List all data sources (git log, file history, author contributions, CI/CD, team structure, ownership, deployments)
   - Create a mapping table of capabilities to MCP primitives: at least 3 Resources, 2 Tools, 1 Prompt

2. **Create the server code:**
   - `app.py` — initialize FastMCP server: `server = FastMCP("git-activity-analyzer")`
   - `server.py` — entry point supporting both stdio and SSE (`--sse`) transports. Log to stderr. Import `tools` module to register handlers. For SSE mode, use uvicorn on port 8000.
   - `git_utils.py` — a `GitRepository` adapter class wrapping GitPython. Methods: `get_commits(days)`, `get_changed_files(commit)`, `get_authors(days)`
   - `analysis.py` — analysis functions: `analyze_hotspots(repo, days, top_n, author_filter)` returning ranked list of files by risk score (changes * unique authors), `analyze_commit_patterns(repo, days, author)`, `get_repository_summary(repo)`
   - `mock_git_utils.py` — mock data constants: `MOCK_REPO_SUMMARY`, `MOCK_TEAMS`, `MOCK_CODEOWNERS`
   - `tools.py` — register MCP resources, tools, and prompts:
     - 3 Resources: `git-activity://summary/{repo_path}`, `git-activity://teams/backend`, `git-activity://ownership/CODEOWNERS` (return mock data)
     - 2 Tools: `analyze_hotspots(repo_path, days=30, author_filter=None)` and `analyze_commit_patterns(repo_path, days=30, author=None)` — validate repo_path exists and is a git repo, raise McpError with INVALID_PARAMS/INTERNAL_ERROR as appropriate, return JSON as TextContent
     - 1 Prompt: `repo_health_review(repo_path)` — guided workflow referencing the tools

3. **Add security:**
   - `config/allowed_repos.json` — list of allowed repository paths
   - `security.py` — `validate_repo_path(path)` function that checks path is inside allowed dirs and blocks `../` traversal
   - Add API key middleware for SSE transport (or a documented TODO)

4. **Add tests** in `tests/`:
   - `conftest.py` with a `temp_repo` fixture (temporary git repo with 3 commits)
   - `test_analysis.py` — test `get_repository_summary` and `analyze_hotspots` ranking
   - `test_tools.py` — test error handling for invalid repo paths

5. **Update `pyproject.toml`** — add any missing dependencies (httpx, uvicorn) and pytest config with `pythonpath = ["."]`

Make sure `uv run pytest` passes.
