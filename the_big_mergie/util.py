import subprocess
from .color import BRIGHT_RED, BOLD, RESET, DIM

ALL_REPOS = ["configuration", "dotfiles", "nix-config", "old-vimfiles"]
RESULT_REPO = "cake"
RERE_CACHE = "data/rerecache"

RENAME_COMMITS = {
    # migrate to vimfiles
    # vimfiles/... -> ...
    "572e7a182e10b815c1e736ce2e564a25b8921007",
    # chezmoi: rename files
    "11957ea3ae9786e92a5d6b93f9fa77d85ea12f33",
    # Use Chezmoi
    "08e45dbc7359baa0f2d7b3175d9d2d125fbd7a73",
    # Use rcm
    "dc749c8c45fe3f96e8bc7d6420ca551c6e54b85c",
}

# Hashes we can ignore, even though the commits rename files.
IGNORE_RENAME_COMMITS = set(
    """
    a113659af1a59bbccc6e0caa3f427b9e27137c77
    ba30d9cbf94b2f0a584a64c7291f84097ceba256
    31ebf33578d316a587ee4cb397e7ab3c6d0fb647
    149ae42af40305ba9521d2c089a32c293d2cc6e2
    a0d10855e9dc93837c4cfb52d61c0151ae2a01d3
    e267f7cf1cf9e2e051665c36adc56ad621d773f9
    783947316312bc25a6c6dd71a0cdcfe8647b0f18
    f6ec82122feb42797cc1932143f2fbfcee08d645
    b4e3b10f4c4c58969cb32264c0c1a7a4478bd384
    481b7ab023bc4f79ff1efc46093bf9cecd49707b
    b2c274250c835565bf99a59079874ae301778af0
    d603e8e61c778c4852898812f7c55738fa11ccfa
    6d1168213627d94e04c0bbbeaff4de9ef7f4f001
    7b501c4abbf404e7b967567103402e490f3ff6c4
    a3b2cd2febe884e06be54dfd6fa62cda49302c63
    5d8631b6e853d5da28d87c012f223adef3a12308
    50882b857f2cb16a728affda7a676a6068235583
    837b3c430fce9e9fa4ea25f1b8a7c0bb2828fb67
    4df4e184b43eef7d8da11d9017281d44a0fc37c2
    838b2e29724547c04e469eacf2e7c7277a661702
    9b9ebc970c2b65356397eb338d59af313a3c7361
    083c1e995afb6bbcabf4715b8345fd9048ced40b
    78d723f818b8f637e7ec3f127398f0daaf81760e
    eb1b1bdd9cdf849beb8f8b2b976c962c5b467889
    e8bf02fad6059c728dc2c91bd7638acd93d339a5
    943e1e1da081bd575c6dd8259249842cce57ff96
    850dbf30ed50ba8ac7cc16d01a5019c35b3d519a
    938aa37d560e21c824d260279b60891ae644a073
    7ff552e84c7af71c2b8fe04061b7365c2fcf6f0c
    fdae9daf9c9d13bd8a93f516b2fcbfe1e6b05250
    828f10be4868fbe380ad7f8aae7cd27bbfd155d4
    238569813806eb44446bab92e1751ee4273d628a
    65937d24ac8346de04f9d35a9004238dd1bb7754
    a272f7e163369113e3afd5878f8b21ba1fdff144
    8b95688ceed5bb02ca9236e93841afc592322720
    4ab34175031089c070b2ffd3d7151806e3cb5700
    32928bad4d4f2365110fce3a382c4aaedb8ef55d
    """.strip().split()
)


def bash(
    script: str,
    check: bool = True,
    capture_output: bool = False,
    input: bytes | str | None = None,
    text: bool | None = None,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    script = "set -evx\n" + script
    result = subprocess.run(
        ["bash", "-c", script],
        text=text,
        capture_output=capture_output,
        cwd=cwd,
        input=input,
    )
    if check and result.returncode != 0:
        directory = ""
        if cwd is not None:
            directory = f" in {cwd}"
        print(
            f"{BRIGHT_RED}{BOLD}Bash script failed{directory} with exit code {result.returncode}:{RESET}"
        )
        print(f"{DIM}{script}{RESET}")

        stdout = result.stdout
        if isinstance(result.stdout, bytes):
            stdout = result.stdout.decode("utf-8", errors="backslashreplace")
        if stdout:
            print("Stdout:")
            print(stdout)

        stderr = result.stderr
        if isinstance(result.stderr, bytes):
            stderr = result.stderr.decode("utf-8", errors="backslashreplace")
        if stderr:
            print("Stderr:")
            print(stderr)

        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd="bash",
            output=result.stdout,
            stderr=result.stderr,
        )

    return result
