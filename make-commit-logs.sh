#!/usr/bin/env bash

git=(git -c core.pager=cat)
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

repos=(configuration dotfiles nix-config old-vimfiles)
for repo in "${repos[@]}"; do
    echo "--> $repo"
    pushd "$repo" >/dev/null || exit

    "${git[@]}" log \
        --format="format:%H %aI %cI %(describe)" \
        > "$scriptDir/data/$repo.log"

    popd >/dev/null || exit
done
