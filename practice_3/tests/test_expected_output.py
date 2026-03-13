"""
Autotests for Lesson 3: Validating MCP Servers.

Validates that the expected_output repo has all bugs fixed:
- Bug 1: status filter uses == (not !=)
- Bug 2: total_builds is computed before filtering
- Bug 3: BUILDS is copied (list(BUILDS)), not referenced directly
Also validates that existing tools still work correctly.
"""
import ast
import asyncio
import json
import os
import sys

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


# ─── Structure Tests ────────────────────────────────────────────────────────


class TestStructure:
    def test_required_files_exist(self):
        for fname in ["server.py", "app.py", "tools.py", "analysis.py", "git_utils.py"]:
            assert file_exists(fname), f"{fname} must exist"

    def test_server_uses_fastmcp(self):
        content = read_file("app.py")
        assert "FastMCP" in content

    def test_tools_registered(self):
        tree = parse_python("tools.py")
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


# ─── Bug Fix Tests (Static Analysis) ────────────────────────────────────────


class TestBugFixesStatic:
    """Verify that the 3 bugs in get_build_history are fixed via code inspection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = read_file("tools.py")

    def test_status_filter_uses_equality(self):
        """Bug 1 fix: status filter should use == not !=.

        The buggy code had:
            builds = [b for b in builds if b["status"] != status]
        Which EXCLUDES matching builds instead of including them.
        """
        # Find the get_build_history function and check its status filter
        tree = parse_python("tools.py")
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                if node.name == "get_build_history":
                    # Find list comprehensions with status comparison
                    for child in ast.walk(node):
                        if isinstance(child, ast.ListComp):
                            for comp_if in child.generators[0].ifs:
                                if isinstance(comp_if, ast.Compare):
                                    # Check if comparing b["status"] with status
                                    left = comp_if.left
                                    if isinstance(left, ast.Subscript):
                                        if isinstance(left.slice, ast.Constant) and left.slice.value == "status":
                                            ops = comp_if.ops
                                            for op in ops:
                                                assert not isinstance(op, ast.NotEq), (
                                                    "Bug 1 NOT fixed: status filter uses != instead of =="
                                                )

    def test_total_computed_before_filtering(self):
        """Bug 2 fix: total_builds should be computed BEFORE filtering.

        The buggy code computed total after branch/status filtering,
        so total_builds would shrink with filters instead of showing
        the true total.
        """
        tree = parse_python("tools.py")
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                if node.name == "get_build_history":
                    # Get line numbers for key operations
                    total_line = None
                    first_filter_line = None

                    for child in ast.walk(node):
                        # Find: total = len(...)
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if isinstance(target, ast.Name) and target.id == "total":
                                    total_line = child.lineno

                        # Find first list comprehension (branch or status filter)
                        if isinstance(child, ast.ListComp) and first_filter_line is None:
                            first_filter_line = child.lineno

                    assert total_line is not None, "total assignment not found"
                    assert first_filter_line is not None, "filter not found"
                    assert total_line < first_filter_line, (
                        f"Bug 2 NOT fixed: total (line {total_line}) must be computed "
                        f"before filtering (line {first_filter_line})"
                    )

    def test_builds_copied_not_referenced(self):
        """Bug 3 fix: builds should be list(BUILDS), not a direct reference.

        The buggy code had:
            builds = BUILDS
        Which means if branch filtering modifies 'builds' via reassignment
        it's fine, but a direct reference to a mutable global is a code smell
        and risky if anyone adds .append/.pop later.
        """
        tree = parse_python("tools.py")
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                if node.name == "get_build_history":
                    for child in ast.walk(node):
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if isinstance(target, ast.Name) and target.id == "builds":
                                    val = child.value
                                    # Check it's list(BUILDS) or BUILDS.copy() or BUILDS[:]
                                    if isinstance(val, ast.Name) and val.id == "BUILDS":
                                        pytest.fail(
                                            "Bug 3 NOT fixed: builds = BUILDS (direct reference). "
                                            "Should be list(BUILDS) or BUILDS.copy() or BUILDS[:]"
                                        )
                                    return  # Found first builds assignment, that's enough


# ─── Bug Fix Tests (Functional) ─────────────────────────────────────────────


class TestBugFixesFunctional:
    """Run the actual get_build_history handler and verify correct behavior."""

    @pytest.fixture(autouse=True)
    def setup(self):
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)

    def _json(self, content):
        return json.loads(content[0].text)

    def _make_temp_repo(self):
        """Create a minimal temp dir with .git to pass validation."""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmpdir, ".git"))
        return tmpdir

    def test_status_filter_includes_matching(self):
        """Bug 1: filtering by status='failed' should return only failed builds."""
        import tools

        tmpdir = self._make_temp_repo()
        try:
            data = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir, status="failed")
            ))
            results = data["results"]
            assert len(results) > 0, "Should return some failed builds"
            for build in results:
                assert build["status"] == "failed", (
                    f"Expected only failed builds, got: {build['status']}"
                )
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_total_builds_is_unfiltered_count(self):
        """Bug 2: total_builds should be the total count before any filtering."""
        import tools

        tmpdir = self._make_temp_repo()
        try:
            # Get unfiltered total
            data_all = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir)
            ))
            total_all = data_all["total_builds"]

            # Get filtered by status
            data_filtered = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir, status="failed")
            ))
            total_filtered = data_filtered["total_builds"]

            assert total_filtered == total_all, (
                f"total_builds should be {total_all} regardless of filters, "
                f"but got {total_filtered} when filtering by status='failed'"
            )
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_no_mutation_between_calls(self):
        """Bug 3: calling get_build_history twice should return the same data."""
        import tools

        tmpdir = self._make_temp_repo()
        try:
            data1 = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir)
            ))
            # Clear cache to force re-computation
            tools._cache._store.clear()
            data2 = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir)
            ))

            assert data1["results"] == data2["results"], (
                "Results differ between calls — BUILDS may be mutated"
            )
            assert data1["total_builds"] == data2["total_builds"]
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_status_filter_success(self):
        """Filtering by status='success' should return only successful builds."""
        import tools

        tmpdir = self._make_temp_repo()
        try:
            data = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir, status="success")
            ))
            for build in data["results"]:
                assert build["status"] == "success", (
                    f"Expected only success builds, got: {build['status']}"
                )
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_branch_filter(self):
        """Filtering by branch should return only builds for that branch."""
        import tools

        tmpdir = self._make_temp_repo()
        try:
            data = self._json(asyncio.run(
                tools.get_build_history(repo_path=tmpdir, branch="main")
            ))
            for build in data["results"]:
                assert build["branch"] == "main", (
                    f"Expected only main builds, got: {build['branch']}"
                )
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Existing Tool Tests ────────────────────────────────────────────────────


class TestExistingTools:
    """Verify the tools from previous lessons still work."""

    @pytest.fixture(autouse=True)
    def setup(self):
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)

    def test_analyze_hotspots_with_mock(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, top_n=10)

        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["file"] == "src/auth.py"
        assert results[0]["risk_score"] == 6

    def test_error_handling_nonexistent_path(self):
        from mcp.shared.exceptions import McpError
        import tools

        with pytest.raises(McpError):
            asyncio.run(tools.analyze_hotspots(repo_path="/nonexistent/path"))

    def test_error_handling_not_git_repo(self, tmp_path):
        from mcp.shared.exceptions import McpError
        import tools

        with pytest.raises(McpError):
            asyncio.run(tools.analyze_hotspots(repo_path=str(tmp_path)))


# ─── In-repo Test Suite Exists ───────────────────────────────────────────────


class TestInRepoTests:
    """Verify the expected_output includes its own test suite."""

    def test_conftest_exists(self):
        assert file_exists("tests/conftest.py"), "tests/conftest.py must exist"

    def test_test_analysis_exists(self):
        assert file_exists("tests/test_analysis.py"), "tests/test_analysis.py must exist"

    def test_test_tools_exists(self):
        assert file_exists("tests/test_tools.py"), "tests/test_tools.py must exist"
