"""
Autotests for Practice 3+4: Validating & Debugging MCP Server Tools.

Validates that the expected_output repo:
- Has correct structure (files, tools registered, imports)
- Has all three get_build_history bugs fixed:
  - Bug 1: status filter uses == (not !=)
  - Bug 2: total_builds is computed before filtering
  - Bug 3: BUILDS is copied (list(BUILDS)), not referenced directly
- Existing tools still work correctly
- In-repo test suite exists and passes
"""
import ast
import asyncio
import json
import os
import sys

import pytest

EXPECTED_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "expected_output")
TOOLS_PY = os.path.join(EXPECTED_OUTPUT, "tools.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def repo_path(*parts: str) -> str:
    return os.path.join(EXPECTED_OUTPUT, *parts)


def file_exists(path: str) -> bool:
    return os.path.isfile(repo_path(path))


def read_file(path: str) -> str:
    with open(repo_path(path)) as f:
        return f.read()


def _parse_tools() -> ast.Module:
    with open(TOOLS_PY) as f:
        return ast.parse(f.read())


def _find_function(tree: ast.Module, name: str) -> ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    return None


def _get_source_lines() -> list[str]:
    with open(TOOLS_PY) as f:
        return f.readlines()


def get_decorator_names(func_def):
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


def find_all_tools(tree: ast.Module) -> list[str]:
    tools = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if "server.tool" in get_decorator_names(node):
                tools.append(node.name)
    return tools


# ---------------------------------------------------------------------------
# Structure Tests
# ---------------------------------------------------------------------------


class TestStructure:
    def test_required_files_exist(self):
        for fname in ["server.py", "app.py", "tools.py", "analysis.py", "git_utils.py"]:
            assert file_exists(fname), f"{fname} must exist"

    def test_server_uses_fastmcp(self):
        content = read_file("app.py")
        assert "FastMCP" in content

    def test_tools_registered(self):
        tree = _parse_tools()
        tools = find_all_tools(tree)
        assert "analyze_hotspots" in tools
        assert "get_build_history" in tools

    def test_tests_directory_exists(self):
        assert os.path.isdir(repo_path("tests")), "tests/ directory must exist"

    def test_tools_import_from_app(self):
        """tools.py must import server from app, not from server (avoids circular import)."""
        content = read_file("tools.py")
        assert "from app import server" in content, (
            "tools.py must use 'from app import server' to avoid circular imports"
        )


# ---------------------------------------------------------------------------
# Bug Fix Tests (Static Analysis)
# ---------------------------------------------------------------------------


class TestBugFixesStatic:
    """AST + source-level checks that the three bugs have been corrected."""

    def test_status_filter_uses_equality(self):
        """Bug 1: status filter must use == not !=."""
        source = open(TOOLS_PY).read()
        tree = ast.parse(source)
        func = _find_function(tree, "get_build_history")
        assert func is not None, "get_build_history not found"

        for node in ast.walk(func):
            if isinstance(node, ast.ListComp):
                for gen in node.generators:
                    for if_clause in gen.ifs:
                        if isinstance(if_clause, ast.Compare):
                            source_segment = ast.get_source_segment(source, if_clause)
                            if source_segment and '"status"' in source_segment:
                                for op in if_clause.ops:
                                    assert not isinstance(op, ast.NotEq), (
                                        "Bug 1 NOT fixed: status filter uses != instead of =="
                                    )

    def test_total_builds_uses_full_dataset(self):
        """Bug 2: total_builds must reflect len(BUILDS) or be computed before filtering."""
        lines = _get_source_lines()
        func = _find_function(_parse_tools(), "get_build_history")
        assert func is not None

        func_lines = lines[func.lineno - 1 : func.end_lineno]

        total_line_idx = None
        first_filter_line_idx = None
        for i, line in enumerate(func_lines):
            stripped = line.strip()
            if stripped.startswith("total") and "len(" in stripped:
                total_line_idx = i
            if first_filter_line_idx is None and ("branch" in stripped or "status" in stripped) and "builds = [" in stripped:
                first_filter_line_idx = i

        assert total_line_idx is not None, "Could not find total assignment"

        total_line = func_lines[total_line_idx].strip()
        uses_builds_constant = "len(BUILDS)" in total_line
        set_before_filtering = first_filter_line_idx is None or total_line_idx < first_filter_line_idx

        assert uses_builds_constant or set_before_filtering, (
            f"Bug 2 NOT fixed: total_builds is computed after filtering. "
            f"total at line {total_line_idx}, first filter at line {first_filter_line_idx}"
        )

    def test_builds_uses_list_copy(self):
        """Bug 3: builds must be a copy of BUILDS, not a direct reference."""
        lines = _get_source_lines()
        func = _find_function(_parse_tools(), "get_build_history")
        assert func is not None

        func_lines = lines[func.lineno - 1 : func.end_lineno]

        for line in func_lines:
            stripped = line.strip()
            if stripped.startswith("builds = ") and "BUILDS" in stripped:
                assert "list(BUILDS)" in stripped or "BUILDS[:]" in stripped or "BUILDS.copy()" in stripped, (
                    f"Bug 3 NOT fixed: builds is assigned directly from BUILDS without copying: {stripped}"
                )
                break


# ---------------------------------------------------------------------------
# Functional tests (import expected_output, run handlers)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def _add_expected_output_to_path():
    sys.path.insert(0, EXPECTED_OUTPUT)
    yield
    sys.path.remove(EXPECTED_OUTPUT)


@pytest.fixture
def temp_repo():
    """Temporary git repo with 3 known commits."""
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    path = tempfile.mkdtemp()

    def git(*args):
        subprocess.run(["git", "-C", path, *args], check=True, capture_output=True)

    git("init")
    git("config", "user.email", "alice@example.com")
    git("config", "user.name", "Alice")

    (Path(path) / "README.md").write_text("# test repo")
    git("add", ".")
    git("commit", "-m", "init")

    (Path(path) / "foo.py").write_text("x = 1")
    (Path(path) / "bar.py").write_text("y = 2")
    git("add", ".")
    git("commit", "-m", "add foo and bar")

    (Path(path) / "foo.py").write_text("x = 2")
    git("add", ".")
    git("commit", "-m", "update foo")

    yield path
    shutil.rmtree(path, ignore_errors=True)


class TestBugFixesFunctional:
    """Call get_build_history and verify correct behavior."""

    @pytest.fixture(autouse=True)
    def _import_tools(self, temp_repo):
        self.temp_repo = temp_repo
        import tools
        self.tools = tools

    def _json(self, content):
        return json.loads(content[0].text)

    def test_status_filter_returns_matching_builds(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, status="failed")
        ))
        assert len(data["results"]) > 0
        assert all(b["status"] == "failed" for b in data["results"]), (
            "Status filter should return only builds matching the requested status"
        )

    def test_status_filter_failed_count(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, status="failed")
        ))
        assert len(data["results"]) == 4, "There are exactly 4 failed builds in BUILDS"

    def test_status_filter_success_count(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, status="success")
        ))
        assert len(data["results"]) == 6, "There are exactly 6 successful builds in BUILDS"

    def test_total_builds_reflects_full_dataset(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, status="failed")
        ))
        assert data["total_builds"] == 10, (
            "total_builds must reflect the full unfiltered dataset (10 builds)"
        )

    def test_total_builds_unaffected_by_branch_filter(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, branch="main")
        ))
        assert data["total_builds"] == 10

    def test_no_filters_returns_all(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo)
        ))
        assert len(data["results"]) == 10
        assert data["total_builds"] == 10

    def test_branch_filter(self):
        data = self._json(asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, branch="main")
        ))
        assert all(b["branch"] == "main" for b in data["results"])
        assert len(data["results"]) == 4

    def test_module_level_builds_not_mutated(self):
        original_len = len(self.tools.BUILDS)
        asyncio.run(
            self.tools.get_build_history(repo_path=self.temp_repo, status="failed")
        )
        assert len(self.tools.BUILDS) == original_len, (
            "BUILDS module-level list must not be mutated by get_build_history"
        )


# ---------------------------------------------------------------------------
# Existing tools still work
# ---------------------------------------------------------------------------


class TestExistingTools:
    """Verify other tools haven't been broken by the fix."""

    @pytest.fixture(autouse=True)
    def _import_tools(self, temp_repo):
        self.temp_repo = temp_repo
        import tools
        self.tools = tools

    def _json(self, content):
        return json.loads(content[0].text)

    def test_analyze_hotspots_still_works(self):
        data = self._json(asyncio.run(
            self.tools.analyze_hotspots(repo_path=self.temp_repo)
        ))
        assert isinstance(data, list)
        assert len(data) > 0

    def test_analyze_hotspots_with_mock(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, top_n=10)

        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["file"] == "src/auth.py"
        assert results[0]["risk_score"] == 6

    def test_analyze_file_activity_still_works(self):
        data = self._json(asyncio.run(
            self.tools.analyze_file_activity(repo_path=self.temp_repo)
        ))
        assert "results" in data
        assert "total" in data

    def test_error_handling_nonexistent_path(self):
        from mcp.shared.exceptions import McpError
        with pytest.raises(McpError):
            asyncio.run(self.tools.analyze_hotspots(repo_path="/nonexistent/path"))

    def test_error_handling_not_git_repo(self, tmp_path):
        from mcp.shared.exceptions import McpError
        with pytest.raises(McpError):
            asyncio.run(self.tools.analyze_hotspots(repo_path=str(tmp_path)))


# ---------------------------------------------------------------------------
# In-repo tests exist and cover get_build_history
# ---------------------------------------------------------------------------


class TestInRepoTests:
    """Verify the expected_output ships its own tests for get_build_history."""

    def test_conftest_exists(self):
        assert file_exists("tests/conftest.py"), "tests/conftest.py must exist"

    def test_test_tools_exists(self):
        assert file_exists("tests/test_tools.py"), "tests/test_tools.py must exist"

    def test_in_repo_tests_cover_build_history(self):
        path = os.path.join(EXPECTED_OUTPUT, "tests", "test_tools.py")
        with open(path) as f:
            source = f.read()
        assert "get_build_history" in source, (
            "In-repo tests should include tests for get_build_history"
        )

    def test_in_repo_tests_pass(self):
        """Run the in-repo test suite and confirm it passes."""
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
