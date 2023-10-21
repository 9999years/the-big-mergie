import subprocess
from .color import BRIGHT_RED, BOLD, RESET, DIM

ALL_REPOS = ["configuration", "dotfiles", "nix-config", "old-vimfiles"]

RESULT_REPO = "cake"


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
        print(
            f"{BRIGHT_RED}{BOLD}Bash script failed with exit code {result.returncode}:{RESET}"
        )
        print(f"{DIM}{script}{RESET}")

        stdout = result.stdout
        if isinstance(result.stdout, bytes):
            stdout = result.stdout.decode("utf-8", errors="backslashreplace")
        if stdout:
            print("Stdout:", stdout)

        stderr = result.stderr
        if isinstance(result.stderr, bytes):
            stderr = result.stderr.decode("utf-8", errors="backslashreplace")
        if stderr:
            print("Stderr:", stderr)

        raise RuntimeError

    return result
