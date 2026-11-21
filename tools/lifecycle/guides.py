"""A repository's copy of the method, pinned to one kit release.

``lifecycle upgrade`` copies the installed kit's ``method/`` into the repository's
guides folder and records the release and each file's digest in
``.lifecycle.lock``. A digest that no longer matches is an edit made in this
repository, which goes back to the kit at its task's Complete; an upgrade before
then carries it onto the new release by a three-way merge from the release its copy
came from, and stops on a conflict.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import METHOD, is_kit, kit_remote, kit_version, release
from . import changelog as _changelog
from .config import Config

LOCK = ".lifecycle.lock"
CHANGELOG = "CHANGELOG.md"
NO_ISSUE = (
    "which the kit's words never carry: in the kit's history #N and GH-N name the kit's own "
    "issues, owner/repo#N and a link a project's, and a closing keyword before any of them "
    "closes that issue once the kit's main takes it"
)
CANONICAL = (
    "this is the kit's own repository: its method/ is the canonical method, changed by the "
    "kit's own commits"
)


class GuidesError(Exception):
    pass


class Changes(list):
    """The guide files an upgrade changed, and the files it replaced with a template's new
    text, each having been the template's old text word for word."""

    def __init__(self, names=(), installed=()):
        super().__init__(names)
        self.installed = list(installed)


@dataclass
class Lock:
    kit: str
    guides: dict[str, str] = field(default_factory=dict)
    #: Each guide pushed since the pin, with the release that took it: its copy holds that
    #: release's text, which is where its next push starts and what the next upgrade waits for.
    pushed: dict[str, str] = field(default_factory=dict)


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
        kit=data["kit"], guides=dict(data.get("guides", {})), pushed=dict(data.get("pushed", {}))
    )


def write_lock(root: Path, lock: Lock) -> None:
    body: dict = {"kit": lock.kit}
    if lock.pushed:
        body["pushed"] = dict(sorted(lock.pushed.items()))
    body["guides"] = dict(sorted(lock.guides.items()))
    (root / LOCK).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")


def local_edits(config: Config, lock: Lock) -> list[str]:
    """The pinned files this repository changed or deleted since its last upgrade."""
    edits = []
    for name, expected in lock.guides.items():
        path = config.guides_dir / name
        if not path.is_file() or digest(path) != expected:
            edits.append(name)
    return edits


def pushed_release(lock: Lock) -> str | None:
    """The newest release a guide push from this repository made, if any is pending."""
    return max(lock.pushed.values(), key=release) if lock.pushed else None


def _check_upgradable(config: Config, lock: Lock | None, adopt: bool) -> list[str] | None:
    """The edits to carry (often none), or None when there is nothing to do.

    Raises when the upgrade would lose something.
    """
    installed = kit_version()
    if lock is not None:
        pushed = pushed_release(lock)
        if pushed and release(installed) < release(pushed):
            raise GuidesError(
                f"this repository's guide edits went out in kit {pushed}, and the installed "
                f"kit is {installed}: update the installed kit first, or the upgrade undoes them"
            )
        if release(installed) <= release(lock.kit):
            return None
        edits = local_edits(config, lock)
        deleted = [name for name in edits if not (config.guides_dir / name).is_file()]
        if deleted:
            raise GuidesError(
                "deleted here: " + ", ".join(deleted) + ". Restore them before the upgrade."
            )
        dropped = [name for name in edits if not (METHOD / name).is_file()]
        if dropped:
            raise GuidesError(
                f"kit {installed} drops " + ", ".join(dropped) + ", which holds an edit here: "
                "take the edit out, or into a guide of the repository's own, then upgrade."
            )
        own = [
            name
            for name in method_files()
            if name not in lock.guides
            and (config.guides_dir / name).is_file()
            and text(config.guides_dir / name) != text(METHOD / name)
        ]
        if own:
            raise GuidesError(
                f"kit {installed} adds " + ", ".join(own) + ", which this repository already has "
                "as a guide of its own: rename the repository's file, then upgrade."
            )
        return edits
    if not adopt:
        raise GuidesError(
            "this repository has no record of where its guides came from. Compare them with "
            "the kit's method/, take anything only this copy has into the kit, then run "
            "`lifecycle upgrade --adopt`."
        )
    return []


def _check_templates(config: Config) -> None:
    """A ``[templates]`` the repository wrote names only templates the method has; a default
    the method lacks is skipped, so a kit that drops one still deletes its copy."""
    missing = [name for name in config.templates if not (METHOD / name).is_file()]
    if config.templates_named and missing:
        raise GuidesError(
            f"[templates] in .lifecycle.toml names {', '.join(missing)}, which kit "
            f"{kit_version()}'s method does not have: fix the name, or take the line out."
        )


def _verbatim_installs(config: Config, before: dict[str, str]) -> list[str]:
    """The files the templates port into that still hold a template's old text word for word."""
    installs = []
    for name, target in config.templates.items():
        old, path = before.get(name), config.root / target
        present = old is not None and (METHOD / name).is_file() and path.is_file()
        if present and text(path) == old and old != text(METHOD / name):
            installs.append(target)
    return installs


def upgrade(config: Config, adopt: bool = False, dry_run: bool = False) -> Changes:
    """Pin the repository's guides to the installed kit.

    Returns the guide files that changed; ``installed`` names each file a template ports
    into that held its old text word for word, which the upgrade replaces with the new text.
    """
    if is_kit(config.root):
        raise GuidesError(CANONICAL + ": nothing upgrades it")
    _check_templates(config)
    lock = read_lock(config.root)
    carry = _check_upgradable(config, lock, adopt)
    if carry is None:
        return Changes()
    # A template whose guide copy holds a carried edit is the task's to finish: its
    # installed copy may hold the same edit, which the kit's text would undo.
    before = {
        name: text(config.guides_dir / name)
        for name in config.templates
        if (config.guides_dir / name).is_file() and name not in carry
    }
    installs = _verbatim_installs(config, before)
    carried = _carry(config, lock, carry) if lock and carry else {}
    new = Lock(kit=kit_version())
    changed = []
    for name in method_files():
        source = METHOD / name
        target = config.guides_dir / name
        new.guides[name] = digest(source)
        body = carried.get(name, text(source))
        if not target.is_file() or text(target) != body:
            changed.append(name)
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body, encoding="utf-8", newline="\n")
    dropped = sorted(set(lock.guides) - set(new.guides)) if lock else []
    for name in dropped:
        changed.append(name)
        if not dry_run:
            (config.guides_dir / name).unlink(missing_ok=True)
    if not dry_run:
        for target, name in ((t, n) for n, t in config.templates.items() if t in installs):
            (config.root / target).write_text(text(METHOD / name), encoding="utf-8", newline="\n")
        write_lock(config.root, new)
    return Changes(sorted(changed), installs)


def _git(cwd: str, *args: str) -> str:
    result = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise GuidesError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _today() -> str:
    return date.today().isoformat()


def _note_release(clone: Path, version: str, message: str) -> None:
    """The release above the newest in the kit's changelog, dated today: a guide push
    changes wording, so its line goes under Changed."""
    changelog = clone / CHANGELOG
    if not changelog.is_file():
        return
    body = text(changelog)
    at = body.find("\n## ")
    entry = f"\n{_changelog.heading(version, _today())}\n\n### Changed\n- {message}\n"
    body = body + entry if at < 0 else body[:at] + entry + body[at:]
    changelog.write_text(body, encoding="utf-8", newline="\n")


def _merge(clone: str, name: str, ours: str, base_release: str, theirs: str | None = None) -> str:
    """This copy's edit of ``name``, replayed from its own release onto ``theirs``.

    ``theirs`` defaults to the kit's latest in ``clone``; an upgrade passes the installed
    release's text.
    """
    work = Path(clone) / ".merge"
    work.mkdir(exist_ok=True)
    base = subprocess.run(
        ["git", "-C", clone, "show", f"v{base_release}:method/{name}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    latest = Path(clone) / "method" / name
    if theirs is None and latest.is_file():
        theirs = text(latest)
    if base.returncode != 0 or theirs is None:
        raise GuidesError(f"{name} is not in the kit at both v{base_release} and its latest")
    files = {"ours": ours, "base": base.stdout.replace("\r\n", "\n"), "theirs": theirs}
    for label, body in files.items():
        (work / label).write_text(body, encoding="utf-8", newline="\n")
    merged = subprocess.run(
        ["git", "merge-file", "-p", str(work / "ours"), str(work / "base"), str(work / "theirs")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if merged.returncode != 0:
        raise GuidesError(
            f"{name}: the kit changed it since v{base_release} too, and the changes conflict"
        )
    return merged.stdout


def _carry(config: Config, lock: Lock, edits: list[str]) -> dict[str, str]:
    """Each unpushed edit, replayed onto the installed release's text of its guide."""
    with tempfile.TemporaryDirectory() as tmp:
        _git(tmp, "clone", "-q", kit_remote(), ".")
        return {
            name: _merge(
                tmp,
                name,
                text(config.guides_dir / name),
                lock.pushed.get(name, lock.kit),
                theirs=text(METHOD / name),
            )
            for name in edits
        }


def push(config: Config, message: str, why: str) -> tuple[list[str], str]:
    """Take this repository's guide edits into the kit as a patch release.

    ``message`` is the kit commit's subject and the release's changelog entry; ``why`` is
    the commit's body, so the kit's own history says why each pushed clause exists.
    Each edit is replayed onto the kit's latest from the release its copy came from, so
    a copy that fell behind never reverts anyone's change; a conflict stops the push.
    Main must sit on its release's tag, or the patch would ship unreleased work under a
    guide-wording number. The pushed guides take the released text, other projects'
    changes included, and the lock records the release, which an upgrade waits for.
    Returns the pushed files and the new release.
    """
    if is_kit(config.root):
        raise GuidesError(CANONICAL + ", not by a push")
    lock = read_lock(config.root)
    if lock is None:
        raise GuidesError("not on the kit yet: nothing to push")
    edits = local_edits(config, lock)
    if not edits:
        return [], pushed_release(lock) or lock.kit
    deleted = [name for name in edits if not (config.guides_dir / name).is_file()]
    if deleted:
        raise GuidesError(
            "deleted here: " + ", ".join(deleted) + ". Restore them; a guide leaves the "
            "method in the kit itself, never from one project's copy."
        )
    message = message.strip()
    if not message:
        raise GuidesError(
            "no line: the message file's first line is what changed, one claim for the kit's "
            "changelog, then a blank line and the reason."
        )
    broken = _changelog.entry_violations(message)
    found = _changelog.issue_named(message)
    if found:
        broken.append(f"an issue reference ({found}), {NO_ISSUE}")
    if broken:
        raise GuidesError(
            "the line is the kit's changelog entry and breaks its style: "
            + "; ".join(broken)
            + f". Write what changed as one claim of at most {_changelog.CAP} characters, "
            "with no issue."
        )
    why = why.strip()
    if not why:
        raise GuidesError(
            "no reason: write why the guides changed below the line, after a blank line. "
            "It is the kit commit's body, where a later review of the guide finds it."
        )
    found = _changelog.issue_named(why)
    if found:
        raise GuidesError(
            f"the reason names an issue ({found}), {NO_ISSUE}. Say in the kit's words what the "
            "edit closes."
        )
    with tempfile.TemporaryDirectory() as tmp:
        _git(tmp, "clone", "-q", kit_remote(), ".")
        manifest = Path(tmp) / ".claude-plugin" / "plugin.json"
        current = json.loads(manifest.read_text(encoding="utf-8"))["version"]
        tagged = subprocess.run(
            ["git", "-C", tmp, "rev-parse", "-q", "--verify", f"v{current}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        if tagged != _git(tmp, "rev-parse", "HEAD"):
            raise GuidesError(
                f"the kit's main has commits after v{current} that no release carries: release "
                "them in the kit first, so this patch ships guide wording alone."
            )
        merged = {
            name: _merge(tmp, name, text(config.guides_dir / name), lock.pushed.get(name, lock.kit))
            for name in edits
        }
        for name, body in merged.items():
            (Path(tmp) / "method" / name).write_text(body, encoding="utf-8", newline="\n")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        major, minor, patch = release(data["version"])
        data["version"] = new = f"{major}.{minor}.{patch + 1}"
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
        _note_release(Path(tmp), new, message)
        released = [
            "method",
            ".claude-plugin",
            *([CHANGELOG] if (Path(tmp) / CHANGELOG).is_file() else []),
        ]
        _git(tmp, "add", "-A", *released)
        # Pinned, so a machine's commit.cleanup=strip cannot drop a reason line opening with #.
        _git(
            tmp,
            "commit",
            "-q",
            "--cleanup=whitespace",
            "-m",
            message,
            "-m",
            why,
            "-m",
            f"Released as v{new}.",
        )
        _git(tmp, "tag", f"v{new}")
        _git(tmp, "push", "-q", "--atomic", "origin", "HEAD:main", f"v{new}")
    for name, body in merged.items():
        (config.guides_dir / name).write_text(body, encoding="utf-8", newline="\n")
        lock.guides[name] = digest(config.guides_dir / name)
        lock.pushed[name] = new
    write_lock(config.root, lock)
    return edits, new
