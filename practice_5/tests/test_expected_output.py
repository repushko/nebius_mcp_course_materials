"""
Lesson 5 autotests — validate the Dockerfile and server health endpoint.

Tests run against the expected_output directory.
Checks Dockerfile structure, server.py health endpoint, and in-repo tests.
"""
import ast
import asyncio
import json
import os
import re
import sys

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "expected_output")
DOCKERFILE = os.path.join(EXPECTED_OUTPUT, "Dockerfile")
SERVER_PY = os.path.join(EXPECTED_OUTPUT, "server.py")
TOOLS_PY = os.path.join(EXPECTED_OUTPUT, "tools.py")
PYPROJECT_TOML = os.path.join(EXPECTED_OUTPUT, "pyproject.toml")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

class TestStructure:
    def test_dockerfile_exists(self):
        assert os.path.isfile(DOCKERFILE)

    def test_server_py_exists(self):
        assert os.path.isfile(SERVER_PY)

    def test_tools_py_exists(self):
        assert os.path.isfile(TOOLS_PY)

    def test_pyproject_toml_exists(self):
        assert os.path.isfile(PYPROJECT_TOML)

    def test_expected_output_has_in_repo_tests(self):
        assert os.path.isdir(os.path.join(EXPECTED_OUTPUT, "tests"))

    def test_config_directory_exists(self):
        assert os.path.isdir(os.path.join(EXPECTED_OUTPUT, "config"))

    def test_docs_directory_exists(self):
        assert os.path.isdir(os.path.join(EXPECTED_OUTPUT, "docs"))

    def test_uv_lock_exists(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "uv.lock"))


# ---------------------------------------------------------------------------
# Dockerfile validation
# ---------------------------------------------------------------------------

class TestDockerfile:
    """Validate the Dockerfile has all required instructions."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(DOCKERFILE)
        self.lines = [line.strip() for line in self.content.splitlines() if line.strip() and not line.strip().startswith("#")]

    def test_no_todo_remaining(self):
        """All TODOs should be resolved."""
        assert "TODO" not in self.content, "Dockerfile still contains TODO placeholders"

    def test_no_placeholder_remaining(self):
        """No ??? placeholders should remain."""
        assert "???" not in self.content, "Dockerfile still contains ??? placeholders"

    def test_has_from_instruction(self):
        from_lines = [l for l in self.lines if l.startswith("FROM")]
        assert len(from_lines) >= 1, "Dockerfile must have a FROM instruction"

    def test_base_image_is_python_slim(self):
        from_lines = [l for l in self.lines if l.startswith("FROM")]
        assert any("python:" in l and "slim" in l for l in from_lines), (
            "Base image should be python:X.Y-slim"
        )

    def test_installs_git(self):
        assert "git" in self.content, "Dockerfile must install git"

    def test_installs_uv(self):
        assert "uv" in self.content, "Dockerfile must install uv"

    def test_copies_pyproject_toml(self):
        copy_lines = [l for l in self.lines if l.startswith("COPY")]
        assert any("pyproject.toml" in l for l in copy_lines), (
            "Dockerfile must COPY pyproject.toml"
        )

    def test_copies_uv_lock(self):
        copy_lines = [l for l in self.lines if l.startswith("COPY")]
        assert any("uv.lock" in l for l in copy_lines), (
            "Dockerfile must COPY uv.lock"
        )

    def test_copies_source_files(self):
        copy_lines = [l for l in self.lines if l.startswith("COPY")]
        assert any(".py" in l or "*.py" in l for l in copy_lines), (
            "Dockerfile must COPY Python source files"
        )

    def test_runs_uv_sync(self):
        run_lines = [l for l in self.lines if l.startswith("RUN")]
        assert any("uv" in l and "sync" in l for l in run_lines), (
            "Dockerfile must run uv sync to install dependencies"
        )

    def test_declares_volume(self):
        assert any(l.startswith("VOLUME") for l in self.lines), (
            "Dockerfile must declare a VOLUME"
        )

    def test_volume_is_repo(self):
        volume_lines = [l for l in self.lines if l.startswith("VOLUME")]
        assert any("/repo" in l for l in volume_lines), (
            "VOLUME should be /repo for mounting git repositories"
        )

    def test_exposes_port(self):
        expose_lines = [l for l in self.lines if l.startswith("EXPOSE")]
        assert len(expose_lines) >= 1, "Dockerfile must EXPOSE a port"

    def test_exposes_port_8000(self):
        expose_lines = [l for l in self.lines if l.startswith("EXPOSE")]
        assert any("8000" in l for l in expose_lines), (
            "Dockerfile must EXPOSE port 8000"
        )

    def test_has_cmd(self):
        cmd_lines = [l for l in self.lines if l.startswith("CMD")]
        assert len(cmd_lines) >= 1, "Dockerfile must have a CMD instruction"

    def test_cmd_starts_server_sse(self):
        cmd_lines = [l for l in self.lines if l.startswith("CMD")]
        assert any("server.py" in l and "--sse" in l for l in cmd_lines), (
            "CMD should start server.py in SSE mode"
        )

    def test_has_workdir(self):
        assert any(l.startswith("WORKDIR") for l in self.lines), (
            "Dockerfile should set a WORKDIR"
        )


# ---------------------------------------------------------------------------
# Server health endpoint
# ---------------------------------------------------------------------------

class TestServerHealthEndpoint:
    """Validate that server.py includes a /health endpoint."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.source = _read(SERVER_PY)

    def test_health_route_defined(self):
        assert "/health" in self.source, (
            "server.py must define a /health route"
        )

    def test_health_returns_json(self):
        assert "JSONResponse" in self.source, (
            "Health endpoint should use JSONResponse"
        )

    def test_health_returns_status_ok(self):
        assert '"status"' in self.source or "'status'" in self.source, (
            "Health endpoint should return a status field"
        )
        assert '"ok"' in self.source or "'ok'" in self.source, (
            "Health endpoint should return status ok"
        )


# ---------------------------------------------------------------------------
# pyproject.toml includes uvicorn
# ---------------------------------------------------------------------------

class TestDependencies:
    def test_uvicorn_in_dependencies(self):
        content = _read(PYPROJECT_TOML)
        assert "uvicorn" in content, (
            "pyproject.toml must include uvicorn for SSE mode"
        )


# ---------------------------------------------------------------------------
# Existing tools still work (functional)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def _add_expected_output_to_path():
    sys.path.insert(0, EXPECTED_OUTPUT)
    yield
    sys.path.remove(EXPECTED_OUTPUT)


class TestExistingToolsWork:
    @pytest.fixture(autouse=True)
    def _import_tools(self, temp_repo):
        self.temp_repo = temp_repo
        import tools
        self.tools = tools

    def _json(self, content):
        return json.loads(content[0].text)

    def test_analyze_hotspots(self):
        data = self._json(asyncio.run(
            self.tools.analyze_hotspots(repo_path=self.temp_repo)
        ))
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_build_history(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo)
        ))
        assert data["total_builds"] == 10
        assert len(data["results"]) == 10

    def test_get_build_history_filter(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, status="failed")
        ))
        assert all(b["status"] == "failed" for b in data["results"])


# ---------------------------------------------------------------------------
# In-repo tests pass
# ---------------------------------------------------------------------------

class TestInRepoTests:
    def test_in_repo_tests_pass(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=EXPECTED_OUTPUT,
        )
        assert result.returncode == 0, (
            f"In-repo tests failed:\n{result.stdout}\n{result.stderr}"
        )
