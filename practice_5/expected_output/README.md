# Lesson 5: Packaging an MCP Server with Docker

In this task, you'll package an MCP server into a Docker image.

## Preparation

1. Confirm that `mcp-docker-practice` appears in your account.
2. Clone the repo locally and open it in your editor.
3. Make sure Docker is installed and running.

## Build the Docker image

1. Open `Dockerfile` in the repo root and complete the TODOs:
   - **Base image**: `python:3.12-slim`
   - **Install `git`** (required by GitPython) and `curl` (for the `uv` installer)
   - **Copy `pyproject.toml` + `uv.lock`** first (for Docker layer caching)
   - **Install dependencies** with `uv sync --frozen --no-install-project`
   - **Copy source code** (`.py` files and `config.json`)
   - **Copy config and docs directories**
   - **Declare a volume** at `/repo` for mounting git repositories
   - **Expose port 8000**
   - **Set the default command** to start the server in SSE mode

2. Build the image:

```bash
docker build -t git-activity-analyzer .
```

### Short of time? (fast path)

Use the prefilled `Dockerfile` and only fill the TODO sections. Don't overthink it — you're aiming for a working container, not a perfect production image.

## Run with SSE and verify

1. Run the container in SSE mode and expose port 8000:

```bash
docker run --rm -p 8000:8000 -v /path/to/your/repo:/repo git-activity-analyzer
```

2. Mount any local git repo into the container at `/repo`.

3. Open in your browser:

```
http://localhost:8000/health
```

4. Confirm it returns:

```json
{"status": "ok"}
```

## Submission checklist

- [ ] `Dockerfile` is complete with all TODOs filled in
- [ ] `docker build -t git-activity-analyzer .` succeeds
- [ ] Container starts and exposes port 8000
- [ ] `http://localhost:8000/health` returns `{"status": "ok"}`
