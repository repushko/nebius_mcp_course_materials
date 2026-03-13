# MCP Interface Design: Git Activity Analyzer

## 1. Host Questions

### Which files are risky to change?
- Commit history per file (frequency of changes)
- Number of unique authors per file
- Recent bug-fix commits touching the file

### What's the ownership schema of repositories?
- CODEOWNERS file content
- Author contribution stats per directory

### What changed most in the last 30 days?
- Commit log filtered by date range
- File change counts aggregated over the period

### Who are the top contributors?
- Author commit counts
- Lines added/deleted per author

### Are there any commit pattern anomalies?
- Commit frequency by day of week and hour
- Large commits (many files changed at once)

### What is the team structure?
- Team member list with roles
- Which directories each team owns

### What is the CI/CD build health?
- Recent build pass/fail rates
- Most common failure stages

### What are the recent deployments?
- Deployment timestamps, environments, versions

## 2. Data Sources

- Git commit log (messages, authors, timestamps, diffs)
- File change history (which files change most frequently)
- Branch information (active branches, merge patterns)
- Author contributions (lines added/deleted, files touched)
- CI/CD build history (pipeline runs, stages, pass/fail)
- Team structure (members, roles, assignments)
- Repository ownership (code owners, review policies)
- Deployment history (environments, versions, timestamps)

## 3. Mapping to MCP Primitives

| Capability | MCP Primitive | URI / Name |
|---|---|---|
| Repository summary | Resource | `git-activity://summary/{repo_path}` |
| Team structure | Resource | `git-activity://teams/backend` |
| Code ownership | Resource | `git-activity://ownership/CODEOWNERS` |
| Analyze file hotspots | Tool | `analyze_hotspots(repo_path, days, limit)` |
| Analyze commit patterns | Tool | `analyze_commit_patterns(repo_path, days, author)` |
| Repo health review | Prompt | `repo_health_review(repo_path)` |
