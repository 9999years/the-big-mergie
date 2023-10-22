from .data import commits_old_to_new

from .util import IGNORE_RENAME_COMMITS


def main() -> None:
    #  data = data_for_all_repos()
    #  author_committer_deltas = []
    #  all_repos: dict[str, dict[str, Commit] | None] = {
    #  repo.repository: None for repo in data
    #  }
    #  for repo in data:
    #  commits = {commit.hash: commit for commit in repo.commits}
    #  all_repos[repo.repository] = commits

    #  different_dates = 0

    #  for commit in repo.commits:
    #  if commit.author_date != commit.commit_date:
    #  author_committer_deltas.append(
    #  (commit, commit.commit_date - commit.author_date, repo.repository)
    #  )
    #  different_dates += 1

    #  print(
    #  repo.repository,
    #  len(repo.commits),
    #  "commits",
    #  )

    #  in_both = []
    #  for hash, commit in cast(dict[str, Commit], all_repos["nix-config"]).items():
    #  if hash in cast(dict[str, Commit], all_repos["configuration"]):
    #  in_both.append(hash)

    #  print(len(in_both), "in both repos")

    #  author_committer_deltas.sort(key=lambda t: t[1])

    #  for delta in author_committer_deltas:
    #  commit, delta, repo = delta
    #  #  print(repo, delta, commit.hash)

    commits = commits_old_to_new()
    created = 0
    renamed = 0
    for commit in commits:
        if commit.renamed_any_files() and commit.hash not in IGNORE_RENAME_COMMITS:
            print("=" * 80)
            print(commit.show)
            renamed += 1
    #  print(created, "commits created files")
    print(renamed, "commits renamed files")


if __name__ == "__main__":
    main()
