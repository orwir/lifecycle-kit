import os
import subprocess
import sys
from pathlib import Path


def test_a_suite_run_inside_a_git_hook_leaves_that_repository_alone(tmp_path):
    victim = tmp_path / "victim"
    subprocess.run(["git", "init", "-q", str(victim)], check=True)
    hook_env = {**os.environ, "GIT_DIR": str(victim / ".git")}  # as a worktree's hook has it
    test = Path(__file__).with_name("test_doctor.py")
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            f"{test}::test_the_kit_notes_an_installed_kit_older_than_the_served_release",
        ],
        env=hook_env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    bare = subprocess.run(
        ["git", "-C", str(victim), "config", "--get", "core.bare"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert bare == "false"
    assert run.returncode == 0, run.stdout + run.stderr
