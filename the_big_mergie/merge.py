import subprocess

from .statistics import data_for_all_repos, Commit
from .util import ALL_REPOS, RESULT_REPO, bash
from .color import BRIGHT_CYAN, CYAN, BOLD, RESET


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


def check_chunks():
    chunks = chunks_by_repository(commits_old_to_new())

    for chunk in chunks:
        if len(chunk) < 10:
            c = chunk[0]
            print(c.repository.upper(), "=" * (59 - len(c.repository)))
            for c in chunk:
                delta = ""
                if c.author_date != c.commit_date:
                    delta = "(" + str(c.commit_date - c.author_date) + ")"
                print(c.hash[:8], c.author_date, delta)
                c.show_patch()
        else:
            print("chunk:", len(chunk), "\t", chunk[0].repository)


def init_repo():
    bash(
        rf"""
        rm -rf {RESULT_REPO}
        mkdir {RESULT_REPO}
        cd {RESULT_REPO}
        git init .
        """
    )
    for repo in ALL_REPOS:
        bash(
            rf"""
            echo "Initializing {repo}"
            git remote add {repo} ../{repo}
            git fetch {repo}
            ../rerere-train.sh remotes/{repo}/main 2>1&>/dev/null
            """,
            cwd=RESULT_REPO,
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
    bash(
        rf"""
        git am --show-current-patch=diff
        """,
        cwd=RESULT_REPO,
    )
    #  subprocess.run(["fish"], cwd=RESULT_REPO, check=True)
    #  subprocess.run(
    #  ["bash", "-c", "git am --continue"], cwd=RESULT_REPO, check=True
    #  )


def main():
    applied_commits: dict[int, Commit] = {}
    commits = commits_old_to_new()
    print(len(commits), "commits")
    init_repo()
    print("repo initialized")
    i = 0
    for commit in commits:
        i += 1
        #  print(
        #  f"{BRIGHT_CYAN}{BOLD}{commit.hash} in {commit.repository} {'=' * 30}{RESET}"
        #  )
        #  print(f"{CYAN}{i}/{len(commits)} = {format(i / len(commits), '.2%')}{RESET}")

        patch = commit.get_patch()
        if not patch:
            print(
                f"{BRIGHT_CYAN}{BOLD}Skipping empty commit {commit.hash} in {commit.repository}{RESET}"
            )
            continue
        patch_hash = hash(patch)

        if patch_hash in applied_commits:
            print(
                f"{BRIGHT_CYAN}{BOLD}Skipping already applied commit {commit.hash} in {commit.repository}{RESET}"
            )
            equiv = applied_commits[patch_hash]
            print(
                f"{BRIGHT_CYAN}{BOLD}Equivalent to {equiv.hash} in {equiv.repository}{RESET}"
            )
            continue

        applied_commits[patch_hash] = commit
        try:
            commit.apply_to(RESULT_REPO)
        except subprocess.CalledProcessError:
            on_conflict(commit)
            raise

    finish_up()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e))
