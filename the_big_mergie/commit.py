from datetime import datetime
from dataclasses import dataclass
import re
import functools

from .util import bash

NEW_FILE_RE = re.compile(r"\(new( ?[+-]l)?( ?[+-]x)?\)")


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
        return f"{self.abbrhash} from {self.repository} ({self.subject})"

    def show_patch(self):
        bash(
            f"""
            git show --oneline {self.hash} | delta | head -n15
            """,
            cwd=self.repository,
        )

    def show_oneline(self):
        bash(
            f"""
            git show --no-patch --oneline {self.hash}
            """,
            options="e",
            cwd=self.repository,
        )

    @functools.cached_property
    def subject(self) -> str:
        return bash(
            f"git show --no-patch --format='format:%s' {self.hash}",
            options=None,
            capture_output=True,
            text=True,
            cwd=self.repository,
        ).stdout

    def is_merge_commit(self) -> bool:
        return (
            bash(
                f"git rev-parse {self.hash}^2 >/dev/null 2>/dev/null",
                check=False,
                cwd=self.repository,
                options=None,
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

    @functools.cached_property
    def show(self) -> str:
        return bash(
            f"git show --stat --compact-summary {self.hash}",
            capture_output=True,
            cwd=self.repository,
            text=True,
        ).stdout

    @functools.cached_property
    def compact_summary(self) -> str:
        return bash(
            f"git show --stat=500,490 --compact-summary --format='' {self.hash}",
            capture_output=True,
            cwd=self.repository,
            text=True,
        ).stdout

    @functools.cached_property
    def nice_compact_summary(self) -> str:
        ret = []
        for line in self.compact_summary.splitlines():
            if "|" in line:
                tokens = line.split("|")
                ret.append(tokens[0].strip())
            else:
                ret.append(line)
        return "\n".join(ret)

    def created_any_files(self) -> bool:
        for line in self.compact_summary.splitlines():
            if NEW_FILE_RE.search(line):
                return True
        return False

    def renamed_any_files(self) -> bool:
        for line in self.compact_summary.splitlines():
            if " => " in line:
                return True
        return False


@dataclass
class Commits:
    repository: str
    commits: list[Commit]
