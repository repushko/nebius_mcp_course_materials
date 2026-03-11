FROM python:3.12-slim

# Install git (required by gitpython) and uv
RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies without the project itself
RUN uv sync --frozen --no-install-project

# Copy application source
COPY *.py config.json ./

# Initialize a git repo so tools work with "." as the repo path
RUN git config --global user.email "docker@example.com" \
    && git config --global user.name "Docker" \
    && git init && git commit --allow-empty -m "init"

EXPOSE 8000

# Run in SSE/HTTP mode so Claude Code and other MCP clients can connect
CMD ["uv", "run", "server.py", "--sse"]
