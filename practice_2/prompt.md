You are working on an MCP server called "git-activity-analyzer". The server already has resources, a prompt template, and an `analyze_commit_patterns` tool implemented. Your task is to implement the `analyze_hotspots` tool handler in `tools.py`.

Open `tools.py` and find the TODO comment block. Implement the `analyze_hotspots` tool handler:

1. **Register it** with `@server.tool()` decorator
2. **Make it async** with signature: `async def analyze_hotspots(repo_path: str, days: int = 30, limit: int = 10) -> list[TextContent]`
3. **Validate inputs** — raise `McpError(ErrorData(code=INVALID_PARAMS, ...))` if:
   - `repo_path` does not exist (`os.path.isdir()`)
   - `repo_path` exists but is not a git repo (no `.git` subdirectory)
4. **Delegate to analysis layer:**
   - `repo = GitRepository(repo_path)`
   - `results = analysis.analyze_hotspots(repo, days=days, limit=limit)`
5. **Handle runtime errors** — wrap the analysis call in try/except:
   - `git.GitCommandError` -> raise `McpError(ErrorData(code=INTERNAL_ERROR, message=f"Git error: {e}"))`
   - Any other `Exception` -> raise `McpError(ErrorData(code=INTERNAL_ERROR, message="Analysis failed"))`
6. **Return result** as `[TextContent(type="text", text=json.dumps(results, indent=2))]`

You'll need to add these imports at the top of `tools.py`:
- `import os`
- `import git`
- `from mcp.shared.exceptions import McpError`
- `from mcp.types import INVALID_PARAMS, INTERNAL_ERROR, ErrorData`

Run `uv run pytest` and fix until all tests pass.
