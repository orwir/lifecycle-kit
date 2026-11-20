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
from pathlib import Path

from . import METHOD, kit_remote, kit_version, release
from .config import Config

LOCK = ".lifecycle.lock"
CHANGELOG = "CHANGELOG.md"
GIST = "https://gist.github.com/d288ef4ec7dcb37a4cd3e9ae2019c037.git"
GIST_REVISION = ".gist-revision"
#: The gist commit the kit's method was imported from; a mirror past it holds gist pushes
#: the kit never took, which a move to the kit would silently revert.
GIST_IMPORTED = "f3b9b7ead40849e7375ff3b26de4a3506b15065b"
TEMPLATES = (
    "agents_template.md",
    "contributing_template.md",
    "issue_template_bug.md",
    "issue_template_task.md",
    "pr_template.md",
)


class GuidesError(Exception):
    pass


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


def check_imported(clone: str, revision: str) -> None:
    """Refuse a gist mirror whose revision the kit's import does not contain."""
    contained = subprocess.run(
        ["git", "-C", clone, "merge-base", "--is-ancestor", revision, GIST_IMPORTED],
        capture_output=True,
        check=False,
    )
    if contained.returncode != 0:
        raise GuidesError(
            f"the mirror is at gist {revision[:7]}, which the kit's import ({GIST_IMPORTED[:7]}) "
            "does not contain: the kit takes those gist changes first, or the move reverts them."
        )


def _gist_mirror_edits(config: Config, revision: str) -> list[str]:
    """Files a gist mirror changed since ``revision``: the README's check, before the kit."""
    with tempfile.TemporaryDirectory() as tmp:
        clone = subprocess.run(
            ["git", "clone", "-q", GIST, tmp], capture_output=True, text=True, check=False
        )
        if clone.returncode != 0:
            raise GuidesError(f"cannot clone the gist to check the mirror: {clone.stderr.strip()}")
        check_imported(tmp, revision)
        subprocess.run(["git", "-C", tmp, "checkout", "-q", revision], check=True)
        names = subprocess.run(
            ["git", "-C", tmp, "ls-files"], capture_output=True, text=True, check=True
        ).stdout.split()
        return [
            name
            for name in names
            if (config.guides_dir / name).is_file()
            and text(config.guides_dir / name) != text(Path(tmp) / name)
        ]


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
    gist_revision = config.guides_dir / GIST_REVISION
    if gist_revision.is_file():
        edits = _gist_mirror_edits(config, text(gist_revision).strip())
        if edits:
            raise GuidesError(
                "the gist mirror has unpushed edits: " + ", ".join(edits) + ". Push them to the "
                "gist by its README's Edit the canonical, then upgrade."
            )
        return []
    if not adopt:
        raise GuidesError(
            "this repository has no record of where its guides came from. Compare them with "
            "the kit's method/, take anything only this copy has into the kit, then run "
            "`lifecycle upgrade --adopt`."
        )
    return []


def upgrade(config: Config, adopt: bool = False, dry_run: bool = False) -> list[str]:
    """Pin the repository's guides to the installed kit; returns the files that changed."""
    lock = read_lock(config.root)
    carry = _check_upgradable(config, lock, adopt)
    if carry is None:
        return []
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
        write_lock(config.root, new)
        (config.guides_dir / GIST_REVISION).unlink(missing_ok=True)
    return sorted(changed)


def _git(cwd: str, *args: str) -> str:
    result = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise GuidesError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _note_release(clone: Path, version: str, message: str) -> None:
    changelog = clone / CHANGELOG
    if not changelog.is_file():
        return
    body = text(changelog)
    at = body.find("\n## ")
    entry = f"\n## v{version}\n\n- {message}\n"
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


def push(config: Config, message: str) -> tuple[list[str], str]:
    """Take this repository's guide edits into the kit as a patch release.

    Each edit is replayed onto the kit's latest from the release its copy came from, so
    a copy that fell behind never reverts anyone's change; a conflict stops the push.
    Main must sit on its release's tag, or the patch would ship unreleased work under a
    guide-wording number. The pushed guides take the released text, other projects'
    changes included, and the lock records the release, which an upgrade waits for.
    Returns the pushed files and the new release.
    """
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
        _git(tmp, "commit", "-q", "-m", message, "-m", f"Released as v{new}.")
        _git(tmp, "tag", f"v{new}")
        _git(tmp, "push", "-q", "--atomic", "origin", "HEAD:main", f"v{new}")
    for name, body in merged.items():
        (config.guides_dir / name).write_text(body, encoding="utf-8", newline="\n")
        lock.guides[name] = digest(config.guides_dir / name)
        lock.pushed[name] = new
    write_lock(config.root, lock)
    return edits, new
