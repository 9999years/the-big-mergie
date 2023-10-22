from datetime import datetime
from dataclasses import dataclass

from .util import bash


@dataclass
class Commit:
    hash: str
    author_date: datetime
    commit_date: datetime
    repository: str

    @property
    def abbrhash(self) -> str:
        return self.hash[:8]

    def __str__(self) -> str:
        return f"{self.abbrhash} from {self.repository}"

    def show_patch(self):
        bash(
            f"""
            git show --oneline {self.hash} | delta | head -n15
            """,
            cwd=self.repository,
        )

    def is_merge_commit(self) -> bool:
        return (
            bash(
                f"git rev-parse {self.hash}^2 >/dev/null 2>/dev/null", check=False
            ).returncode
            == 0
        )

    def get_patch(self) -> bytes:
        return bash(
            rf"""
            if git rev-parse {self.hash}^2 >/dev/null 2>/dev/null; then
                git diff-tree -p -c {self.hash}
            else
                git diff {self.hash}^!
            fi
            """,
            cwd=self.repository,
            capture_output=True,
        ).stdout

    def apply_to(self, other_repository: str):
        bash(
            rf"""
            git format-patch -1 {self.hash} --stdout \
                | ( cd ../{other_repository} \
                    && git am --ignore-whitespace -3 \
                )
            """,
            cwd=self.repository,
            capture_output=True,
        )


@dataclass
class Commits:
    repository: str
    commits: list[Commit]
