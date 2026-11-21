"""What a repository needs before its next task, cheap enough for every session start.

A repository behind the installed kit by a minor or major release blocks a review
round: the skills it would run were written for a newer method and contract than
its copy describes. A patch release only changed guide wording, so it is a note.
Each finding names its fix, and a tracked task's clarify runs the upgrade as its first
step; an untracked task meets a minor or major one at its work round. Every check
is offline: nothing here asks the kit's remote.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

from . import KIT_ROOT, is_kit, kit_repository, kit_version
from . import changelog as _changelog
from . import guides as _guides
from . import release as _release
from .config import Config
from .guides import (
    LOCK,
    Lock,
    local_edits,
    method_files,
    pushed_release,
    read_lock,
    text,
)

BLOCK = "block"
NOTE = "note"
UPGRADE = "upgrade"
ADOPT = "adopt"
UPDATE_KIT = "update-kit"
CHANGES_SHOWN = 8
UPGRADE_SKILL = "the upgrade skill (Claude: `/lifecycle:upgrade`)"
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
    #: The remedy: UPGRADE, ADOPT or UPDATE_KIT, or None when nothing needs doing.
    #: Whether it stops a round is ``level``'s to say, never the fix's.
    fix: str | None = None
    details: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "message": self.message,
            "fix": self.fix,
            "details": list(self.details),
        }


def _entries(name: str, after: str, upto: str) -> list[tuple[str, list[str]]]:
    """A kit file's releases after ``after`` up to ``upto``, newest first, each entry's
    ``#N`` naming the kit's issue: these lines are read in other repositories."""
    repository = kit_repository()
    return [
        (version, [_changelog.qualify(entry, repository) for entry in entries])
        for version, entries in _changelog.sections(KIT_ROOT / name, after, upto)
    ]


def changes_since(pinned: str, installed: str) -> list[str]:
    """The kit CHANGELOG's entries for the releases after ``pinned`` up to ``installed``.

    A ``Repositories:`` entry is left out: its steps, from ``steps_since``, stand in for it.
    """
    return [
        entry
        for _, entries in _entries("CHANGELOG.md", pinned, installed)
        for entry in entries
        if not entry.startswith(REPOSITORIES)
    ]


def steps_since(pinned: str, installed: str) -> list[str]:
    """``UPGRADING.md``'s steps for the releases after ``pinned`` up to ``installed``: what
    each asks of every repository beyond its guides and templates, oldest release first,
    the order they are made in. Each opens ``Upgrade <release>:``, since a step can speak
    of its release and a first move runs several releases' steps together."""
    return [
        f"{UPGRADE_STEP} {version}: {step}"
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


def _behind(lock: Lock, installed: str, pushed_pending: str | None) -> Finding:
    pinned, current = _release(lock.kit), _release(installed)
    changes = _shown(changes_since(lock.kit, installed), steps_since(lock.kit, installed))
    minor = pinned[:2] < current[:2]
    if pushed_pending:
        return Finding(
            BLOCK if minor else NOTE,
            f"this repository is on kit {lock.kit}, and its guide edits went out in kit "
            f"{pushed_pending}, newer than the installed {installed}: update the kit "
            f"({UPDATE_COMMAND}), then upgrade",
            UPDATE_KIT,
            changes,
        )
    if minor:
        message = (
            f"this repository is on kit {lock.kit} and the installed kit is {installed}: "
            f"the next task upgrades first, by {UPGRADE_SKILL}, before any review round"
        )
    else:
        message = (
            f"kit {installed} changed guides this repository's {lock.kit} lacks: the next "
            f"task upgrades first, by {UPGRADE_SKILL}"
        )
    return Finding(BLOCK if minor else NOTE, message, UPGRADE, changes)


def _kit(config: Config, installed: str) -> list[Finding]:
    """The kit's own repository pins no copy of the method, so it needs no lock. Its rounds
    run on the installed plugin, though: older than the release on the integration branch,
    they run skills that release replaced. The release is read at the flow's base, so a
    task's own bump in the tree is not mistaken for it."""
    released = _at(config, flow_base(config), ".claude-plugin/plugin.json")
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
            f"the kit's {config.integration} is at {version} and the installed kit is "
            f"{installed}: update it before the next round ({UPDATE_COMMAND})",
            UPDATE_KIT,
        )
    ]


def check(config: Config, installed: str | None = None) -> list[Finding]:
    installed = installed or kit_version()
    if is_kit(config.root):
        return _kit(config, installed)
    lock = read_lock(config.root)
    if lock is None:
        return [
            Finding(
                BLOCK,
                "not on the kit yet: see `lifecycle upgrade --help`",
                ADOPT,
                _required(installed),
            )
        ]

    findings = []
    current = _release(installed)
    pushed = pushed_release(lock)
    pushed_pending = pushed if pushed and _release(pushed) > current else None
    if _release(lock.kit) < current:
        findings.append(_behind(lock, installed, pushed_pending))
    elif _release(lock.kit) > current:
        findings.append(
            Finding(
                BLOCK,
                f"this repository is on kit {lock.kit} but the installed kit is {installed}: "
                f"update the kit ({UPDATE_COMMAND})",
                UPDATE_KIT,
            )
        )
    elif pushed_pending:
        findings.append(
            Finding(
                NOTE,
                f"this repository's guide edits went out in kit {pushed_pending}; the installed "
                f"kit is {installed}: the next upgrade waits until the kit is updated "
                f"({UPDATE_COMMAND})",
                UPDATE_KIT,
            )
        )
    edits = local_edits(config, lock)
    if edits:
        findings.append(
            Finding(
                NOTE,
                "guide edits not yet in the kit: " + ", ".join(edits) + " (they go to the kit "
                "at their task's Complete)",
            )
        )
    return findings


def _git(config: Config, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(config.root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def flow_base(config: Config) -> str:
    """The commit a task's work is measured from: HEAD on the integration branch, the
    merge-base with it on any other branch, so a WIP commit on a branch still counts."""
    branch = (_git(config, "rev-parse", "--abbrev-ref", "HEAD") or "").strip()
    if branch == config.integration:
        return "HEAD"
    for integration in (config.integration, f"origin/{config.integration}"):
        base = _git(config, "merge-base", integration, "HEAD")
        if base:
            return base.strip()
    return "HEAD"


def _at(config: Config, base: str, rel: str) -> str | None:
    shown = _git(config, "show", f"{base}:{rel}")
    return shown.replace("\r\n", "\n") if shown is not None else None


def upgraded(config: Config, base: str | None = None) -> dict | None:
    """The upgrade the tree holds that has not landed: against ``base``, the flow's by default.

    A task that spans sessions finds its upgrade here: the release move, what the kit
    changed in between, the guides it rewrote or deleted and the templates it installed
    whole. Guides the task itself edited stay out: they are its own work, not kit text.
    """
    base = base or flow_base(config)
    lock = read_lock(config.root)
    landed = _at(config, base, LOCK)
    before = json.loads(landed) if landed else None
    if lock is None or (before and before.get("kit") == lock.kit):
        return None
    own = set(local_edits(config, lock))
    rewritten = [
        name
        for name in method_files()
        if name not in own
        and (config.guides_dir / name).is_file()
        and _at(config, base, f"{config.guides}/{name}") != text(config.guides_dir / name)
    ]
    deleted = sorted(set(before.get("guides", {})) - set(lock.guides)) if before else []
    installed = [
        target
        for name, target in config.templates.items()
        if (config.root / target).is_file()
        and (_guides.METHOD / name).is_file()
        and text(config.root / target) == text(_guides.METHOD / name)
        and _at(config, base, target) != text(config.root / target)
    ]
    previous = before.get("kit") if before else None
    changes = changes_since(previous, lock.kit) if previous else []
    # A first move has no release to measure from: every step the kit has asked for applies.
    owed = steps_since(previous or "0.0.0", lock.kit)
    return {
        "from": previous,
        "to": lock.kit,
        "changes": changes,
        "required": owed,
        "guides": rewritten,
        "deleted": deleted,
        "installed": installed,
    }
