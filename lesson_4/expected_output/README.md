# 1. Questions
- Which files are risky to change?
- Ownership schema of repositories

# 2. Identify Data Sources
- Git commit log (messages, authors, timestamps, diffs) 
- File change history (which files change most frequently) 
- Branch information (active branches, merge patterns) 
- Author contributions (lines added/deleted, files touched)
- CI/CD build history (pipeline runs, stages, pass/fail) 
- Team structure (members, roles, assignments) 
- Repository ownership (code owners, review policies) 
- Deployment history (environments, versions, timestamps)

# 3. Map to MCP Primitives
- Static data → Resource. 
- Parameterized operations → Tool. 
- Guided workflows → Prompt.

# 4. Design Resource URIs
- git-activity://teams/backend 
- git-activity://ownership/CODEOWNERS
- git-activity://summary/{repo_path}

# 5. Design Tool Schemas
- tool: analyze_hotspot
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "analyze_hotspot Tool Schema",
  "description": "Schema for the analyze_hotspot tool, which analyzes file hotspots in a Git repository.",
  "type": "object",
  "properties": {
    "repo_path": {
      "type": "string",
      "description": "The local or remote path to the Git repository to be analyzed."
    },
    "branch": {
      "type": "string",
      "description": "The branch to analyze for hotspots. Defaults to the repository's default branch.",
      "default": "main"
    },
    "time_window_days": {
      "type": "integer",
      "description": "Number of days in the past to include in the analysis. If omitted, the full commit history is analyzed.",
      "minimum": 1
    },
    "author_filter": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of author names or emails to include in the analysis. If omitted, all authors are included."
    },
    "top_n": {
      "type": "integer",
      "description": "Return only the top N hotspots. If omitted, returns all hotspots.",
      "minimum": 1
    }
  },
  "required": ["repo_path"],
  "additionalProperties": false
}
```
/* Example Usage:
{
  "repo_path": "/path/to/repo",
  "branch": "develop",
  "time_window_days": 90,
  "author_filter": ["alice@example.com", "bob@example.com"],
  "top_n": 10
}
*/

# 6. Prompt Templates as Workflows
# 7. Auth + Security


