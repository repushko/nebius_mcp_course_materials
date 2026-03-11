"""
Stub for unit tests and demos.
Swap GitRepository for MockGitRepository to work without a real git repo.

TODO: Add adapters for GitHub API, GitLab, Jira, or a database here
      when replacing mock data with real integrations.
"""
from dataclasses import dataclass, field


@dataclass
class MockAuthor:
    email: str


@dataclass
class MockCommit:
    author: MockAuthor
    changed_files: list[str] = field(default_factory=list)


class MockGitRepository:
    def __init__(self, commits: list[MockCommit]):
        self._commits = commits

    def get_commits(self, days: int) -> list[MockCommit]:
        return self._commits

    def get_changed_files(self, commit: MockCommit) -> list[str]:
        return commit.changed_files


SAMPLE_COMMITS = [
    MockCommit(MockAuthor("alice@example.com"), ["src/auth.py", "src/models.py"]),
    MockCommit(MockAuthor("bob@example.com"), ["src/auth.py", "tests/test_auth.py"]),
    MockCommit(MockAuthor("alice@example.com"), ["src/auth.py"]),
    MockCommit(MockAuthor("carol@example.com"), ["src/models.py", "src/api.py"]),
]
