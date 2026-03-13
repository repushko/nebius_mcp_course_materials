"""
Autotests for Lesson 2: MCP Hotspots Handler — Thin Handler + Structured Errors.

Validates that the expected_output repo meets all submission criteria:
- analyze_hotspots is registered with @server.tool()
- Handler is async with correct defaults (days=30, limit=10)
- Handler is a thin wrapper (delegates to data_access + analysis layers)
- InvalidParams errors for non-existent repo and non-git folders
- InternalError errors for analysis/runtime failures
- Output is valid JSON with a ranked list
"""
import ast
import asyncio
import json
import os
import sys
import tempfile

import pytest

REPO_DIR = os.path.join(os.path.dirname(__file__), "..", "expected_output")


# ─── Helpers ─────────────────────────────────────────────────────────────────


def repo_path(*parts: str) -> str:
    return os.path.join(REPO_DIR, *parts)


def file_exists(path: str) -> bool:
    return os.path.isfile(repo_path(path))


def read_file(path: str) -> str:
    with open(repo_path(path)) as f:
        return f.read()


def parse_python(path: str) -> ast.Module:
    return ast.parse(read_file(path))


def get_decorator_names(func_def: ast.AsyncFunctionDef | ast.FunctionDef) -> list[str]:
    """Extract decorator call names like 'server.tool'."""
    names = []
    for dec in func_def.decorator_list:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            obj = dec.func.value
            attr = dec.func.attr
            if isinstance(obj, ast.Name):
                names.append(f"{obj.id}.{attr}")
        elif isinstance(dec, ast.Attribute):
            obj = dec.value
            attr = dec.attr
            if isinstance(obj, ast.Name):
                names.append(f"{obj.id}.{attr}")
    return names


def find_tool_function(tree: ast.Module, tool_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
    """Find a @server.tool() decorated function by name."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if node.name == tool_name and "server.tool" in get_decorator_names(node):
                return node
    return None


def find_all_tools(tree: ast.Module) -> list[str]:
    """Find all @server.tool() decorated function names."""
    tools = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if "server.tool" in get_decorator_names(node):
                tools.append(node.name)
    return tools


# ─── Structure Tests ────────────────────────────────────────────────────────


class TestStructure:
    def test_server_py_exists(self):
        assert file_exists("server.py"), "server.py must exist"

    def test_app_py_exists(self):
        assert file_exists("app.py"), "app.py must exist"

    def test_tools_py_exists(self):
        assert file_exists("tools.py"), "tools.py must exist"

    def test_analysis_py_exists(self):
        assert file_exists("analysis.py"), "analysis.py must exist"

    def test_git_utils_py_exists(self):
        assert file_exists("git_utils.py"), "git_utils.py must exist"

    def test_app_creates_fastmcp(self):
        content = read_file("app.py")
        assert "FastMCP" in content, "app.py must use FastMCP"

    def test_tools_import_from_app(self):
        """tools.py must import server from app, not from server (avoids circular import)."""
        content = read_file("tools.py")
        assert "from app import server" in content, (
            "tools.py must use 'from app import server' to avoid circular imports"
        )

    def test_pyproject_has_dependencies(self):
        content = read_file("pyproject.toml")
        assert "gitpython" in content.lower()
        assert "mcp" in content.lower()


# ─── Tool Registration Tests ────────────────────────────────────────────────


class TestToolRegistration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.tools_tree = parse_python("tools.py")
        self.func = find_tool_function(self.tools_tree, "analyze_hotspots")

    def test_analyze_hotspots_registered(self):
        assert self.func is not None, (
            "analyze_hotspots must be registered with @server.tool()"
        )

    def test_analyze_hotspots_is_async(self):
        assert self.func is not None, "Function not found"
        assert isinstance(self.func, ast.AsyncFunctionDef), (
            "analyze_hotspots must be async"
        )

    def test_has_repo_path_param(self):
        assert self.func is not None, "Function not found"
        param_names = [arg.arg for arg in self.func.args.args]
        assert "repo_path" in param_names, (
            f"Must have 'repo_path' parameter. Found: {param_names}"
        )

    def test_has_days_param(self):
        assert self.func is not None, "Function not found"
        param_names = [arg.arg for arg in self.func.args.args]
        assert "days" in param_names, (
            f"Must have 'days' parameter. Found: {param_names}"
        )

    def test_has_limit_param(self):
        assert self.func is not None, "Function not found"
        param_names = [arg.arg for arg in self.func.args.args]
        assert "limit" in param_names, (
            f"Must have 'limit' parameter. Found: {param_names}"
        )

    def test_days_default_30(self):
        """days parameter should default to 30."""
        assert self.func is not None, "Function not found"
        params = self.func.args
        param_names = [arg.arg for arg in params.args]
        days_idx = param_names.index("days")

        # defaults are right-aligned with params
        num_params = len(param_names)
        num_defaults = len(params.defaults)
        default_start = num_params - num_defaults
        default_idx = days_idx - default_start

        assert default_idx >= 0, "days has no default value"
        default_node = params.defaults[default_idx]
        assert isinstance(default_node, ast.Constant), "Default must be a constant"
        assert default_node.value == 30, (
            f"days default must be 30, got {default_node.value}"
        )

    def test_limit_default_10(self):
        """limit parameter should default to 10."""
        assert self.func is not None, "Function not found"
        params = self.func.args
        param_names = [arg.arg for arg in params.args]
        limit_idx = param_names.index("limit")

        num_params = len(param_names)
        num_defaults = len(params.defaults)
        default_start = num_params - num_defaults
        default_idx = limit_idx - default_start

        assert default_idx >= 0, "limit has no default value"
        default_node = params.defaults[default_idx]
        assert isinstance(default_node, ast.Constant), "Default must be a constant"
        assert default_node.value == 10, (
            f"limit default must be 10, got {default_node.value}"
        )


# ─── Thin Wrapper Tests ─────────────────────────────────────────────────────


class TestThinWrapper:
    def test_tools_imports_analysis(self):
        content = read_file("tools.py")
        assert "import analysis" in content or "from analysis" in content, (
            "tools.py must import the analysis module"
        )

    def test_tools_imports_git_repository(self):
        content = read_file("tools.py")
        assert "GitRepository" in content, (
            "tools.py must use GitRepository from git_utils"
        )

    def test_tools_delegates_to_analysis(self):
        content = read_file("tools.py")
        assert "analysis.analyze_hotspots" in content or "analyzer.analyze_hotspots" in content, (
            "Handler must delegate to analysis.analyze_hotspots()"
        )

    def test_tools_returns_text_content(self):
        content = read_file("tools.py")
        assert "TextContent" in content, (
            "Handler must return MCP TextContent"
        )

    def test_tools_returns_json(self):
        content = read_file("tools.py")
        assert "json.dumps" in content, (
            "Handler must serialize results with json.dumps"
        )


# ─── Error Handling Tests (static analysis) ──────────────────────────────────


class TestErrorHandlingStatic:
    def test_imports_mcp_error(self):
        content = read_file("tools.py")
        assert "McpError" in content, (
            "tools.py must import McpError from mcp.shared.exceptions"
        )

    def test_imports_invalid_params(self):
        content = read_file("tools.py")
        assert "INVALID_PARAMS" in content, (
            "tools.py must import INVALID_PARAMS from mcp.types"
        )

    def test_imports_internal_error(self):
        content = read_file("tools.py")
        assert "INTERNAL_ERROR" in content, (
            "tools.py must import INTERNAL_ERROR from mcp.types"
        )

    def test_checks_path_exists(self):
        """Handler should validate that repo_path exists."""
        content = read_file("tools.py")
        assert "os.path.isdir" in content or "os.path.exists" in content or "Path(" in content, (
            "Handler must check if repo_path exists"
        )

    def test_checks_git_repo(self):
        """Handler should validate that repo_path is a git repo."""
        content = read_file("tools.py")
        assert ".git" in content, (
            "Handler must check for .git directory"
        )

    def test_raises_invalid_params_for_path(self):
        """Handler should raise McpError with INVALID_PARAMS."""
        content = read_file("tools.py")
        assert "INVALID_PARAMS" in content and "McpError" in content, (
            "Handler must raise McpError(ErrorData(code=INVALID_PARAMS, ...)) for bad paths"
        )

    def test_has_try_except(self):
        """Handler should wrap analysis in try/except."""
        content = read_file("tools.py")
        assert "try:" in content and "except" in content, (
            "Handler must have try/except for error handling"
        )

    def test_catches_git_command_error(self):
        """Handler should catch git.GitCommandError."""
        content = read_file("tools.py")
        assert "GitCommandError" in content or "git.GitCommandError" in content or "git.exc" in content, (
            "Handler must catch git command errors"
        )

    def test_raises_internal_error(self):
        """Handler should raise McpError with INTERNAL_ERROR for runtime errors."""
        content = read_file("tools.py")
        assert "INTERNAL_ERROR" in content, (
            "Handler must raise McpError with INTERNAL_ERROR"
        )

    def test_has_analysis_failed_message(self):
        """Generic exceptions should produce 'Analysis failed' message."""
        content = read_file("tools.py")
        assert "Analysis failed" in content, (
            "Generic exception handler must include 'Analysis failed' message"
        )


# ─── Functional Tests (using mock data) ─────────────────────────────────────


class TestFunctional:
    @pytest.fixture(autouse=True)
    def setup(self):
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)

    def test_analysis_hotspots_with_mock(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, limit=10)

        assert isinstance(results, list)
        assert len(results) > 0

        for item in results:
            assert "file" in item
            assert "authors" in item
            assert "changes" in item
            assert "risk_score" in item

        # src/auth.py should be the top hotspot (3 changes, 2 authors, risk=6)
        top = results[0]
        assert top["file"] == "src/auth.py"
        assert top["risk_score"] == 6

    def test_analysis_output_is_json_serializable(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, limit=10)

        # Must be JSON-serializable
        text = json.dumps(results, indent=2)
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_analysis_respects_limit(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, limit=2)
        assert len(results) <= 2

    def test_analysis_sorted_by_risk_score(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, limit=10)

        for i in range(len(results) - 1):
            assert results[i]["risk_score"] >= results[i + 1]["risk_score"], (
                "Results must be sorted by risk_score descending"
            )


# ─── Error Handling Functional Tests ─────────────────────────────────────────


class TestErrorHandlingFunctional:
    @pytest.fixture(autouse=True)
    def setup(self):
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)

    def test_invalid_params_nonexistent_path(self):
        """Handler should raise McpError with INVALID_PARAMS for non-existent path."""
        from tools import analyze_hotspots
        from mcp.shared.exceptions import McpError

        with pytest.raises(McpError) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                analyze_hotspots(repo_path="/nonexistent/path/that/does/not/exist")
            )

        error = exc_info.value.error
        # INVALID_PARAMS is -32602 in JSON-RPC
        assert error.code == -32602 or "INVALID_PARAMS" in str(error.code)

    def test_invalid_params_not_git_repo(self):
        """Handler should raise McpError with INVALID_PARAMS for non-git directory."""
        from tools import analyze_hotspots
        from mcp.shared.exceptions import McpError

        with tempfile.TemporaryDirectory() as tmpdir:
            real_tmpdir = os.path.realpath(tmpdir)
            with pytest.raises(McpError) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    analyze_hotspots(repo_path=real_tmpdir)
                )

            error = exc_info.value.error
            assert error.code == -32602 or "INVALID_PARAMS" in str(error.code)
