import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config" / "allowed_repos.json"


def load_allowed_repos() -> list[str]:
    if not CONFIG_PATH.exists():
        return []
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    return data.get("allowed_repos", [])


def validate_repo_path(repo_path: str) -> str:
    """Validate that repo_path is inside an allowed directory.

    Returns the resolved path if valid, raises ValueError otherwise.
    """
    resolved = os.path.realpath(repo_path)
    allowed = load_allowed_repos()
    for allowed_dir in allowed:
        allowed_resolved = os.path.realpath(allowed_dir)
        if resolved.startswith(allowed_resolved + os.sep) or resolved == allowed_resolved:
            return resolved
    raise ValueError(
        f"Repository path '{repo_path}' is not inside any allowed directory. "
        f"Allowed: {allowed}"
    )


def validate_file_path(repo_path: str, file_path: str) -> str:
    """Validate that file_path stays inside repo_path (block ../ traversal).

    Returns the resolved file path if valid, raises ValueError otherwise.
    """
    repo_resolved = os.path.realpath(repo_path)
    full_path = os.path.realpath(os.path.join(repo_resolved, file_path))
    if not full_path.startswith(repo_resolved + os.sep) and full_path != repo_resolved:
        raise ValueError(
            f"File path '{file_path}' escapes the repository directory. "
            f"Path traversal is not allowed."
        )
    return full_path
