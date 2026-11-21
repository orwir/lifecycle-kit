"""A repository's record of the kit release it follows.

The method is served live from the installed kit: a repository keeps no copy of it.
``.lifecycle.lock`` holds the release the repository last upgraded to and the text of each
template it follows at that release. So ``lifecycle doctor`` knows offline what a newer
kit asks of it, and ``lifecycle upgrade`` has each template's old text for a port. A
repository from before 0.8.0 still holds a copy of the method in its guides folder, with
each file's digest in its lock: its first upgrade deletes the copy.
"""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import METHOD, is_kit, kit_version, release
from .config import Config

LOCK = ".lifecycle.lock"
CANONICAL = (
    "this is the kit's own repository: its method/ is the canonical method, changed by the "
    "kit's own commits"
)


class GuidesError(Exception):
    pass


@dataclass
class Lock:
    kit: str
    #: Each followed template's text at ``kit``: what doctor compares the installed kit
    #: with, and a port's old text.
    templates: dict[str, str] = field(default_factory=dict)
    #: A lock from before 0.8.0: the digest of each method file copied into the guides
    #: folder, which the next upgrade deletes.
    guides: dict[str, str] = field(default_factory=dict)


@dataclass
class Port:
    """A changed template whose target the repository adapted, or does not have yet."""

    name: str
    target: str
    #: The unified diff from the template's old text to the new; empty when it is read whole.
    diff: str


@dataclass
class Changes:
    #: The release the repository was on, or "none" on a first move, and the installed one.
    before: str = "none"
    after: str = ""
    installed: list[str] = field(default_factory=list)
    ports: list[Port] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


def text(path: Path) -> str:
    """A file's text with line endings as the kit keeps them, whatever the checkout did."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(text(path).encode("utf-8")).hexdigest()


def method_files() -> list[str]:
    return sorted(p.name for p in METHOD.iterdir() if p.is_file() and not p.name.startswith("."))


def read_lock(root: Path) -> Lock | None:
    path = root / LOCK
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Lock(
        kit=data["kit"],
        templates=dict(data.get("templates", {})),
        guides=dict(data.get("guides", {})),
    )


def write_lock(root: Path, lock: Lock) -> None:
    body = {"kit": lock.kit, "templates": dict(sorted(lock.templates.items()))}
    (root / LOCK).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")


def followed(config: Config) -> dict[str, str]:
    """The templates the repository follows that the installed kit has, each with its target.
    A template the kit dropped leaves the set, and its target stays the repository's own."""
    return {name: target for name, target in config.templates.items() if (METHOD / name).is_file()}


def old_text(config: Config, lock: Lock | None, name: str) -> str | None:
    """A followed template's text at the lock's release: from the lock, or, before 0.8.0,
    from the repository's unedited copy. None for a template new to the repository."""
    if lock is None:
        return None
    if name in lock.templates:
        return lock.templates[name]
    copy = config.guides_dir / name
    if name in lock.guides and copy.is_file() and digest(copy) == lock.guides[name]:
        return text(copy)
    return None


def owed_templates(config: Config, lock: Lock | None) -> list[str]:
    """The followed templates the installed kit changed since the lock, or that are new to it."""
    return [
        name for name in followed(config) if old_text(config, lock, name) != text(METHOD / name)
    ]


def _check_templates(config: Config) -> None:
    """A ``[templates]`` the repository wrote names only templates the method has; a default
    the method lacks is skipped."""
    missing = [name for name in config.templates if not (METHOD / name).is_file()]
    if config.templates_named and missing:
        raise GuidesError(
            f"[templates] in .lifecycle.toml names {', '.join(missing)}, which kit "
            f"{kit_version()}'s method does not have: fix the name, or take the line out."
        )


def _copies(config: Config, lock: Lock | None, adopt: bool) -> list[str]:
    """The kit's files in the guides folder that the upgrade deletes. Raises, before anything
    is written, on a copied file that holds an edit the kit never took."""
    if lock is None:
        return (
            [name for name in method_files() if (config.guides_dir / name).is_file()]
            if adopt
            else []
        )
    present = {name: d for name, d in lock.guides.items() if (config.guides_dir / name).is_file()}
    edited = sorted(name for name, d in present.items() if digest(config.guides_dir / name) != d)
    if edited:
        raise GuidesError(
            f"{', '.join(edited)} in {config.guides}: an edit the kit never took. File it as an "
            "issue on the kit or move it into a guide of the repository's own, put the kit's text "
            "back in the copy (or delete it), then upgrade again."
        )
    return sorted(present)


def _diff(name: str, old: str, new: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{name} (kit {before})",
            tofile=f"{name} (kit {after})",
        )
    )


def upgrade(config: Config, adopt: bool = False, dry_run: bool = False) -> Changes:
    """Bring the repository to the installed kit: replace each followed template's target
    that holds the old text word for word, name the rest to port with their diffs, delete a
    copy of the method from before 0.8.0, and write the lock. Reads nothing over the network.
    """
    if is_kit(config.root):
        raise GuidesError(CANONICAL + ": nothing upgrades it")
    _check_templates(config)
    lock = read_lock(config.root)
    installed = kit_version()
    if lock is None and not adopt:
        raise GuidesError(
            "this repository has no record of the kit release it follows. Compare each file in "
            f"{config.guides} named like one in the kit's method/ with the kit, file anything "
            "only this copy has as an issue on the kit or move it into a guide of the repository's "
            "own, then run `lifecycle upgrade --adopt`, as the upgrade skill does."
        )
    if lock is not None and release(installed) < release(lock.kit):
        raise GuidesError(
            f"this repository is on kit {lock.kit} and the installed kit is {installed}: "
            "update the installed kit first (`lifecycle doctor` names how)"
        )
    copies = _copies(config, lock, adopt)
    before = lock.kit if lock else "none"
    changes = Changes(before=before, after=installed, deleted=copies)
    for name, target in followed(config).items():
        old, new, path = old_text(config, lock, name), text(METHOD / name), config.root / target
        if old == new:
            continue
        if old is not None and path.is_file() and text(path) == old:
            changes.installed.append(target)
        else:
            whole = old is None or not path.is_file()
            diff = "" if whole else _diff(name, old, new, before, installed)
            changes.ports.append(Port(name, target, diff))
    if dry_run:
        return changes
    for name, target in followed(config).items():
        if target in changes.installed:
            (config.root / target).write_text(text(METHOD / name), encoding="utf-8", newline="\n")
    for name in copies:
        (config.guides_dir / name).unlink()
    templates = {name: text(METHOD / name) for name in followed(config)}
    write_lock(config.root, Lock(kit=installed, templates=templates))
    return changes
