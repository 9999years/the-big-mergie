import subprocess

from .statistics import ALL_REPOS, data_for_all_repos, Commit

RESULT_REPO = "the_cake"


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
    subprocess.run(
        [
            "bash",
            "-c",
            f"rm -rf {RESULT_REPO}"
            + f" && mkdir {RESULT_REPO}"
            + f" && cd {RESULT_REPO}"
            + " && git init .",
        ],
        check=True,
    )
    for repo in ALL_REPOS:
        subprocess.run(
            [
                "bash",
                "-c",
                f"cd {RESULT_REPO}"
                + " && git remote add "
                + repo
                + "../"
                + repo
                + " && git fetch "
                + repo,
            ],
            check=True,
        )


def finish_up():
    subprocess.run(
        [
            "bash",
            "-c",
            f"cd {RESULT_REPO}"
            + " && FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --env-filter 'export GIT_COMMITTER_DATE=\"$GIT_AUTHOR_DATE\"'",
        ]
    )


def main():
    diff_hashes = set()
    commits = commits_old_to_new()
    print(len(commits), "commits")
    init_repo()
    print("repo initialized")
    i = 0
    for commit in commits:
        i += 1
        print(commit.hash, "in", commit.repository, "=" * 30)
        print(i, "/", len(commits), "=", format(i / len(commits), ".2%"))
        patch = commit.get_patch()
        if not patch:
            print("skipping empty commit")
            continue
        patch_hash = hash(patch)
        if patch_hash in diff_hashes:
            print(
                "skipping",
                commit.hash,
                "from",
                commit.repository,
                "\t",
                commit.author_date,
            )
            continue
        else:
            #  print(
            #  "applying",
            #  commit.hash,
            #  "from",
            #  commit.repository,
            #  "\t",
            #  commit.author_date,
            #  )
            diff_hashes.add(patch_hash)
            try:
                commit.apply_to(RESULT_REPO)
            except subprocess.CalledProcessError:
                print("Fix the conflicts and exit to continue!")
                subprocess.run(["fish"], cwd=RESULT_REPO, check=True)
                subprocess.run(
                    ["bash", "-c", "git am --continue"], cwd=RESULT_REPO, check=True
                )
    finish_up()


if __name__ == "__main__":
    main()
