"""
Lesson 6 autotests — validate the mcp_agent_demo.py script.

Tests use AST-based static analysis and import checks.
Does NOT call the Anthropic API (no API key required for tests).
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
AGENT_SCRIPT = os.path.join(EXPECTED_OUTPUT, "mcp_agent_demo.py")
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


def _find_assignment(tree: ast.Module, name: str) -> ast.Assign | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node
    return None


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

class TestStructure:
    def test_agent_script_exists(self):
        assert os.path.isfile(AGENT_SCRIPT), "mcp_agent_demo.py must exist"

    def test_tools_py_exists(self):
        assert os.path.isfile(TOOLS_PY)

    def test_dockerfile_exists(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "Dockerfile"))

    def test_server_py_exists(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "server.py"))

    def test_in_repo_tests_exist(self):
        assert os.path.isdir(os.path.join(EXPECTED_OUTPUT, "tests"))


# ---------------------------------------------------------------------------
# Agent script: static analysis
# ---------------------------------------------------------------------------

class TestAgentScriptStatic:
    """AST-based checks on mcp_agent_demo.py."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.source = _read(AGENT_SCRIPT)
        self.tree = _parse(AGENT_SCRIPT)

    def test_no_todo_remaining(self):
        """All TODOs should be resolved."""
        assert "TODO" not in self.source, "mcp_agent_demo.py still contains TODO placeholders"

    def test_imports_anthropic(self):
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
        assert any("anthropic" in name for name in import_names), (
            "Script must import anthropic"
        )

    def test_imports_mcp_client(self):
        assert "mcp" in self.source, "Script must import from MCP client library"
        assert "ClientSession" in self.source, "Script must use ClientSession"

    def test_imports_stdio_client(self):
        assert "stdio_client" in self.source, (
            "Script must use stdio_client for MCP connection"
        )

    def test_defines_tools_list(self):
        assignment = _find_assignment(self.tree, "TOOLS")
        assert assignment is not None, "Script must define a TOOLS list"

    def test_tools_list_not_empty(self):
        assignment = _find_assignment(self.tree, "TOOLS")
        assert assignment is not None
        # Check it's a non-empty list
        if isinstance(assignment.value, ast.List):
            assert len(assignment.value.elts) > 0, "TOOLS list must not be empty"

    def test_tools_contain_analyze_hotspots(self):
        assert "analyze_hotspots" in self.source, (
            "TOOLS must include analyze_hotspots"
        )

    def test_tool_schema_has_input_schema(self):
        assert "input_schema" in self.source, (
            "Tool schema must include input_schema"
        )

    def test_tool_schema_has_repo_path(self):
        assert "repo_path" in self.source, (
            "Tool schema must include repo_path parameter"
        )

    def test_has_run_agent_function(self):
        func = _find_function(self.tree, "run_agent")
        assert func is not None, "Script must define a run_agent function"

    def test_run_agent_is_async(self):
        func = _find_function(self.tree, "run_agent")
        assert func is not None
        assert isinstance(func, ast.AsyncFunctionDef), "run_agent must be async"

    def test_has_main_function(self):
        func = _find_function(self.tree, "main")
        assert func is not None, "Script must define a main function"

    def test_has_main_guard(self):
        assert '__name__' in self.source and '__main__' in self.source, (
            "Script must have if __name__ == '__main__' guard"
        )

    def test_uses_messages_create(self):
        assert "messages.create" in self.source or "messages_create" in self.source, (
            "Script must call the Anthropic messages API"
        )

    def test_handles_tool_use(self):
        assert "tool_use" in self.source, (
            "Script must detect and handle tool_use responses"
        )

    def test_calls_mcp_server(self):
        assert "call_tool" in self.source, (
            "Script must call the MCP server with session.call_tool"
        )

    def test_sends_tool_result_back(self):
        assert "tool_result" in self.source, (
            "Script must send tool_result back to the model"
        )

    def test_prints_final_answer(self):
        # Check there's a print statement in the function
        func = _find_function(self.tree, "run_agent")
        assert func is not None
        has_print = False
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    has_print = True
                    break
        assert has_print, "run_agent must print the final answer"

    def test_accepts_repo_path_argument(self):
        assert "sys.argv" in self.source, (
            "Script must accept repo_path from command line arguments"
        )


# ---------------------------------------------------------------------------
# Tool schema validation
# ---------------------------------------------------------------------------

class TestToolSchema:
    """Validate the TOOLS list has proper Anthropic format."""

    @pytest.fixture(autouse=True)
    def _load(self):
        sys.path.insert(0, EXPECTED_OUTPUT)
        # Import the module to get TOOLS
        import importlib
        spec = importlib.util.spec_from_file_location("mcp_agent_demo", AGENT_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        # Don't actually execute the module (it would call main)
        # Instead, just exec the top-level assignments
        source = _read(AGENT_SCRIPT)
        tree = ast.parse(source)

        # Extract TOOLS by evaluating just the assignment
        namespace = {}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "TOOLS":
                        exec(compile(ast.Module(body=[node], type_ignores=[]), AGENT_SCRIPT, "exec"), namespace)

        self.tools = namespace.get("TOOLS", [])
        yield
        sys.path.remove(EXPECTED_OUTPUT)

    def test_tools_is_list(self):
        assert isinstance(self.tools, list)

    def test_tools_not_empty(self):
        assert len(self.tools) > 0

    def test_first_tool_is_analyze_hotspots(self):
        assert self.tools[0]["name"] == "analyze_hotspots"

    def test_tool_has_description(self):
        tool = self.tools[0]
        assert "description" in tool
        assert len(tool["description"]) > 10

    def test_tool_has_input_schema(self):
        tool = self.tools[0]
        assert "input_schema" in tool

    def test_input_schema_has_properties(self):
        schema = self.tools[0]["input_schema"]
        assert "properties" in schema

    def test_input_schema_has_repo_path(self):
        props = self.tools[0]["input_schema"]["properties"]
        assert "repo_path" in props

    def test_repo_path_is_required(self):
        schema = self.tools[0]["input_schema"]
        assert "required" in schema
        assert "repo_path" in schema["required"]

    def test_input_schema_type_is_object(self):
        schema = self.tools[0]["input_schema"]
        assert schema.get("type") == "object"


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
