from pathlib import Path
from datetime import datetime

from .commit import Commit, Commits
from .util import ALL_REPOS


def read_data(repository: str) -> Commits:
    commits: list[Commit] = []

    with open(Path("data") / (repository + ".log")) as repo_file:
        for line in repo_file.readlines():
            hash, author_date, commit_date = line.split()
            author_date = datetime.fromisoformat(author_date)
            commit_date = datetime.fromisoformat(commit_date)
            commits.append(
                Commit(
                    hash=hash,
                    author_date=author_date,
                    commit_date=commit_date,
                    repository=repository,
                )
            )

    return Commits(commits=commits, repository=repository)


def data_for_repos(repos: list[str]) -> list[Commits]:
    ret: list[Commits] = []

    for repo in repos:
        data = read_data(repo)
        ret.append(data)

    return ret


def data_for_all_repos():
    return data_for_repos(ALL_REPOS)


def commits_old_to_new() -> list[Commit]:
    data = data_for_all_repos()
    all_commits: list[Commit] = []
    for repo in data:
        if repo.repository == "configuration":
            # Only the first few commits are unique.
            for commit in repo.commits:
                all_commits.append(commit)
                if commit.hash == "b21f4191e24d28b2ba70b26a00965206ac855e8d":
                    # This is the last unique commit.
                    break
        else:
            all_commits.extend(repo.commits)

    all_commits.sort(key=lambda commit: commit.author_date)

    return all_commits


def chunks_by_repository(commits: list[Commit]) -> list[list[Commit]]:
    last_repo = None
    chunks: list[list[Commit]] = []
    chunk: list[Commit] = []
    for commit in commits:
        chunk.append(commit)
        if last_repo is None:
            last_repo = commit.repository
        elif commit.repository != last_repo:
            chunks.append(chunk)
            chunk = []
            last_repo = commit.repository
    chunks.append(chunk)
    return chunks
