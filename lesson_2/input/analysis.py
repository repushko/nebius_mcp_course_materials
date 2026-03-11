from collections import defaultdict

from git_utils import GitRepository


def analyze_hotspots(repo: GitRepository, days: int = 90, limit: int = 10) -> list[dict]:
    commits = repo.get_commits(days=days)

    file_authors: dict[str, set] = defaultdict(set)
    file_changes: dict[str, int] = defaultdict(int)

    for commit in commits:
        for file in repo.get_changed_files(commit):
            file_authors[file].add(commit.author.email)
            file_changes[file] += 1

    results = [
        {
            "file": file,
            "authors": len(file_authors[file]),
            "changes": file_changes[file],
            "risk_score": len(file_authors[file]) * file_changes[file],
        }
        for file in file_changes
    ]

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results[:limit]
