# Designing an MCP Interface: Git Activity Analyzer

In this task, you'll design an MCP interface for a Git Activity Analyzer server so a coding agent can query repo facts (history, hotspots, CI, ownership) as structured resources and tools instead of pasting context manually.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- A local Git repository to analyze (or use any public repo)

## Setup

```bash
uv sync
```

## Task Steps

### 1. Start from host questions

1. Create (or open) `docs/interface.md`.
2. Add 5-8 questions the server should be able to answer.
   - Examples:
     - Which files are risky to change?
     - What's the ownership schema of repositories?
     - What changed most in the last 30 days?
3. Under each question, write the minimum data it needs.

### 2. Identify data sources

In `docs/interface.md`, list the data sources your server will expose. Include these categories:

> Some sources may come from `.git` (GitPython or equivalent). Others may come from external APIs (GitHub Actions, GitLab CI, internal dashboards). Feel free to use placeholders for this task.

- Git commit log (authors, timestamps, messages, diffs)
- File change history (which files change most frequently)
- Author contributions (lines added/deleted, files touched)
- CI/CD build history (runs, stages, pass/fail)
- Team structure (members, roles)
- Repository ownership (code owners, review policies)
- Deployment history (environments, version, timestamp)

### 3. Map capabilities to MCP primitives

In `docs/interface.md`, map each capability to one primitive:

- **Resource** = static data
- **Tool** = parameterized operation that computes/returns results
- **Prompt** = guided workflow (often orchestrates multiple tools)

**Include at least:**

- 3 Resources
- 2 Tools
- 1 Prompt template

### 4. Design and implement Resource URIs

In the server code, add at least 3 Resources with stable URIs. Use a consistent URI scheme, like:

- `git-activity://summary/{repo_path}`
- `git-activity://teams/backend`
- `git-activity://ownership/CODEOWNERS`

### 5. Design and implement Tool schemas (JSON Schema)

Add 2 Tools and define their input schemas (name, description, parameters):

- `analyze_hotspots(repo_path, days=30, branch=...)` - identifies frequently changed files with many authors
- `analyze_commit_patterns(repo_path, days=30, author=...)` - analyzes commit frequency and patterns

### 6. Add a prompt template as a workflow

Add at least 1 Prompt template. Make it a workflow that references your tools, e.g.:

- "Repo health review": check build failures -> identify culprit commits -> cross-reference hotspots -> produce recommendations.

### 7. Add permission boundaries

1. Add repository access control:
   - Create a config file `config/allowed_repos.json`.
   - Validate `repo_path` is inside allowed directories.
   - Validate `file_path` stays inside the repo (block `../` traversal).
2. Add a transport security placeholder:
   - Add a simple auth check (API key/JWT header) or a documented TODO in the SSE middleware.

### 8. Extra mile (optional)

Add an extra tool of your choice.

## Submission Checklist

- [ ] **Documentation (`docs/interface.md`)**
  - [ ] 5-8 host questions with required data listed
  - [ ] All data sources listed (git log, file history, etc.)
  - [ ] Mapping table: 3+ Resources, 2+ Tools, 1+ Prompt
- [ ] **Resources (server code)**
  - [ ] 3 Resources with URIs like `git-activity://summary/{repo_path}`
  - [ ] Resources return static data (not empty)
- [ ] **Tools (server code)**
  - [ ] `analyze_hotspots` schema defined and implemented
  - [ ] `analyze_commit_patterns` schema defined and implemented
  - [ ] Extra mile: 1 additional tool (optional)
- [ ] **Prompt Template (server code)**
  - [ ] 1 workflow prompt referencing your tools (e.g. "Repo health review")
- [ ] **Security**
  - [ ] `config/allowed_repos.json` exists with >= 1 repo path
  - [ ] `repo_path` validation blocks paths outside allowed dirs
  - [ ] `file_path` blocks `../` traversal
  - [ ] SSE auth: API key check OR "TODO: add JWT" comment
- [ ] **Tests pass**
  - [ ] `pytest` runs green
  - [ ] MCP inspector discovers all 3 Resources + 2 Tools + 1 Prompt

## Running the Server

```bash
uv run python server.py
```

## Running Tests

```bash
uv run pytest
```
