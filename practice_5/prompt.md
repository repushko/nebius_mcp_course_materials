You are working on an MCP server called "git-activity-analyzer". Your task is to complete the `Dockerfile` to package it as a Docker image.

Open `Dockerfile` and fill in all the TODOs:

1. **Base image:** Use `python:3.12-slim`
   ```dockerfile
   FROM python:3.12-slim
   ```

2. **Install system dependencies** — git (for GitPython) and curl (for uv installer):
   ```dockerfile
   RUN apt-get update && apt-get install -y --no-install-recommends git curl \
       && curl -LsSf https://astral.sh/uv/install.sh | sh \
       && apt-get clean && rm -rf /var/lib/apt/lists/*
   ```

3. **Add uv to PATH:**
   ```dockerfile
   ENV PATH="/root/.local/bin:$PATH"
   ```

4. **Copy dependency files first** (for layer caching):
   ```dockerfile
   COPY pyproject.toml uv.lock ./
   ```

5. **Install dependencies:**
   ```dockerfile
   RUN uv sync --frozen --no-install-project
   ```

6. **Copy application source files:**
   ```dockerfile
   COPY *.py config.json ./
   ```

7. **Copy config and docs directories:**
   ```dockerfile
   COPY config/ ./config/
   COPY docs/ ./docs/
   ```

8. **Declare volume, expose port, set command:**
   ```dockerfile
   VOLUME ["/repo"]
   EXPOSE 8000
   CMD ["uv", "run", "server.py", "--sse"]
   ```

Then verify:
- `docker build -t git-activity-analyzer .` succeeds
- `docker run --rm -p 8000:8000 -v /path/to/repo:/repo git-activity-analyzer` starts
- `http://localhost:8000/health` returns `{"status": "ok"}`
