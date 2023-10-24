"""
Ideas:
- group commits into chunk by the dag finding chokepoints where all the commits
  in the chunk share one minimal common ancestor
- multi-phase rebase:
  1. rename paths
  2. join repositories together and interleave chunks
"""

import subprocess
import argparse
from collections import deque, defaultdict
from typing import DefaultDict

from .commit import Commit
from .data import chunks_by_repository, commits_old_to_new
from .util import ALL_REPOS, RERE_CACHE, RESULT_REPO, bash, RERE_CACHE
from .color import BRIGHT_CYAN, CYAN, BOLD, RESET, RED


def check_chunks():
    chunks = chunks_by_repository(commits_old_to_new())

    merge_commits = 0

    for _, chunk in enumerate(chunks):
        if len(chunk) == 1:
            print("{", chunk[0], "}")
        elif len(chunk) == 2:
            print("{", chunk[0])
            print(" ", chunk[-1], "}")
        elif len(chunk) == 3:
            print("{", chunk[0])
            print(" ", chunk[1])
            print(" ", chunk[-1], "}")
        else:
            print("{", chunk[0])
            print(" ", f"... {len(chunk) - 2} ...")
            print(" ", chunk[-1], "}")
        for commit in chunk:
            if commit.is_merge_commit:
                merge_commits += 1
        input()

    print(merge_commits, "merge commits")


def walk_chunks(repo):
    # Chunks start with a commit with one parent.
    # Chunks end with the first commit

    # Hashes to hashes.
    parents: DefaultDict[Commit, set[Commit]] = defaultdict(set)
    children: DefaultDict[Commit, set[Commit]] = defaultdict(set)

    chunk_starts: set[Commit] = set()

    head = Commit.from_repo_rev(repo=repo)
    print("main is", head)

    commits: deque[Commit] = deque([head])
    seen: set[Commit] = {head}
    i = 0

    while commits:
        i += 1

        commit = commits.pop()
        if i % 100:
            print("Working on commit", commit.hash, "seen", len(seen))
        seen.add(commit)
        commits.extend(commit for commit in commit.parents if commit not in seen)

        parents[commit].update(commit.parents)
        for parent in commit.parents:
            children[parent].add(commit)

        if len(commit.parents) == 1:
            chunk_starts.add(commit)

    print("Found", len(chunk_starts), "chunk starts from", len(seen), "commits")

    for start in chunk_starts:
        seen = {start}
        commits.clear()
        commits.append(start)

        while commits:
            commit = commits.pop()
            seen.add(commit)
            commits.extend(
                commit for commit in children[commit] if commit.hash not in seen
            )

            # uhh
            # so how do we detect a chunk end?


def init_repo():
    bash(
        rf"""
        rm -rf {RESULT_REPO}
        mkdir {RESULT_REPO}
        cd {RESULT_REPO} || exit 1
        git init .
        git switch --orphan rerere-training
        git commit --allow-empty -m "Train rerere cache"
        """
    )
    for repo in ALL_REPOS:
        print(f"{CYAN}Initializing {repo}{RESET}")
        bash(
            rf"""
            git remote add {repo} ../{repo}
            git fetch {repo}
            ../rerere-train.sh remotes/{repo}/main
            """,
            cwd=RESULT_REPO,
            capture_output=True,
        )
    bash(
        rf"""
        git switch --no-guess --orphan main
        """,
        cwd=RESULT_REPO,
    )


def save_rerere():
    print(f"{CYAN}Saving rerere cache{RESET}")
    bash(
        rf"""
        if [[ ! -d {RERE_CACHE} ]]; then
            mkdir -p {RERE_CACHE}
            pushd {RERE_CACHE} || exit 1
            git init .
            git remote add {RESULT_REPO} ../../{RESULT_REPO}
            git fetch {RESULT_REPO}
            popd || exit 1
        fi
        cd {RERE_CACHE} || exit 1
        ../../rerere-train.sh remotes/{RESULT_REPO}/main
        """
    )


def finish_up():
    bash(
        rf"""
        export FILTER_BRANCH_SQUELCH_WARNING=1
        git filter-branch \
            --env-filter 'export GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"'
        """,
        cwd=RESULT_REPO,
    )


def on_conflict(commit: Commit):
    print(
        f"{BOLD}{RED}Failure applying {commit.abbrhash} from {commit.repository}{RESET}"
    )
    bash(
        rf"""
        git am --show-current-patch=diff
        """,
        cwd=RESULT_REPO,
    )
    while True:
        response = input(f"{BOLD}{CYAN}fix, quit, skip? {RESET}").lower()
        if response.startswith("f"):
            subprocess.run(["fish"], cwd=RESULT_REPO, check=True)
            result = bash("git am --continue", cwd=RESULT_REPO, check=False)
            if result.returncode != 0:
                print(f"{BOLD}{CYAN}Couldn't continue, did something go wrong?{RESET}")
            else:
                break
        elif response.startswith("q"):
            raise RuntimeError("quit")
        elif response.startswith("s"):
            bash("git am --skip", cwd=RESULT_REPO)
            break
        else:
            print("Uhh idk what to do with that sry haha")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--continue", action="store", dest="continue_hash")
    parser.add_argument("--chunks", action="store_true")
    parser.add_argument("--no-init", action="store_false", dest="init")
    args = parser.parse_args()

    if args.chunks:
        #  check_chunks()
        walk_chunks("dotfiles")
        return

    commits = commits_old_to_new()
    print(len(commits), "commits")

    if args.continue_hash:
        all_commits = commits
        commits = []
        found_commit = False
        for commit in all_commits:
            if found_commit:
                commits.append(commit)
            elif commit.hash == args.continue_hash:
                found_commit = True
    else:
        if args.init:
            init_repo()
            print("Repo initialized")

    total_commits = len(commits)

    i = 0
    for commit in commits:
        i += 1
        print(
            f"{BRIGHT_CYAN}{BOLD}{commit}{RESET} {CYAN}{i}/{total_commits}",
            "=",
            f"{format(i / len(commits), '.2%')}",
            f"{BOLD}{'=' * 30}{RESET}",
        )

        try:
            with open("data/commit", "w") as commit_file:
                commit_file.write(commit.hash)
            bash(f"git cherry-pick --allow-empty -m 1 {commit.hash}", cwd=RESULT_REPO)
        except subprocess.CalledProcessError:
            on_conflict(commit)

    finish_up()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        save_rerere()
        #  print(e)
        raise
