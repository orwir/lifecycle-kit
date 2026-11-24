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

A worktree on a detached HEAD, which an assistant's archive leaves to reuse it and
``git worktree add --detach`` makes, names no branch, and no git record names the one it
held: it goes on its HEAD's own reflog, read from the clone, which also holds any commit
made on that HEAD and left behind. The branch it held is then checked out nowhere, so the
branches no checkout holds take the branch test too, whatever left them; a branch nothing
was made on goes once its head has landed, as no session works on it.
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
#: What git leaves in a checkout's own git folder while an operation is under way: a
#: checkout mid-rebase lists as detached and clean, and git removes one mid-bisect.
UNDER_WAY = (
    ("rebase-merge", "a rebase"),
    ("rebase-apply", "a rebase or `git am`"),
    ("MERGE_HEAD", "a merge"),
    ("CHERRY_PICK_HEAD", "a cherry-pick"),
    ("REVERT_HEAD", "a revert"),
    ("BISECT_LOG", "a bisect"),
)
#: Where a rebase names the branch it rewrites, and a bisect the one it started on.
REBASING = ("rebase-merge/head-name", "rebase-apply/head-name")
BISECTING = "BISECT_START"
AWAY = "reset away, not pushed, or squash-merged"


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
    #: The commit its HEAD is at, as git listed it.
    head: str | None = None


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
                head=fields.get("HEAD") or None,
            )
        )
    return found


def _same(one: Path, other: Path) -> bool:
    """The same folder, by its path as git prints it, or by the file system where both
    exist (a short name, a link)."""
    if os.path.normcase(os.path.normpath(one)) == os.path.normcase(os.path.normpath(other)):
        return True
    try:
        return os.path.samefile(one, other)
    except OSError:
        return False


def _admin(root: Path, tree: Worktree) -> Path | None:
    """The checkout's own git folder, which holds its HEAD's reflog and any operation under
    way: the clone's own for the primary checkout, ``worktrees/<id>`` in it for a linked
    one. Where the folder is gone, it is the one whose ``gitdir`` file names it."""
    if not tree.prunable:
        found = _git(tree.path, "rev-parse", "--absolute-git-dir")
        return Path(found) if found else None
    common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        return None
    for gitdir in sorted((Path(common) / "worktrees").glob("*/gitdir")):
        try:
            named = Path(gitdir.read_text(encoding="utf-8").strip())
        except OSError:
            continue
        if not named.is_absolute():
            named = gitdir.parent / named
        if _same(named.parent, tree.path):
            return gitdir.parent
    return None


def _under_way(admin: Path) -> str | None:
    """The operation git has under way in the checkout whose git folder is ``admin``."""
    return next((what for name, what in UNDER_WAY if (admin / name).exists()), None)


def _held(admin: Path) -> set[str]:
    """The branches a rebase or a bisect in the checkout whose git folder is ``admin``
    holds, though the checkout lists as detached."""
    held = set()
    for name in (*REBASING, BISECTING):
        try:
            ref = (admin / name).read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if ref:
            held.add(ref.removeprefix("refs/heads/"))
    return held


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


def _made(root: Path, ref: str) -> list[str] | None:
    """The commits the ref's reflog records as made on it, oldest first; an amended one
    gives way to its amend. None where git could not read the reflog: a ref with no reflog
    reads as one with nothing made on it, never a failed read."""
    log = _git(root, "reflog", "show", "--format=%H%x00%gs", ref, "--")
    if log is None:
        return None
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


def _off(root: Path, made: list[str], head: str | None, integration: str, off: str) -> str | None:
    """Why the work ``made`` up to ``head`` is not all on the integration branch, or None;
    ``off`` is the reason where ``head`` is not on it."""
    upstream = _upstream(integration)
    if any(not _on(root, commit, upstream) for commit in made):
        return f"a commit of its own not on {integration} ({AWAY})"
    if not head or _run(root, "merge-base", "--is-ancestor", head, upstream).returncode != 0:
        return off
    return None


def _tip(root: Path, branch: str) -> str | None:
    return _git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}")


def _unlanded(root: Path, tree: Worktree, integration: str) -> str | None:
    """Why ``tree``'s branch holds work not on the integration branch, or None."""
    made = _made(root, f"refs/heads/{tree.branch}")
    if made is None:
        return f"the reflog of its branch {tree.branch} could not be read"
    if not made:
        return "no commit of its own (a fresh session's)"
    tip = _tip(root, tree.branch)
    off = f"its HEAD not on {integration} (not pushed, or squash-merged)"
    return _off(root, made, tip, integration, off)


def _adrift(root: Path, tree: Worktree, admin: Path, integration: str) -> str | None:
    """Why a detached worktree holds work not on the integration branch, or None: its HEAD's
    reflog records every commit made on it, the ones it left behind too."""
    made = _made(root, f"worktrees/{admin.name}/HEAD")
    if made is None:
        return "a detached HEAD whose reflog could not be read"
    return _off(root, made, tree.head, integration, f"its HEAD not on {integration}")


def _default(root: Path) -> str | None:
    """The branch ``origin/HEAD`` names, the default branch, where this clone knows it."""
    named = _git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    return named.removeprefix("origin/") if named else None


def _here(root: Path) -> Path | None:
    """The checkout this runs in."""
    top = _git(root, "rev-parse", "--show-toplevel")
    return Path(top) if top else None


def _kept(root: Path, tree: Worktree, integration: str, here: Path | None) -> str | None:
    """Why ``tree`` stays, or None where its own work has landed."""
    if here is not None and _same(tree.path, here):
        return "the checkout this runs in"
    if tree.branch == integration:
        return f"{integration} checked out here, the integration branch"
    if tree.branch is not None and tree.branch == _default(root):
        return f"{tree.branch} checked out here, the default branch"
    if tree.locked:
        return "locked"
    admin = _admin(root, tree)
    if admin is None and tree.branch is None:
        return "a detached HEAD whose git folder in the clone was not found"
    under_way = _under_way(admin) if admin is not None else None
    if under_way:
        return f"{under_way} in progress"
    if not tree.prunable and _git(tree.path, "status", "--porcelain") != "":
        return "edits or untracked files"
    if tree.branch is None:
        return _adrift(root, tree, admin, integration)
    return _unlanded(root, tree, integration)


def _loose(root: Path, branch: str, integration: str) -> str | None:
    """Why a branch no checkout holds keeps work not on the integration branch, or None.
    One nothing was made on goes once its head has landed: no session works on it."""
    made = _made(root, f"refs/heads/{branch}")
    if made is None:
        return "its reflog could not be read"
    return _off(root, made, _tip(root, branch), integration, f"its head not on {integration}")


def _branches(root: Path) -> list[str]:
    """Every local branch, by its short name."""
    refs = _git(root, "for-each-ref", "--format=%(refname)", "refs/heads/") or ""
    return [ref.removeprefix("refs/heads/") for ref in refs.splitlines() if ref]


def _holding(root: Path, integration: str, listed: list[Worktree]) -> set[str | None]:
    """The branches tidy never deletes alone: the integration and default branches, and
    each one a checkout has out or a rebase or a bisect in it is on, though that checkout
    lists as detached."""
    held = {integration, _default(root)}
    for tree in listed:
        held.add(tree.branch)
        admin = None if tree.bare else _admin(root, tree)
        if admin is not None:
            held |= _held(admin)
    return held


def strays(
    root: Path, integration: str, listed: list[Worktree], names: list[str]
) -> list[tuple[str, str | None]]:
    """Each of ``names`` no checkout in ``listed`` holds, but the integration and default
    branches, with why it stays, or None where its own work has landed."""
    held = _holding(root, integration, listed)
    return [(name, _loose(root, name, integration)) for name in names if name not in held]


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


def _remove(root: Path, tree: Worktree, integration: str, here: Path | None) -> tuple[str, str]:
    """Remove a landed worktree and delete its branch: how it ended, and its line."""
    name = tree.path.as_posix()
    try:
        held = probe(tree.path)
    except TidyError as error:
        return REFUSED, f"{name}: {error}"
    if held:
        return KEPT, f"kept {name}: in use"
    if tree.branch is None:
        # Its reflog goes with it, so it is judged again as it stands: a commit made since,
        # or a session given it on a branch of its own, keeps it.
        now = next((listed for listed in worktrees(root) if _same(listed.path, tree.path)), None)
        if now is None:
            return KEPT, f"{name}: gone from git's list before its removal, nothing done"
        why = _kept(root, now, integration, here)
        if why:
            return KEPT, f"kept {name}: {why}"
        tree = now
    # This entry alone: `git worktree prune` drops every gone folder's, kept ones too.
    removed = _run(root, "worktree", "remove", str(tree.path))
    if removed.returncode != 0:
        if any(_same(listed.path, tree.path) for listed in worktrees(root)):
            kept = " with its branch" if tree.branch else ""
            return REFUSED, f"{name}: removal refused, kept{kept}: {_why(removed)}"
        if tree.branch is None:
            branch = "a detached HEAD with no branch to delete"
        else:
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
    if tree.branch is None:
        return REMOVED, f"{name}: {how}, a detached HEAD with no branch to delete"
    again = _unlanded(root, tree, integration)
    if again:
        return REFUSED, f"{name}: {how}, its branch {tree.branch} kept: {again}"
    deleted = _run(root, "branch", "-D", tree.branch)
    if deleted.returncode != 0:
        return REFUSED, f"{name}: {how}, its branch {tree.branch} kept: {_why(deleted)}"
    return REMOVED, f"{name}: {how}, its branch {tree.branch} deleted"


def _delete(root: Path, branch: str, integration: str) -> tuple[str, str]:
    """Delete a landed branch no checkout holds, judged again as it stands: how it ended,
    and its line."""
    again = _loose(root, branch, integration)
    if again:
        return KEPT, f"kept branch {branch}: {again}"
    if branch in _holding(root, integration, worktrees(root)):
        return KEPT, f"kept branch {branch}: checked out since the listing"
    deleted = _run(root, "branch", "-D", branch)
    if deleted.returncode != 0:
        return REFUSED, f"branch {branch}: its deletion was refused: {_why(deleted)}"
    return REMOVED, f"branch {branch}: deleted, checked out nowhere"


def tidy(root: Path, integration: str, remove: bool = False) -> Report:
    """Fast-forward the primary checkout, then list the linked worktrees whose own work
    has landed and the landed branches no checkout holds, or with ``remove``, remove those
    worktrees with their branches and delete those branches."""
    ok, line = fast_forward(root, integration)
    lines = [line]
    refused = not ok
    if lag(root, integration).state in ("none", "no-origin"):
        return Report(tuple(lines), refused)
    # The branches first, then the checkouts, both before anything goes: a branch made
    # since is never judged, and one checked out since is held.
    names = _branches(root)
    listed, here = worktrees(root), _here(root)
    surveyed = [(tree, _kept(root, tree, integration, here)) for tree in listed[1:]]
    loose = strays(root, integration, listed, names)
    landed = removed = 0
    for tree, why in surveyed:
        name = tree.path.as_posix()
        if why:
            lines.append(f"kept {name}: {why}")
            continue
        landed += 1
        if not remove:
            held = f"branch {tree.branch}" if tree.branch else "a detached HEAD"
            lines.append(f"landed {name}, {held}")
            continue
        outcome, line = _remove(root, tree, integration, here)
        lines.append(line)
        removed += outcome == REMOVED
        refused = refused or outcome == REFUSED
    strayed = deleted = 0
    for branch, why in loose:
        if why:
            lines.append(f"kept branch {branch}: {why}")
            continue
        strayed += 1
        if not remove:
            lines.append(f"landed branch {branch}, checked out nowhere")
            continue
        outcome, line = _delete(root, branch, integration)
        lines.append(line)
        deleted += outcome == REMOVED
        refused = refused or outcome == REFUSED
    lines.append(_summary(remove, landed, removed, strayed, deleted))
    return Report(tuple(lines), refused)


def _summary(remove: bool, landed: int, removed: int, strayed: int, deleted: int) -> str:
    """The last line: each part only where something landed, a worktree's branch left to
    its own line, which says whether it had one."""
    if not landed and not strayed:
        return "no other landed worktree or branch to remove"
    if remove:
        parts = [f"{removed} of {landed} other landed worktree(s) removed"] if landed else []
        if strayed:
            parts.append(f"{deleted} of {strayed} landed branch(es) checked out nowhere deleted")
        return ", ".join(parts)
    parts = [f"{landed} other landed worktree(s)"] if landed else []
    if strayed:
        parts.append(f"{strayed} landed branch(es) checked out nowhere")
    return (
        " and ".join(parts) + ": on the maintainer's word, `lifecycle tidy --remove` removes them"
    )
