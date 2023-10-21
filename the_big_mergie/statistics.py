from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import cast
import subprocess
import tempfile

ALL_REPOS = ["configuration", "dotfiles", "nix-config", "old-vimfiles"]


@dataclass
class Commit:
    hash: str
    author_date: datetime
    commit_date: datetime
    repository: str

    def show_patch(self):
        subprocess.run(
            [
                "bash",
                "-c",
                "cd "
                + self.repository
                + " && git show --oneline "
                + self.hash
                + " | delta | head -n15",
            ],
            check=True,
        )

    def get_patch(self):
        return subprocess.run(
            [
                "bash",
                "-c",
                "set -ev\n cd "
                + self.repository
                + " && rm -f xxx-patch\n "
                + "if git rev-parse "
                + self.hash
                + "^2 >/dev/null 2>/dev/null\n then\n "
                + "  git diff-tree -p "
                + self.hash
                + " > xxx-patch\n "
                + "else\n"
                + "  git diff "
                + self.hash
                + "^! > xxx-patch\n "
                + "fi\n "
                + "lsdiff xxx-patch"
                + " | sort -u"
                + r" | sed -e 's/[*?]/\\&/g'"
                + " | xargs -I{} filterdiff --include={} --clean xxx-patch",
            ],
            capture_output=True,
            check=True,
        ).stdout

    def apply_to(self, path: str):
        patch = subprocess.run(
            [
                "bash",
                "-c",
                "cd "
                + self.repository
                + " && git format-patch -1 "
                + self.hash
                + " --stdout",
            ],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [
                "bash",
                "-c",
                "set -e\ncd "
                + path
                + "\nif git am\nthen\nexit 0\nelse\ngit am --show-current-patch=diff\nexit 1\nfi",
            ],
            check=True,
            input=patch.stdout,
        )


@dataclass
class Commits:
    repository: str
    commits: list[Commit]


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


def main() -> None:
    data = data_for_all_repos()
    author_committer_deltas = []
    all_repos: dict[str, dict[str, Commit] | None] = {
        repo.repository: None for repo in data
    }
    for repo in data:
        commits = {commit.hash: commit for commit in repo.commits}
        all_repos[repo.repository] = commits

        different_dates = 0

        for commit in repo.commits:
            if commit.author_date != commit.commit_date:
                author_committer_deltas.append(
                    (commit, commit.commit_date - commit.author_date, repo.repository)
                )
                different_dates += 1

        print(
            repo.repository,
            len(repo.commits),
            "commits",
        )

    in_both = []
    for hash, commit in cast(dict[str, Commit], all_repos["nix-config"]).items():
        if hash in cast(dict[str, Commit], all_repos["configuration"]):
            in_both.append(hash)

    print(len(in_both), "in both repos")

    author_committer_deltas.sort(key=lambda t: t[1])

    for delta in author_committer_deltas:
        commit, delta, repo = delta
        #  print(repo, delta, commit.hash)


if __name__ == "__main__":
    main()
