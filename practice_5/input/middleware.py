import json
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def _load_allowed_keys() -> set[str]:
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        data = json.loads(config_path.read_text())
        return set(data.get("allowed_api_keys", []))
    return set()


ALLOWED_API_KEYS = _load_allowed_keys()


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] not in ALLOWED_API_KEYS:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)
