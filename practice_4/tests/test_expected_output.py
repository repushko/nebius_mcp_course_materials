"""
Lesson 4 autotests — validate that get_build_history bugs are fixed.

Tests run against the expected_output directory (added to sys.path via conftest).
Uses both AST-based static analysis and functional tests.
"""
import ast
import asyncio
import json
import os
import sys
import textwrap

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "expected_output")
TOOLS_PY = os.path.join(EXPECTED_OUTPUT, "tools.py")


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


# ---------------------------------------------------------------------------
# Structure: files exist
# ---------------------------------------------------------------------------

class TestStructure:
    def test_tools_py_exists(self):
        assert os.path.isfile(TOOLS_PY)

    def test_expected_output_has_app_py(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "app.py"))

    def test_expected_output_has_server_py(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "server.py"))

    def test_expected_output_has_analysis_py(self):
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "analysis.py"))

    def test_expected_output_has_in_repo_tests(self):
        assert os.path.isdir(os.path.join(EXPECTED_OUTPUT, "tests"))
        assert os.path.isfile(os.path.join(EXPECTED_OUTPUT, "tests", "test_tools.py"))


# ---------------------------------------------------------------------------
# Static analysis: the 3 bugs are fixed
# ---------------------------------------------------------------------------

class TestBugFixesStatic:
    """AST + source-level checks that the three bugs have been corrected."""

    def test_status_filter_uses_equality(self):
        """Bug 1: status filter must use == not !=."""
        source = open(TOOLS_PY).read()
        tree = ast.parse(source)
        func = _find_function(tree, "get_build_history")
        assert func is not None, "get_build_history not found"

        # Find comparisons in the function involving b["status"]
        for node in ast.walk(func):
            if isinstance(node, ast.ListComp):
                for gen in node.generators:
                    for if_clause in gen.ifs:
                        if isinstance(if_clause, ast.Compare):
                            # Check if this is a status comparison
                            source_segment = ast.get_source_segment(source, if_clause)
                            if source_segment and '"status"' in source_segment:
                                # Must use Eq, not NotEq
                                for op in if_clause.ops:
                                    assert not isinstance(op, ast.NotEq), (
                                        "Status filter uses != instead of =="
                                    )

    def test_total_builds_uses_full_dataset(self):
        """Bug 2: total_builds must reflect len(BUILDS) or be computed before filtering."""
        lines = _get_source_lines()
        func = _find_function(_parse_tools(), "get_build_history")
        assert func is not None

        # Get the source lines of the function
        func_lines = lines[func.lineno - 1 : func.end_lineno]
        func_source = "".join(func_lines)

        # total should reference BUILDS (the module-level constant) or be set before filtering
        # Find the line that sets total
        total_line_idx = None
        first_filter_line_idx = None
        for i, line in enumerate(func_lines):
            stripped = line.strip()
            if stripped.startswith("total") and "len(" in stripped:
                total_line_idx = i
            if first_filter_line_idx is None and ("branch" in stripped or "status" in stripped) and "builds = [" in stripped:
                first_filter_line_idx = i

        assert total_line_idx is not None, "Could not find total assignment"

        # Either total uses len(BUILDS) directly, or it's set before any filtering
        total_line = func_lines[total_line_idx].strip()
        uses_builds_constant = "len(BUILDS)" in total_line
        set_before_filtering = first_filter_line_idx is None or total_line_idx < first_filter_line_idx

        assert uses_builds_constant or set_before_filtering, (
            f"total_builds is computed after filtering. "
            f"total at line {total_line_idx}, first filter at line {first_filter_line_idx}"
        )

    def test_builds_uses_list_copy(self):
        """Bug 3: builds must be a copy of BUILDS, not a direct reference."""
        lines = _get_source_lines()
        func = _find_function(_parse_tools(), "get_build_history")
        assert func is not None

        func_lines = lines[func.lineno - 1 : func.end_lineno]

        # Find the first assignment to builds
        for line in func_lines:
            stripped = line.strip()
            if stripped.startswith("builds = ") and "BUILDS" in stripped:
                # Must use list() or [:] to copy
                assert "list(BUILDS)" in stripped or "BUILDS[:]" in stripped or "BUILDS.copy()" in stripped, (
                    f"builds is assigned directly from BUILDS without copying: {stripped}"
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

    def test_analyze_file_activity_still_works(self):
        data = self._json(asyncio.run(
            self.tools.analyze_file_activity(repo_path=self.temp_repo)
        ))
        assert "results" in data
        assert "total" in data


# ---------------------------------------------------------------------------
# In-repo tests exist and cover get_build_history
# ---------------------------------------------------------------------------

class TestInRepoTests:
    """Verify the expected_output ships its own tests for get_build_history."""

    def test_in_repo_test_tools_exists(self):
        path = os.path.join(EXPECTED_OUTPUT, "tests", "test_tools.py")
        assert os.path.isfile(path)

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
