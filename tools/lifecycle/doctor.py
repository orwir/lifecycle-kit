"""What a repository needs before its next task, cheap enough for every session start.

A repository behind the installed kit by a minor or major release blocks a review
round: the skills it would run were written for a newer method and contract than
its copy describes. A patch release only changed guide wording, so it is a note.
Each finding names its fix, and a tracked task's clarify runs the upgrade as its first
step; an untracked task meets a minor or major one at its work round. The one
network read, the newest release on the kit's remote, comes in from the caller
(``latest.latest_release``), so the checks here stay offline.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field

from . import KIT_ROOT, kit_version
from . import guides as _guides
from . import release as _release
from .config import Config
from .guides import (
    GIST_REVISION,
    INSTALLED_AS,
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
REPOSITORIES = "Repositories: "

_HEADING = re.compile(r"^## v(\d+\.\d+\.\d+)\s*$")


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


def changes_since(pinned: str, installed: str) -> list[str]:
    """The kit CHANGELOG's entries for the releases after ``pinned`` up to ``installed``.

    Any ``## `` line ends a release's entries, so a heading in another shape drops its
    own entries rather than lending them to the release above it.
    """
    changelog = KIT_ROOT / "CHANGELOG.md"
    if not changelog.is_file():
        return []
    entries, taking = [], False
    for line in changelog.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            heading = _HEADING.match(line)
            taking = bool(heading) and (
                _release(pinned) < _release(heading.group(1)) <= _release(installed)
            )
            continue
        if taking and line.startswith("- "):
            entries.append(line[2:])
    return entries


def _shown(entries: list[str]) -> tuple[str, ...]:
    """The entries a session sees: every ``Repositories:`` line, then the rest up to the cap."""
    required = [e for e in entries if e.startswith(REPOSITORIES)]
    others = [e for e in entries if not e.startswith(REPOSITORIES)]
    room = max(CHANGES_SHOWN - len(required), 0)
    rest = len(others) - room
    more = [f"… and {rest} more in CHANGELOG.md (`lifecycle where`)"] if rest > 0 else []
    return (*required, *others[:room], *more)


def _behind(lock: Lock, installed: str, pushed_pending: str | None) -> Finding:
    pinned, current = _release(lock.kit), _release(installed)
    changes = _shown(changes_since(lock.kit, installed))
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


def _newer_out(installed: str, latest: str | None) -> list[Finding]:
    if not latest or _release(latest) <= _release(installed):
        return []
    return [
        Finding(
            NOTE,
            f"kit {latest} is out and this machine has {installed}: update it ({UPDATE_COMMAND})",
            UPDATE_KIT,
        )
    ]


def check(config: Config, installed: str | None = None, latest: str | None = None) -> list[Finding]:
    """``latest`` is the newest release on the kit's remote, when the caller asked for it."""
    installed = installed or kit_version()
    findings = _repository(config, installed)
    if any(finding.fix == UPDATE_KIT for finding in findings):
        return findings
    return _newer_out(installed, latest) + findings


def _repository(config: Config, installed: str) -> list[Finding]:
    lock = read_lock(config.root)
    if lock is None:
        if (config.guides_dir / GIST_REVISION).is_file():
            return [
                Finding(
                    BLOCK,
                    "the guides still mirror the gist: moving onto the kit is its own task "
                    "(`lifecycle upgrade`, then port the templates)",
                    ADOPT,
                )
            ]
        return [Finding(BLOCK, "not on the kit yet: see `lifecycle upgrade --help`", ADOPT)]

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
        for name, target in INSTALLED_AS.items()
        if (config.root / target).is_file()
        and (_guides.METHOD / name).is_file()
        and text(config.root / target) == text(_guides.METHOD / name)
        and _at(config, base, target) != text(config.root / target)
    ]
    previous = before.get("kit") if before else None
    changes = changes_since(previous, lock.kit) if previous else []
    return {
        "from": previous,
        "to": lock.kit,
        "changes": changes,
        "required": [c.removeprefix(REPOSITORIES) for c in changes if c.startswith(REPOSITORIES)],
        "guides": rewritten,
        "deleted": deleted,
        "installed": installed,
    }
