from app import server

# TODO: Add JWT/API-key auth check in SSE transport middleware

import tools  # noqa: E402, F401 — registers tool/resource/prompt handlers as a side effect

if __name__ == "__main__":
    server.run()
