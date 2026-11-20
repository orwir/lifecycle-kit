"""What a repository needs before its next task: offline, so it can run at every session start.

A repository behind the installed kit by a minor or major release blocks a review
round: the skills it would run were written for a newer method and contract than
its copy describes. A patch release only changed guide wording, so it is reported
and waits for the next upgrade.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import kit_version
from . import release as _release
from .config import Config
from .guides import GIST_REVISION, local_edits, pushed_release, read_lock

BLOCK = "block"
NOTE = "note"


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


def check(config: Config, installed: str | None = None) -> list[Finding]:
    installed = installed or kit_version()
    lock = read_lock(config.root)
    if lock is None:
        if (config.guides_dir / GIST_REVISION).is_file():
            return [Finding(BLOCK, "the guides still mirror the gist: run `lifecycle upgrade`")]
        return [Finding(BLOCK, "not on the kit yet: see `lifecycle upgrade --help`")]

    findings = []
    pinned, current = _release(lock.kit), _release(installed)
    if pinned[:2] < current[:2]:
        findings.append(
            Finding(
                BLOCK,
                f"this repository is on kit {lock.kit} and the installed kit is {installed}: "
                "run `lifecycle upgrade` before a review round",
            )
        )
    elif pinned < current:
        findings.append(
            Finding(NOTE, f"kit {installed} changed guides this repository's {lock.kit} lacks")
        )
    elif pinned > current:
        findings.append(
            Finding(
                BLOCK,
                f"this repository is on kit {lock.kit} but the installed kit is {installed}: "
                "update the kit (Claude: `claude plugin marketplace update lifecycle-kit`)",
            )
        )
    pushed = pushed_release(lock)
    if pushed and _release(pushed) > current:
        findings.append(
            Finding(
                NOTE,
                f"this repository's guide edits went out in kit {pushed}; the installed kit "
                f"is {installed}: update it before the next upgrade",
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
