import subprocess
import argparse

from .statistics import data_for_all_repos, Commit
from .util import ALL_REPOS, RERE_CACHE, RESULT_REPO, bash, RERE_CACHE
from .color import BRIGHT_CYAN, CYAN, BOLD, RESET, RED


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
        cd {RESULT_REPO} || exit 1
        git init .
        git switch -c rerere-training
        """
    )
    for repo in ALL_REPOS:
        bash(
            rf"""
            echo "Initializing {repo}"
            git remote add {repo} ../{repo}
            git fetch {repo}
            ../rerere-train.sh remotes/{repo}/main >/dev/null 2>&1
            """,
            cwd=RESULT_REPO,
        )
    bash(
        rf"""
        git switch main
        git log --oneline --graph
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
            break
        elif response.startswith("q"):
            raise RuntimeError
        elif response.startswith("s"):
            bash("git am --skip", cwd=RESULT_REPO)
            break
        else:
            print("Uhh idk what to do with that sry haha")


def save_rerere():
    bash(
        rf"""
        if [[ ! -d {RERE_CACHE} ]]; then
            mkdir -p {RERE_CACHE}
            pushd {RERE_CACHE} || exit 1
            git init .
            popd || exit 1
        fi
        cd {RERE_CACHE} || exit 1
        ../../rerere-train.sh main
        """
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--continue", action="store", dest="continue_hash")
    args = parser.parse_args()

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
        init_repo()
        print("Repo initialized")

    total_commits = len(commits)
    skipped = 0

    i = 0
    for commit in commits:
        i += 1
        print(
            f"{BRIGHT_CYAN}{BOLD}{commit}{RESET} {CYAN}{i}/{total_commits}",
            "=",
            f"{format((i - skipped) / len(commits), '.2%')},",
            "skipped",
            skipped,
            f"{BOLD}{'=' * 30}{RESET}",
        )

        patch = commit.get_patch()
        if not patch:
            print(f"{BRIGHT_CYAN}{BOLD}Skipping empty commit {commit}{RESET}")
            skipped += 1
            continue

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
        save_rerere()
        print(str(e))
