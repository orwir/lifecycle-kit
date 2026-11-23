"""The commit a task's work is measured from: where its branch forked from the integration
branch, which the work round's fails-without worktree and the reviewer's diff start at.

The local integration branch can sit releases behind ``origin``'s, or be missing where a
clone never checked it out, and ``origin``'s is missing in a clone with no remote, so the
fork point is read from whichever of the two exists: the newest commit HEAD shares with
either. On the integration branch itself that is HEAD's own commit. Both are named in
full, so a tag of the same name never stands in, and nothing is fetched: ``origin``'s
branch only moves forward, never behind the commit a branch was cut from it at.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class BaseError(Exception):
    """No commit to measure the work from."""


def _git(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _commit(root: Path, name: str) -> str | None:
    return _git(root, "rev-parse", "--verify", "--quiet", f"{name}^{{commit}}")


def base(root: Path, integration: str) -> str:
    """The full SHA of the newest commit HEAD shares with ``integration``, here or on
    ``origin``."""
    if _commit(root, "HEAD") is None:
        raise BaseError(
            "no commit at HEAD (not a git repository, or no commit yet): nothing to measure "
            "the work from; run it inside the repository, or commit first"
        )
    refs = [
        ref
        for ref in (f"refs/heads/{integration}", f"refs/remotes/origin/{integration}")
        if _commit(root, ref) is not None
    ]
    if not refs:
        raise BaseError(
            f"neither {integration} nor origin/{integration} is a branch in this clone: "
            "`git fetch origin`, or name the integration branch in .lifecycle.toml"
        )
    fork = _git(root, "merge-base", "HEAD", *refs)
    if not fork:
        raise BaseError(
            f"HEAD shares no commit with {' or '.join(ref.split('/', 2)[2] for ref in refs)}: "
            "`git fetch origin`, or check this branch was cut from the integration branch"
        )
    return fork
