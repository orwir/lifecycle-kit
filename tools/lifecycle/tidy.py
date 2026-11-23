"""What a task that lands from a linked worktree leaves behind: the primary checkout's
integration branch, behind the one it just pushed to, and the worktree itself, with its
branch, once its work is on the integration branch.

The primary checkout follows by fast-forward alone, wherever git allows it, edits or not:
a long-lived local edit would otherwise hold it back for good. A worktree goes only once
every commit made on its branch is on the integration branch, or a patch-equivalent of it
is (a rebase before the push makes one), and its tree holds nothing: a fresh session's
worktree, cut from the integration branch with nothing of its own, has its HEAD there
too, and a branch reset after its commit may have dropped that commit. Nothing is
fetched: a push from any worktree moves the remote-tracking ref they all share.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: The reflog subjects of a commit made on the branch, ``commit (amend)`` among them.
MADE = ("commit", "cherry-pick:", "revert:", "am:")
AMEND = "commit (amend):"
#: The most names a line gives before it counts the rest.
NAMED = 5
#: Only Windows refuses to rename a folder a process holds; elsewhere nothing shows it.
PROBES = os.name == "nt"


class TidyError(Exception):
    """A worktree the probe moved and could not move back."""


@dataclass(frozen=True)
class Worktree:
    path: Path
    #: The branch's short name, or None for a detached HEAD or a bare repository.
    branch: str | None = None
    bare: bool = False
    locked: bool = False
    #: Its folder is gone: git lists it until its entry is removed or pruned.
    prunable: bool = False


@dataclass(frozen=True)
class Lag:
    """Where the primary checkout's integration branch stands against ``origin``'s."""

    path: Path | None
    #: level, behind, diverged, ahead, elsewhere, bare, no-origin or none
    state: str
    behind: int = 0
    ahead: int = 0
    #: The branch checked out there when it is not the integration branch.
    branch: str | None = None


@dataclass(frozen=True)
class Report:
    lines: tuple[str, ...]
    #: A fast-forward or a removal git refused: the command exits 1.
    refused: bool = False


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _git(root: Path, *args: str) -> str | None:
    result = _run(root, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def _names(names: list[str]) -> str:
    shown = ", ".join(names[:NAMED])
    return shown + (f" and {len(names) - NAMED} more" if len(names) > NAMED else "")


def _why(result: subprocess.CompletedProcess) -> str:
    """git's reason: its ``error:`` or ``fatal:`` line with the paths it lists below it,
    or else its last line (a refused merge ends on a bare "Aborting")."""
    lines = (result.stderr or result.stdout).splitlines()
    for at, line in enumerate(lines):
        if line.startswith(("error:", "fatal:")):
            paths = []
            for below in lines[at + 1 :]:
                if not below.startswith("\t"):
                    break
                paths.append(below.strip())
            return f"{line.strip()} {_names(paths)}" if paths else line.strip()
    last = [line.strip() for line in lines if line.strip()]
    return last[-1] if last else f"exit {result.returncode}"


def worktrees(root: Path) -> list[Worktree]:
    """Every checkout of the clone, the primary one first, as git lists them."""
    listed = _git(root, "worktree", "list", "--porcelain")
    found: list[Worktree] = []
    for block in (listed or "").split("\n\n"):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            fields[key] = value
        if "worktree" not in fields:
            continue
        branch = fields.get("branch", "")
        found.append(
            Worktree(
                path=Path(fields["worktree"]),
                branch=branch.removeprefix("refs/heads/") if branch else None,
                bare="bare" in fields,
                locked="locked" in fields,
                prunable="prunable" in fields,
            )
        )
    return found


def _upstream(integration: str) -> str:
    return f"refs/remotes/origin/{integration}"


def _count(root: Path, revisions: str) -> int:
    counted = _git(root, "rev-list", "--count", revisions)
    return int(counted) if counted and counted.isdigit() else 0


def lag(root: Path, integration: str) -> Lag:
    """The primary checkout against ``origin/<integration>``, read offline."""
    listed = worktrees(root)
    if not listed:
        return Lag(None, "none")
    primary = listed[0]
    if primary.bare:
        return Lag(primary.path, "bare")
    upstream = _upstream(integration)
    if _git(root, "rev-parse", "--verify", "--quiet", f"{upstream}^{{commit}}") is None:
        return Lag(primary.path, "no-origin")
    if primary.branch != integration:
        return Lag(primary.path, "elsewhere", branch=primary.branch)
    local = f"refs/heads/{integration}"
    behind = _count(root, f"{local}..{upstream}")
    ahead = _count(root, f"{upstream}..{local}")
    if behind and ahead:
        state = "diverged"
    elif behind:
        state = "behind"
    elif ahead:
        state = "ahead"
    else:
        state = "level"
    return Lag(primary.path, state, behind, ahead)


def _edits(path: Path) -> list[str]:
    """The tracked files the checkout holds edits to, staged or not."""
    return (_git(path, "diff", "--name-only", "HEAD") or "").splitlines()


def fast_forward(root: Path, integration: str) -> tuple[bool, str]:
    """Fast-forward the primary checkout's integration branch to ``origin``'s where git
    allows it: False where git refused, and the line that says what happened."""
    where = lag(root, integration)
    upstream = f"origin/{integration}"
    if where.path is None:
        return True, "primary checkout: none found, this is not a git checkout"
    at = f"primary checkout {where.path.as_posix()}"
    left = {
        "bare": "a bare repository, nothing to fast-forward",
        "no-origin": f"no {upstream} in this clone to follow, nothing fast-forwarded",
        "elsewhere": f"{where.branch or 'a detached HEAD'} checked out, not {integration}: "
        "left as it is",
        "level": f"{integration} level with {upstream}",
        "ahead": f"{integration} {where.ahead} commit(s) ahead of {upstream}, "
        "nothing to fast-forward",
        "diverged": f"{integration} has {where.ahead} commit(s) of its own and is "
        f"{where.behind} behind {upstream}: left for you",
    }
    if where.state in left:
        return True, f"{at}: {left[where.state]}"
    edits = _edits(where.path)
    merged = _run(where.path, "merge", "--ff-only", "--quiet", _upstream(integration))
    if merged.returncode != 0:
        return False, (
            f"{at}: the fast-forward of {integration} to {upstream} was refused, nothing "
            f"changed: {_why(merged)}"
        )
    head = _git(where.path, "rev-parse", "--short", "HEAD") or upstream
    line = f"{at}: fast-forwarded {integration} by {where.behind} commit(s) to {head}"
    if edits:
        line += f", its edits left in place: {_names(edits)}"
    return True, line


def _made(root: Path, branch: str) -> list[str]:
    """The commits the branch's reflog records as made on it, oldest first; an amended
    one gives way to its amend."""
    log = _git(root, "reflog", "show", "--format=%H%x00%gs", f"refs/heads/{branch}", "--") or ""
    entries = [line.split("\0", 1) for line in reversed(log.splitlines()) if "\0" in line]
    made: list[str] = []
    before = None
    for sha, subject in entries:
        if subject.startswith(AMEND) and before in made:
            made.remove(before)
        if subject.startswith(MADE):
            made.append(sha)
        before = sha
    return made


def _on(root: Path, commit: str, upstream: str) -> bool:
    """``commit`` is on ``upstream``, or a patch-equivalent of it is."""
    if _run(root, "merge-base", "--is-ancestor", commit, upstream).returncode == 0:
        return True
    cherry = _git(root, "cherry", upstream, commit, f"{commit}^")
    return bool(cherry) and all(line.startswith("-") for line in cherry.splitlines())


def _unlanded(root: Path, tree: Worktree, integration: str) -> str | None:
    """Why ``tree``'s branch holds work not on the integration branch, or None."""
    upstream = _upstream(integration)
    made = _made(root, tree.branch)
    if not made:
        return "no commit of its own (a fresh session's)"
    if any(not _on(root, commit, upstream) for commit in made):
        return (
            f"a commit of its own not on {integration} (reset away, not pushed, or squash-merged)"
        )
    head = _git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{tree.branch}")
    if not head or _run(root, "merge-base", "--is-ancestor", head, upstream).returncode != 0:
        return f"its HEAD not on {integration} (not pushed, or squash-merged)"
    return None


def _current(root: Path) -> str | None:
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return None if branch in (None, "HEAD") else branch


def _default(root: Path) -> str | None:
    """The branch ``origin/HEAD`` names, the default branch, where this clone knows it."""
    named = _git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    return named.removeprefix("origin/") if named else None


def _kept(root: Path, tree: Worktree, integration: str, current: str | None) -> str | None:
    """Why ``tree`` stays, or None where its own work has landed."""
    if tree.branch is not None and tree.branch == current:
        return "the checkout this runs in"
    if tree.branch == integration:
        return f"{integration} checked out here, the integration branch"
    if tree.branch is not None and tree.branch == _default(root):
        return f"{tree.branch} checked out here, the default branch"
    if tree.locked:
        return "locked"
    if tree.branch is None:
        return "a detached HEAD"
    if not tree.prunable and _git(tree.path, "status", "--porcelain") != "":
        return "edits or untracked files"
    return _unlanded(root, tree, integration)


def survey(root: Path, integration: str) -> list[tuple[Worktree, str | None]]:
    """Each linked worktree, with why it stays, or None where its work has landed."""
    listed = worktrees(root)
    current = _current(root)
    return [(tree, _kept(root, tree, integration, current)) for tree in listed[1:]]


def probe(path: Path) -> bool:
    """Whether a process has ``path`` open. On Windows a folder cannot be renamed while
    a process has it as its working directory or holds a file in it open; elsewhere
    nothing tells, and the maintainer's word is the guard."""
    if not PROBES or not path.exists():
        return False
    moved = path.with_name(f"{path.name}.tidy-probe")
    try:
        path.rename(moved)
    except OSError:
        return True
    try:
        moved.rename(path)
    except OSError as error:
        raise TidyError(
            f"the probe moved it to {moved.as_posix()} and could not move it back ({error}): "
            "rename it back; nothing in it was touched"
        ) from error
    return False


REMOVED = "removed"
KEPT = "kept"
REFUSED = "refused"


def _remove(root: Path, tree: Worktree, integration: str) -> tuple[str, str]:
    """Remove a landed worktree and delete its branch: how it ended, and its line."""
    name = tree.path.as_posix()
    try:
        held = probe(tree.path)
    except TidyError as error:
        return REFUSED, f"{name}: {error}"
    if held:
        return KEPT, f"kept {name}: in use"
    # This entry alone: `git worktree prune` drops every gone folder's, kept ones too.
    removed = _run(root, "worktree", "remove", str(tree.path))
    if removed.returncode != 0:
        if any(listed.path == tree.path for listed in worktrees(root)):
            return REFUSED, f"{name}: removal refused, kept with its branch: {_why(removed)}"
        deleted = _run(root, "branch", "-D", tree.branch)
        branch = (
            f"so its branch {tree.branch} is deleted"
            if deleted.returncode == 0
            else f"and its branch {tree.branch} stays: {_why(deleted)}"
        )
        return REFUSED, (
            f"{name}: removal failed partway ({_why(removed)}); git dropped the worktree, "
            f"{branch}; the folder is left behind for you"
        )
    how = "folder gone, its entry removed" if tree.prunable else "removed"
    again = _unlanded(root, tree, integration)
    if again:
        return REFUSED, f"{name}: {how}, its branch {tree.branch} kept: {again}"
    deleted = _run(root, "branch", "-D", tree.branch)
    if deleted.returncode != 0:
        return REFUSED, f"{name}: {how}, its branch {tree.branch} kept: {_why(deleted)}"
    return REMOVED, f"{name}: {how}, its branch {tree.branch} deleted"


def tidy(root: Path, integration: str, remove: bool = False) -> Report:
    """Fast-forward the primary checkout, then list the linked worktrees whose own work
    has landed, or with ``remove``, remove them and delete their branches."""
    ok, line = fast_forward(root, integration)
    lines = [line]
    refused = not ok
    if lag(root, integration).state in ("none", "no-origin"):
        return Report(tuple(lines), refused)
    landed = removed = 0
    for tree, why in survey(root, integration):
        name = tree.path.as_posix()
        if why:
            lines.append(f"kept {name}: {why}")
            continue
        landed += 1
        if not remove:
            lines.append(f"landed {name}, branch {tree.branch}")
            continue
        outcome, line = _remove(root, tree, integration)
        lines.append(line)
        removed += outcome == REMOVED
        refused = refused or outcome == REFUSED
    if remove:
        lines.append(f"{removed} of {landed} other landed worktree(s) removed with their branches")
    elif landed:
        lines.append(
            f"{landed} other landed worktree(s): on the maintainer's word, "
            "`lifecycle tidy --remove` removes them and their branches"
        )
    else:
        lines.append("no other landed worktree to remove")
    return Report(tuple(lines), refused)
