"""
Tool handler tests — call handlers directly with asyncio.run(), no running server needed.
FastMCP's @server.tool() registers the function but returns it unchanged, so it's
callable as a plain async function. Handlers return list[TextContent]; extract
.text before parsing JSON.
"""
import asyncio
import json

import pytest

import tools
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS


def _json(content):
    """Extract and parse the JSON text from a list[TextContent] result."""
    return json.loads(content[0].text)


# ---------------------------------------------------------------------------
# analyze_hotspots
# ---------------------------------------------------------------------------

def test_hotspots_nonexistent_path():
    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.analyze_hotspots(repo_path="/nonexistent/path"))
    assert exc_info.value.error.code == INVALID_PARAMS


def test_hotspots_not_a_git_repo(tmp_path):
    # tmp_path is a real directory but has no .git
    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.analyze_hotspots(repo_path=str(tmp_path)))
    assert exc_info.value.error.code == INVALID_PARAMS


def test_hotspots_returns_ranked_json(temp_repo):
    data = _json(asyncio.run(tools.analyze_hotspots(repo_path=temp_repo)))

    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert first["file"] == "foo.py"
    assert {"file", "authors", "changes", "risk_score"} <= first.keys()


def test_hotspots_top_n_limits_results(temp_repo):
    data = _json(asyncio.run(tools.analyze_hotspots(repo_path=temp_repo, top_n=1)))
    assert len(data) == 1


def test_hotspots_author_filter(temp_repo):
    # filter to an email that made no commits → empty list
    data = _json(asyncio.run(
        tools.analyze_hotspots(repo_path=temp_repo, author_filter=["nobody@example.com"])
    ))
    assert data == []


# ---------------------------------------------------------------------------
# analyze_file_activity
# ---------------------------------------------------------------------------

def test_file_activity_nonexistent_path():
    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.analyze_file_activity(repo_path="/nonexistent/path"))
    assert exc_info.value.error.code == INVALID_PARAMS


def test_file_activity_not_a_git_repo(tmp_path):
    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.analyze_file_activity(repo_path=str(tmp_path)))
    assert exc_info.value.error.code == INVALID_PARAMS


def test_file_activity_returns_paginated_shape(temp_repo):
    data = _json(asyncio.run(tools.analyze_file_activity(repo_path=temp_repo)))

    assert {"results", "total", "limit"} <= data.keys()
    assert isinstance(data["results"], list)
    assert data["total"] == 2        # foo.py and bar.py
    assert data["limit"] == 20       # default


def test_file_activity_limit_respected(temp_repo):
    data = _json(asyncio.run(tools.analyze_file_activity(repo_path=temp_repo, limit=1)))

    assert len(data["results"]) == 1
    assert data["total"] == 2        # total unchanged by limit


# ---------------------------------------------------------------------------
# get_build_history
# ---------------------------------------------------------------------------

def test_build_history_nonexistent_path():
    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.get_build_history(repo_path="/nonexistent/path"))
    assert exc_info.value.error.code == INVALID_PARAMS


def test_build_history_not_a_git_repo(tmp_path):
    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.get_build_history(repo_path=str(tmp_path)))
    assert exc_info.value.error.code == INVALID_PARAMS


def test_build_history_no_filters(temp_repo):
    data = _json(asyncio.run(tools.get_build_history(repo_path=temp_repo)))

    assert data["total_builds"] == 10  # full dataset
    assert len(data["results"]) == 10


def test_build_history_status_filter_failed(temp_repo):
    data = _json(asyncio.run(tools.get_build_history(repo_path=temp_repo, status="failed")))

    assert all(b["status"] == "failed" for b in data["results"])
    assert len(data["results"]) == 4  # 4 failed builds in BUILDS


def test_build_history_status_filter_success(temp_repo):
    data = _json(asyncio.run(tools.get_build_history(repo_path=temp_repo, status="success")))

    assert all(b["status"] == "success" for b in data["results"])
    assert len(data["results"]) == 6  # 6 successful builds in BUILDS


def test_build_history_branch_filter(temp_repo):
    data = _json(asyncio.run(tools.get_build_history(repo_path=temp_repo, branch="main")))

    assert all(b["branch"] == "main" for b in data["results"])
    assert len(data["results"]) == 4  # 4 main builds


def test_build_history_total_reflects_full_dataset(temp_repo):
    """total_builds must always reflect the full unfiltered dataset."""
    data = _json(asyncio.run(tools.get_build_history(repo_path=temp_repo, status="failed")))
    assert data["total_builds"] == 10

    data = _json(asyncio.run(tools.get_build_history(repo_path=temp_repo, branch="main")))
    assert data["total_builds"] == 10


def test_build_history_uses_list_copy(temp_repo):
    """Calling get_build_history must not mutate the module-level BUILDS list."""
    original_len = len(tools.BUILDS)
    asyncio.run(tools.get_build_history(repo_path=temp_repo, status="failed"))
    assert len(tools.BUILDS) == original_len
