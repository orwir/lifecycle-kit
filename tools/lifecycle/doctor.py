"""What a repository needs before its next task, cheap enough for every session start.

The method is served live from the installed kit, so a release that changes only guide
wording, a skill or the tools asks nothing of a repository. One that changes a template it
follows, or carries an ``UPGRADING.md`` step after its release, owes an upgrade, which the
next task runs alone before its round. Each finding names its fix. Every check is
offline: nothing here asks the kit's remote.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

from . import KIT_ROOT, is_kit, kit_repository, kit_version
from . import changelog as _changelog
from . import release as _release
from .config import Config
from .guides import followed, owed_templates, read_lock

BLOCK = "block"
NOTE = "note"
UPGRADE = "upgrade"
ADOPT = "adopt"
UPDATE_KIT = "update-kit"
REBASE = "rebase"
CHANGES_SHOWN = 8
UPGRADE_SKILL = "the upgrade skill (Claude: `/lifecycle:upgrade`)"
IN_THE_TREE = "a task whose edits are in the tree lands before the upgrade"
UPDATE_COMMAND = (
    "Claude: `claude plugin marketplace update lifecycle-kit` and "
    "`claude plugin update lifecycle@lifecycle-kit`, then `/reload-plugins` in a running session"
)
#: The changelog's marker for a change every repository makes; its steps are UPGRADING.md's.
REPOSITORIES = "Repositories: "
UPGRADE_STEP = "Upgrade"


@dataclass(frozen=True)
class Finding:
    level: str
    message: str
    #: The remedy: UPGRADE, ADOPT, UPDATE_KIT or REBASE, or None when nothing needs doing.
    #: Whether it stops a round is ``level``'s to say, never the fix's; the review skill
    #: lets an UPGRADE wait while a task's edits are in the tree.
    fix: str | None = None
    details: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "message": self.message,
            "fix": self.fix,
            "details": list(self.details),
        }


def _entries(name: str, after: str, upto: str) -> list[tuple[str, list[_changelog.Entry]]]:
    """A kit file's releases after ``after`` up to ``upto``, newest first, each entry's
    ``#N`` naming the kit's issue: these lines are read in other repositories."""
    repo = kit_repository()
    return [
        (version, [entry._replace(text=_changelog.qualify(entry.text, repo)) for entry in entries])
        for version, entries in _changelog.sections(KIT_ROOT / name, after, upto)
    ]


def changes_since(pinned: str, installed: str) -> list[str]:
    """The kit CHANGELOG's entries for the releases after ``pinned`` up to ``installed``,
    each opened by its group (``Removed: …``), so none reads as the opposite of its claim.

    A ``Repositories:`` entry is left out: its steps, from ``steps_since``, stand in for it.
    """
    return [
        f"{entry.group}: {entry.text}" if entry.group else entry.text
        for _, entries in _entries("CHANGELOG.md", pinned, installed)
        for entry in entries
        if not entry.text.startswith(REPOSITORIES)
    ]


def steps_since(pinned: str, installed: str) -> list[str]:
    """``UPGRADING.md``'s steps for the releases after ``pinned`` up to ``installed``: what
    each asks of every repository beyond its templates, oldest release first,
    the order they are made in. Each opens ``Upgrade <release>:``, since a step can speak
    of its release and a first move runs several releases' steps together."""
    return [
        f"{UPGRADE_STEP} {version}: {step.text}"
        for version, steps in reversed(_entries("UPGRADING.md", pinned, installed))
        for step in steps
    ]


def _required(installed: str) -> tuple[str, ...]:
    """Every step up to ``installed``: what a first move onto the kit owes, which the
    upgrade skill reads before the upgrade, since some change the settings it reads."""
    return tuple(steps_since("0.0.0", installed))


def _shown(changes: list[str], required: list[str]) -> tuple[str, ...]:
    """The lines a session sees: every step, then the changes up to the cap."""
    room = max(CHANGES_SHOWN - len(required), 0)
    rest = len(changes) - room
    more = [f"… and {rest} more in CHANGELOG.md (`lifecycle where`)"] if rest > 0 else []
    return (*required, *changes[:room], *more)


#: The branch the marketplace serves: the kit's default branch, which only a release moves.
SERVED = "origin/HEAD"


def _kit(config: Config, installed: str) -> list[Finding]:
    """The kit's own repository is the method's home, so it needs no lock. Its rounds
    run on the installed plugin, though, and its tasks on the integration branch."""
    return [*_served(config, installed), *_behind(config)]


def _served(config: Config, installed: str) -> list[Finding]:
    """Older than the release the marketplace serves, the rounds run skills that release
    replaced. Tasks land on the integration branch and a release fast-forwards the default
    branch, so the manifest there is the release: a bump still on the integration branch,
    or a tag a refused push left behind, is not one."""
    released = _git(config, "show", f"{SERVED}:.claude-plugin/plugin.json")
    try:
        version = str(json.loads(released)["version"]) if released else None
        behind = bool(version) and _release(installed) < _release(version)
    except (ValueError, KeyError, TypeError):
        return []
    if not behind:
        return []
    return [
        Finding(
            NOTE,
            f"the kit's latest release is {version} and the installed kit is "
            f"{installed}: the rounds run on {installed}'s skills until it is updated "
            f"({UPDATE_COMMAND})",
            UPDATE_KIT,
        )
    ]


#: A branch cut from the last release's tag to ship without what has landed since.
HOTFIX = "hotfix/"


def _behind(config: Config) -> list[Finding]:
    """A session's worktree is cut from the default branch, the last release, so until it
    takes what has landed since, a task would read code without it. A branch with a
    commit of its own, or a tree holding edits, is a task under way, which started on
    the integration branch and whose push rebases; a hotfix branch stays off it."""
    landed = f"origin/{config.integration}"
    missing = _count(config, f"HEAD..{landed}")
    if not missing or _count(config, f"{landed}..HEAD") != 0:
        return []
    branch = (_git(config, "rev-parse", "--abbrev-ref", "HEAD") or "").strip()
    if branch.startswith(HOTFIX) or _git(config, "status", "--porcelain") != "":
        return []
    return [
        Finding(
            NOTE,
            f"this branch is {missing} commit(s) behind {landed}, where the kit's tasks land: "
            f"before a task reads the code, `git fetch origin` and `git rebase {landed}`, "
            "then read AGENTS.md again",
            REBASE,
        )
    ]


def _count(config: Config, revisions: str) -> int | None:
    counted = _git(config, "rev-list", "--count", revisions)
    return int(counted) if counted and counted.strip().isdigit() else None


def check(config: Config, installed: str | None = None) -> list[Finding]:
    installed = installed or kit_version()
    if is_kit(config.root):
        return _kit(config, installed)
    lock = read_lock(config.root)
    if lock is None:
        return [
            Finding(
                BLOCK,
                f"not on the kit yet: before the next task, {UPGRADE_SKILL} moves it on. It "
                "compares each guide "
                "named like one of the kit's with the kit's, then runs `lifecycle upgrade --adopt`",
                ADOPT,
                _required(installed),
            )
        ]
    if _release(lock.kit) > _release(installed):
        return [
            Finding(
                BLOCK,
                f"this repository is on kit {lock.kit} but the installed kit is {installed}: "
                f"update the kit before the next task ({UPDATE_COMMAND})",
                UPDATE_KIT,
            )
        ]
    behind = _release(lock.kit) < _release(installed)
    steps = steps_since(lock.kit, installed) if behind else []
    targets = followed(config)
    templates = [f"template {name} -> {targets[name]}" for name in owed_templates(config, lock)]
    if not (lock.guides or steps or templates):
        return []
    changes = changes_since(lock.kit, installed) if behind else []
    if lock.guides:
        message = (
            f"this repository still holds a copy of the method in {config.guides}: the next "
            f"task runs {UPGRADE_SKILL} alone first, which deletes the copy; {IN_THE_TREE}"
        )
    else:
        message = (
            f"kit {installed} asks this repository, on {lock.kit}, for an upgrade: the next "
            f"task runs {UPGRADE_SKILL} alone first; {IN_THE_TREE}"
        )
    return [Finding(BLOCK, message, UPGRADE, _shown(changes, [*steps, *templates]))]


def _git(config: Config, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(config.root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.stdout if result.returncode == 0 else None
