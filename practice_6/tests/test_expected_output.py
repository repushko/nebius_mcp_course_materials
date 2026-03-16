"""
Practice 6 autotests — validate the mcp_client_demo.py script.

Tests use AST-based static analysis and import checks.
No API key required for tests.
"""
import ast
import asyncio
import json
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "expected_output")
CLIENT_SCRIPT = os.path.join(EXPECTED_OUTPUT, "mcp_client_demo.py")
TOOLS_PY = os.path.join(EXPECTED_OUTPUT, "tools.py")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


def _parse(path: str) -> ast.Module:
    return ast.parse(_read(path))


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

class TestStructure:
    def test_client_script_exists(self):
        assert os.path.isfile(CLIENT_SCRIPT), "mcp_client_demo.py must exist"

    def test_tools_py_exists(self):
        assert os.path.isfile(TOOLS_PY)

    def test_dockerfile_exists(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "Dockerfile"))

    def test_server_py_exists(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "server.py"))

    def test_in_repo_tests_exist(self):
        assert os.path.isdir(os.path.join(EXPECTED_OUTPUT, "tests"))


# ---------------------------------------------------------------------------
# Client script: static analysis
# ---------------------------------------------------------------------------

class TestClientScriptStatic:
    """AST-based checks on mcp_client_demo.py."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.source = _read(CLIENT_SCRIPT)
        self.tree = _parse(CLIENT_SCRIPT)

    def test_no_todo_remaining(self):
        """All TODOs should be resolved."""
        assert "TODO" not in self.source, "mcp_client_demo.py still contains TODO placeholders"

    def test_does_not_import_anthropic(self):
        """Script must NOT import anthropic — this is a pure MCP client."""
        imports = [
            node for node in ast.walk(self.tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        import_names = []
        for imp in imports:
            if isinstance(imp, ast.Import):
                import_names.extend(alias.name for alias in imp.names)
            elif isinstance(imp, ast.ImportFrom) and imp.module:
                import_names.append(imp.module)
        assert not any("anthropic" in name for name in import_names), (
            "Script must NOT import anthropic"
        )

    def test_imports_mcp_client(self):
        assert "mcp" in self.source, "Script must import from MCP client library"
        assert "ClientSession" in self.source, "Script must use ClientSession"

    def test_imports_stdio_client(self):
        assert "stdio_client" in self.source, (
            "Script must use stdio_client for MCP connection"
        )

    def test_has_run_client_function(self):
        func = _find_function(self.tree, "run_client")
        assert func is not None, "Script must define a run_client function"

    def test_run_client_is_async(self):
        func = _find_function(self.tree, "run_client")
        assert func is not None
        assert isinstance(func, ast.AsyncFunctionDef), "run_client must be async"

    def test_has_main_function(self):
        func = _find_function(self.tree, "main")
        assert func is not None, "Script must define a main function"

    def test_has_main_guard(self):
        assert '__name__' in self.source and '__main__' in self.source, (
            "Script must have if __name__ == '__main__' guard"
        )

    def test_uses_list_tools(self):
        assert "list_tools" in self.source, (
            "Script must call session.list_tools()"
        )

    def test_uses_initialize(self):
        assert "initialize" in self.source, (
            "Script must call session.initialize()"
        )

    def test_uses_server_parameters(self):
        assert "StdioServerParameters" in self.source, (
            "Script must use StdioServerParameters"
        )

    def test_prints_output(self):
        func = _find_function(self.tree, "run_client")
        assert func is not None
        has_print = False
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    has_print = True
                    break
        assert has_print, "run_client must print the tool listing"


# ---------------------------------------------------------------------------
# Existing MCP tools still work
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
