import logging
import sys

from app import server
from middleware import ApiKeyMiddleware

# Log to stderr — stdout is reserved for the MCP stdio protocol
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

import tools  # noqa: E402, F401 — registers tool handlers as a side effect

if __name__ == "__main__":
    if "--sse" in sys.argv:
        import uvicorn
        logger.info("Starting git-activity-analyzer (SSE transport, port 8000)")
        app = server.streamable_http_app()
        app.add_middleware(ApiKeyMiddleware)
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        logger.info("Starting git-activity-analyzer (stdio transport)")
        logger.info("Tools: analyze_hotspots, analyze_file_activity, get_team_structure, get_deployment_history")
        logger.info("Inspect with:  npx @modelcontextprotocol/inspector uv run server.py")
        server.run()
