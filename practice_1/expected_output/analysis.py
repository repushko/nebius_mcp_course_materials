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


def analyze_commit_patterns(
    repo: GitRepository, days: int = 30, author: str | None = None
) -> dict:
    commits = repo.get_commits(days=days)

    by_day: dict[str, int] = defaultdict(int)
    by_hour: dict[int, int] = defaultdict(int)
    commit_sizes: list[int] = []
    authors: dict[str, int] = defaultdict(int)

    for commit in commits:
        email = commit.author.email
        if author and email != author:
            continue

        changed_files = repo.get_changed_files(commit)
        commit_sizes.append(len(changed_files))
        authors[email] += 1

        if hasattr(commit, "committed_datetime"):
            dt = commit.committed_datetime
            by_day[dt.strftime("%A")] += 1
            by_hour[dt.hour] += 1

    total = len(commit_sizes)
    avg_size = sum(commit_sizes) / total if total else 0

    return {
        "total_commits": total,
        "by_day_of_week": dict(by_day),
        "by_hour": {str(k): v for k, v in sorted(by_hour.items())},
        "avg_files_per_commit": round(avg_size, 2),
        "max_files_in_commit": max(commit_sizes) if commit_sizes else 0,
        "authors": dict(authors),
    }
