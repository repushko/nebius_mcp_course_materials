"""
Autotests for Lesson 1: Designing an MCP Interface.

These tests validate that the expected_output repo meets all submission criteria.
They can be run against any student submission by changing REPO_DIR.
"""
import ast
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


def get_decorator_names(func_def: ast.AsyncFunctionDef | ast.FunctionDef) -> list[str]:
    """Extract decorator call names like 'server.tool', 'server.resource', 'server.prompt'."""
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


def find_decorated_functions(tree: ast.Module, decorator_pattern: str) -> list[str]:
    """Find all async functions decorated with a pattern like 'server.tool'."""
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            for name in get_decorator_names(node):
                if name == decorator_pattern:
                    results.append(node.name)
    return results


# ─── Documentation Tests ────────────────────────────────────────────────────


class TestDocumentation:
    def test_interface_md_exists(self):
        assert file_exists("docs/interface.md"), "docs/interface.md must exist"

    def test_interface_has_questions(self):
        content = read_file("docs/interface.md").lower()
        assert "question" in content or "?" in content, (
            "docs/interface.md should contain host questions"
        )

    def test_interface_has_at_least_5_questions(self):
        content = read_file("docs/interface.md")
        question_count = content.count("?")
        assert question_count >= 5, (
            f"Expected at least 5 questions (found {question_count})"
        )

    def test_interface_has_data_sources(self):
        content = read_file("docs/interface.md").lower()
        required_sources = ["commit", "file", "author", "ci", "team", "ownership", "deployment"]
        found = [s for s in required_sources if s in content]
        assert len(found) >= 5, (
            f"Expected at least 5 of {required_sources} mentioned, found {found}"
        )

    def test_interface_has_mapping(self):
        content = read_file("docs/interface.md").lower()
        assert "resource" in content, "Mapping should mention 'resource'"
        assert "tool" in content, "Mapping should mention 'tool'"
        assert "prompt" in content, "Mapping should mention 'prompt'"


# ─── Resource Tests ─────────────────────────────────────────────────────────


class TestResources:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Parse all Python files to find resources
        self.all_resources = []
        for fname in os.listdir(REPO_DIR):
            if fname.endswith(".py"):
                tree = parse_python(fname)
                self.all_resources.extend(
                    find_decorated_functions(tree, "server.resource")
                )

    def test_at_least_3_resources(self):
        assert len(self.all_resources) >= 3, (
            f"Expected at least 3 resources, found {len(self.all_resources)}: {self.all_resources}"
        )

    def test_resource_uris_in_code(self):
        """Check that resource URIs follow the git-activity:// scheme."""
        found_uris = []
        for fname in os.listdir(REPO_DIR):
            if fname.endswith(".py"):
                content = read_file(fname)
                import re
                uris = re.findall(r'git-activity://\S+', content)
                found_uris.extend(uris)
        assert len(found_uris) >= 3, (
            f"Expected at least 3 git-activity:// URIs, found {len(found_uris)}"
        )


# ─── Tool Tests ──────────────────────────────────────────────────────────────


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.all_tools = []
        for fname in os.listdir(REPO_DIR):
            if fname.endswith(".py"):
                tree = parse_python(fname)
                self.all_tools.extend(
                    find_decorated_functions(tree, "server.tool")
                )

    def test_at_least_2_tools(self):
        assert len(self.all_tools) >= 2, (
            f"Expected at least 2 tools, found {len(self.all_tools)}: {self.all_tools}"
        )

    def test_analyze_hotspots_exists(self):
        assert "analyze_hotspots" in self.all_tools, (
            f"Tool 'analyze_hotspots' not found. Found: {self.all_tools}"
        )

    def test_analyze_commit_patterns_exists(self):
        assert "analyze_commit_patterns" in self.all_tools, (
            f"Tool 'analyze_commit_patterns' not found. Found: {self.all_tools}"
        )

    def _find_tool_params(self, tool_name: str) -> list[str] | None:
        """Find parameters of a @server.tool() decorated function by name."""
        for fname in os.listdir(REPO_DIR):
            if not fname.endswith(".py"):
                continue
            tree = parse_python(fname)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if node.name != tool_name:
                    continue
                decorators = get_decorator_names(node)
                if "server.tool" in decorators:
                    return [arg.arg for arg in node.args.args]
        return None

    def test_analyze_hotspots_has_repo_path_param(self):
        """The analyze_hotspots tool must accept repo_path."""
        params = self._find_tool_params("analyze_hotspots")
        assert params is not None, "analyze_hotspots @server.tool() not found"
        assert "repo_path" in params, (
            f"analyze_hotspots must have 'repo_path' parameter, found: {params}"
        )

    def test_analyze_commit_patterns_has_repo_path_param(self):
        """The analyze_commit_patterns tool must accept repo_path."""
        params = self._find_tool_params("analyze_commit_patterns")
        assert params is not None, "analyze_commit_patterns @server.tool() not found"
        assert "repo_path" in params, (
            f"analyze_commit_patterns must have 'repo_path' parameter, found: {params}"
        )


# ─── Prompt Tests ────────────────────────────────────────────────────────────


class TestPrompts:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.all_prompts = []
        for fname in os.listdir(REPO_DIR):
            if fname.endswith(".py"):
                tree = parse_python(fname)
                self.all_prompts.extend(
                    find_decorated_functions(tree, "server.prompt")
                )

    def test_at_least_1_prompt(self):
        assert len(self.all_prompts) >= 1, (
            f"Expected at least 1 prompt, found {len(self.all_prompts)}: {self.all_prompts}"
        )

    def test_prompt_references_tools(self):
        """The prompt template should reference at least one tool by name."""
        for fname in os.listdir(REPO_DIR):
            if not fname.endswith(".py"):
                continue
            tree = parse_python(fname)
            for node in ast.walk(tree):
                if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    if node.name in self.all_prompts:
                        source = read_file(fname)
                        # Check if the prompt body mentions tool names
                        if "analyze_hotspots" in source or "analyze_commit_patterns" in source:
                            return
        pytest.fail("Prompt template should reference at least one tool name")


# ─── Security Tests ─────────────────────────────────────────────────────────


class TestSecurity:
    def test_allowed_repos_config_exists(self):
        assert file_exists("config/allowed_repos.json"), (
            "config/allowed_repos.json must exist"
        )

    def test_allowed_repos_has_entries(self):
        content = json.loads(read_file("config/allowed_repos.json"))
        repos = content.get("allowed_repos", [])
        assert len(repos) >= 1, (
            "config/allowed_repos.json must have at least 1 allowed repo path"
        )

    def test_repo_path_validation_exists(self):
        """Some Python file should contain path validation logic."""
        found_validation = False
        for fname in os.listdir(REPO_DIR):
            if not fname.endswith(".py"):
                continue
            content = read_file(fname)
            if "validate_repo_path" in content or "allowed_repos" in content:
                found_validation = True
                break
        assert found_validation, (
            "No repo_path validation found in any Python file"
        )

    def test_path_traversal_protection(self):
        """Some Python file should block ../ path traversal."""
        found_traversal_check = False
        for fname in os.listdir(REPO_DIR):
            if not fname.endswith(".py"):
                continue
            content = read_file(fname)
            if "../" in content or "traversal" in content.lower() or "validate_file_path" in content:
                found_traversal_check = True
                break
        assert found_traversal_check, (
            "No path traversal protection found in any Python file"
        )

    def test_auth_placeholder(self):
        """Server should have an auth TODO or implementation."""
        found_auth = False
        for fname in os.listdir(REPO_DIR):
            if not fname.endswith(".py"):
                continue
            content = read_file(fname).lower()
            if "jwt" in content or "api key" in content or "api_key" in content or "auth" in content:
                found_auth = True
                break
        assert found_auth, (
            "No auth placeholder (JWT/API key TODO or implementation) found"
        )


# ─── Functional Tests (using mock data) ─────────────────────────────────────


class TestFunctional:
    """Test that the analysis functions work correctly with mock data."""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Add the expected_output dir to sys.path so we can import
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)

    def test_analyze_hotspots_with_mock(self):
        # Import from expected_output
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_hotspots

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_hotspots(repo, days=90, limit=10)

        assert isinstance(results, list)
        assert len(results) > 0

        # Check structure of results
        for item in results:
            assert "file" in item
            assert "authors" in item
            assert "changes" in item
            assert "risk_score" in item
            assert isinstance(item["risk_score"], int)

        # src/auth.py should be the top hotspot (3 changes, 2 authors)
        top = results[0]
        assert top["file"] == "src/auth.py"
        assert top["changes"] == 3
        assert top["authors"] == 2
        assert top["risk_score"] == 6

    def test_analyze_commit_patterns_with_mock(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_commit_patterns

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_commit_patterns(repo, days=90)

        assert isinstance(results, dict)
        assert "total_commits" in results
        assert results["total_commits"] == 4
        assert "avg_files_per_commit" in results
        assert "authors" in results
        assert len(results["authors"]) == 3  # alice, bob, carol

    def test_analyze_commit_patterns_author_filter(self):
        from mock_git_utils import MockGitRepository, SAMPLE_COMMITS
        from analysis import analyze_commit_patterns

        repo = MockGitRepository(SAMPLE_COMMITS)
        results = analyze_commit_patterns(repo, days=90, author="alice@example.com")

        assert results["total_commits"] == 2
        assert "alice@example.com" in results["authors"]
        assert len(results["authors"]) == 1

    def test_security_validate_repo_path_rejects_outside(self):
        from security import validate_repo_path
        with pytest.raises(ValueError, match="not inside any allowed"):
            validate_repo_path("/etc/passwd")

    def test_security_validate_file_path_blocks_traversal(self):
        from security import validate_file_path
        with pytest.raises(ValueError, match="traversal"):
            validate_file_path("/tmp/test-repo", "../../etc/passwd")

    def test_security_validate_file_path_allows_valid(self):
        """A path inside the repo should be accepted."""
        from security import validate_file_path
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            real_tmpdir = os.path.realpath(tmpdir)
            subfile = os.path.join(real_tmpdir, "src", "main.py")
            os.makedirs(os.path.dirname(subfile), exist_ok=True)
            with open(subfile, "w") as f:
                f.write("")
            result = validate_file_path(real_tmpdir, "src/main.py")
            assert result == subfile


# ─── Structure Tests ────────────────────────────────────────────────────────


class TestStructure:
    def test_server_py_exists(self):
        assert file_exists("server.py"), "server.py must exist"

    def test_app_py_exists(self):
        assert file_exists("app.py"), "app.py must exist"

    def test_app_creates_fastmcp(self):
        content = read_file("app.py")
        assert "FastMCP" in content, "app.py must use FastMCP"

    def test_tools_import_from_app(self):
        """tools.py must import server from app, not from server (avoids circular import)."""
        content = read_file("tools.py")
        assert "from app import server" in content, (
            "tools.py must use 'from app import server' to avoid circular imports"
        )

    def test_pyproject_toml_exists(self):
        assert file_exists("pyproject.toml"), "pyproject.toml must exist"

    def test_has_gitpython_dependency(self):
        content = read_file("pyproject.toml")
        assert "gitpython" in content.lower(), "pyproject.toml must list gitpython"

    def test_has_mcp_dependency(self):
        content = read_file("pyproject.toml")
        assert "mcp" in content.lower(), "pyproject.toml must list mcp"
