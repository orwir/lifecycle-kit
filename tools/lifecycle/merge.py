"""Merge a pull request by squash, then delete its branch wherever nothing is lost.

``gh pr merge --delete-branch`` merges, cleans up the local branch and deletes the remote one
as one call, one exit code covering all three. Its local cleanup switches the checkout it
runs in to the base branch, which git refuses in a linked worktree whose base branch another
checkout holds: gh exits 1 on a pull request it merged, and stops before the remote deletion.

Here the merge's outcome is the pull request's state, read after the call, never an exit
code. The branch on GitHub goes only where it still points at the pull request's head, read
just before the delete, so a commit pushed after the merge stays; one pushed in the moment
between that read and the delete is not guarded, since the API's delete takes no expected
commit. It goes through GitHub's API, as gh's own deletion does: a ``git push --delete``
would run the repository's pre-push hook, its whole gate in a repository on the kit. A local
branch goes only where its tip is that head: directly where no checkout holds it, after a
switch to the base branch where the primary checkout this runs in holds it, and never a
linked worktree's, which stays with its worktree: tidy keeps a squash-merged worktree, so
both go by hand.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import quote

from . import ship, tidy

#: Exit codes: merged, whatever the cleanup did; or not merged, the pull request as it was.
MERGED, NOT_MERGED = 0, 1
FIELDS = "state,headRefName,headRefOid,baseRefName,isCrossRepository"


class MergeError(Exception):
    """The pull request's state could not be read: nothing was deleted."""


def _git(root: Path, *args: str, timeout: float | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args, 124, "", f"fatal: git {args[0]} gave no answer in {timeout} s"
        )


def _view(pr: int, asked: bool) -> dict:
    try:
        return json.loads(ship.read("pr", "view", str(pr), "--json", FIELDS))
    except (ship.ReleaseError, ValueError) as error:
        if asked:
            raise MergeError(
                f"PR #{pr}'s state could not be read after the merge was asked for ({error}): "
                f"nothing deleted; lifecycle merge {pr} reads it again, and merges it only if "
                "it still reads open"
            ) from error
        raise MergeError(
            f"PR #{pr}'s state could not be read ({error}): nothing merged or deleted; "
            f"lifecycle merge {pr} reads it again, and merges it if it reads open"
        ) from error


def _on_origin(root: Path, head: str) -> tuple[str | None, str | None]:
    """The branch's commit on origin, None where it has none; or why it could not be read."""
    listed = _git(root, "ls-remote", "origin", f"refs/heads/{head}", timeout=ship.CALL_SECONDS)
    if listed.returncode != 0:
        return None, tidy._why(listed)
    return (listed.stdout.split()[0] if listed.stdout.strip() else None), None


def _remote(root: Path, pr: int, view: dict) -> str:
    """The head branch on GitHub, deleted where it is at the pull request's head."""
    head, oid = view["headRefName"], view["headRefOid"]
    again = f"lifecycle merge {pr} reads it again"
    if view.get("isCrossRepository"):
        return f"branch {head} is on the fork the PR came from: left there"
    tip, unread = _on_origin(root, head)
    if unread:
        return f"branch {head} on origin could not be read, so it is left ({unread}); {again}"
    if tip is None:
        return f"branch {head} on origin: gone already, no delete sent"
    if tip != oid:
        return (
            f"branch {head} on origin is at {tip[:8]}, not the PR's head {oid[:8]}: left for "
            "the maintainer"
        )
    try:
        ship.gh("api", f"repos/{{owner}}/{{repo}}/git/refs/heads/{quote(head)}", "-X", "DELETE")
    except ship.ReleaseError as error:
        tip, unread = _on_origin(root, head)
        if not unread and tip is None:
            return f"branch {head} on origin: gone, though its delete reported an error ({error})"
        if isinstance(error, ship.Refused):
            return f"branch {head} on origin: GitHub refused its deletion, so it is left: {error}"
        return f"branch {head} on origin: its deletion failed, so it may be left: {error}; {again}"
    return f"branch {head} on origin: deleted"


def _local(root: Path, view: dict) -> str:
    """The local head branch, deleted where nothing on it would be lost and no linked
    worktree holds it."""
    head, oid, base = view["headRefName"], view["headRefOid"], view["baseRefName"]
    tip = _git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{head}").stdout.strip()
    if not tip:
        return f"local branch {head}: none here"
    listed = tidy.worktrees(root)
    holder = next((tree for tree in listed if tree.branch == head), None)
    held = f", checked out in {holder.path.as_posix()}" if holder is not None else ""
    if tip != oid:
        return f"local branch {head} is at {tip[:8]}, not the PR's head {oid[:8]}: left{held}"
    current = _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if holder is not None and current != head:
        return f"local branch {head}: left{held}"
    if holder is not None and holder is not listed[0]:
        path = holder.path.as_posix()
        return (
            f"local branch {head}: left with its worktree {path}, which tidy keeps after a "
            f"squash merge: both go by git worktree remove {path} and git branch -D {head}, "
            "on the maintainer's word"
        )
    switched = ""
    if holder is not None:
        moved = _git(root, "switch", "--quiet", base)
        if moved.returncode != 0:
            return (
                f"local branch {head}: left, as {holder.path.as_posix()} could not switch "
                f"to {base}: {tidy._why(moved)}"
            )
        switched = f"switched {holder.path.as_posix()} to {base}, then "
    dropped = _git(root, "branch", "--quiet", "-D", head)
    if dropped.returncode != 0:
        return f"{switched}local branch {head}: its deletion failed: {tidy._why(dropped)}"
    return f"{switched}local branch {head}: deleted"


def merge(root: Path, pr: int) -> tuple[int, list[str]]:
    """Squash-merge ``pr`` where it is open, then delete its branch on GitHub and here
    where nothing would be lost: the exit code and a line per step."""
    view = _view(pr, asked=False)
    if view["state"] == "MERGED":
        outcome = f"PR #{pr} was merged already into {view['baseRefName']}"
    elif view["state"] != "OPEN":
        return NOT_MERGED, [f"PR #{pr} is {view['state'].lower()}, not merged: nothing deleted"]
    else:
        why = ""
        try:
            ship.gh("pr", "merge", str(pr), "--squash")
        except ship.ReleaseError as error:
            why = str(error)
        view = _view(pr, asked=True)
        if view["state"] != "MERGED":
            reason = why or "gh reported no error"
            return NOT_MERGED, [
                f"PR #{pr} not merged, {view['state'].lower()}: {reason}; nothing deleted"
            ]
        outcome = f"PR #{pr} merged by squash into {view['baseRefName']}"
        if why:
            outcome += f", though the call reported an error ({why})"
    lines = [outcome, _remote(root, pr, view)]
    fetched = _git(root, "fetch", "--quiet", "--prune", "origin", timeout=ship.CALL_SECONDS)
    if fetched.returncode != 0:
        lines.append(
            f"git fetch --prune origin failed ({tidy._why(fetched)}): until a fetch succeeds, "
            "tidy reads origin as last fetched"
        )
    lines.append(_local(root, view))
    return MERGED, lines
