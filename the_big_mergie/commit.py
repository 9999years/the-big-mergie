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

    def get_patch(self) -> bytes:
        fname = f"../data/{self.repository}.patch"
        return bash(
            rf"""
            rm -f {fname}
            if git rev-parse {self.hash}^2 >/dev/null 2>/dev/null; then
                git diff-tree -p -c {self.hash} > {fname}
            else
                git diff {self.hash}^! > {fname}
            fi

            lsdiff {fname} \
                | sort -u \
                | sed -e 's/[*?]/\\&/g' \
                | xargs -I! filterdiff --include=! --clean {fname} \
                | grep -e '^[-+@]' \
                | grep -v '^---' \
                | grep -v '^+++' \
                | sed 's/ @@@ .*//'
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
