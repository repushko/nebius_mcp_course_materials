from datetime import datetime, timedelta, timezone

import git


class GitRepository:
    def __init__(self, path: str):
        self.repo = git.Repo(path)

    def get_commits(self, days: int) -> list[git.Commit]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return list(self.repo.iter_commits(since=since.strftime("%Y-%m-%d")))

    def get_changed_files(self, commit: git.Commit) -> list[str]:
        if not commit.parents:
            return []
        return [d.b_path or d.a_path for d in commit.parents[0].diff(commit)]
