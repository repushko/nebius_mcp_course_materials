# TODO: Choose a base image
# Hint: use python:3.12-slim for a lightweight Python image
FROM ???

# TODO: Install system dependencies
# Hint: git is required by GitPython; also install curl to fetch the uv installer
# RUN apt-get update && apt-get install -y --no-install-recommends ... \
#     && curl -LsSf https://astral.sh/uv/install.sh | sh \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# TODO: Add uv to PATH
# Hint: uv installs to /root/.local/bin
# ENV PATH="???:$PATH"

WORKDIR /app

# TODO: Copy dependency files first (for Docker layer caching)
# Hint: copy pyproject.toml and uv.lock before source code
# COPY ??? ./

# TODO: Install dependencies (without the project itself for caching)
# Hint: uv sync --frozen --no-install-project
# RUN ???

# TODO: Copy application source files
# Hint: copy all .py files and config.json
# COPY ??? ./

# TODO: Copy config and docs directories
# COPY ??? ./???

# TODO: Declare a volume for mounting git repositories
# Hint: VOLUME ["/repo"]

# TODO: Expose the SSE port
# Hint: the server listens on port 8000 in SSE mode

# TODO: Set the default command to start the server in SSE mode
# Hint: CMD ["uv", "run", "server.py", "--sse"]
