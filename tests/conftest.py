import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from lifecycle import guides
from lifecycle.config import load

# A git hook exports what lets git find its repository, GIT_DIR among them, absolute from a
# linked worktree: left in place, a test's scratch `git init` runs on the real repository and
# leaves it bare. Cleared before any test runs, as githooks(5) advises.
_GIT_LOCAL = subprocess.run(
    ["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True, check=True
).stdout.split()
for _name in _GIT_LOCAL:
    os.environ.pop(_name, None)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repository on the kit with a two-file method at release 1.2.0."""
    method = tmp_path / "kit" / "method"
    method.mkdir(parents=True)
    (method / "task_review.md").write_text("# Task review\n", encoding="utf-8")
    (method / "agents_template.md").write_text("# AGENTS\n", encoding="utf-8")
    (method / "pr_template.md").write_text("a\nb\nc\nd\n", encoding="utf-8")
    monkeypatch.setattr(guides, "METHOD", method)
    monkeypatch.setattr(guides, "kit_version", lambda: "1.2.0")
    root = tmp_path / "repo"
    (root / "docs" / "guides").mkdir(parents=True)
    (root / ".lifecycle.toml").write_text('[branches]\nintegration = "main"\n', encoding="utf-8")
    return load(root)


@pytest.fixture
def kit_checkout(tmp_path):
    """A checkout of the kit itself: the kit's manifest at its root, its canonical method/."""
    root = tmp_path / "kit-checkout"
    (root / "method").mkdir(parents=True)
    (root / "method" / "task_review.md").write_text("# Task review, canonical\n", encoding="utf-8")
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(
        '{"name": "lifecycle", "version": "9.9.9"}\n', encoding="utf-8"
    )
    (root / ".lifecycle.toml").write_text(
        '[branches]\nintegration = "main"\n',
        encoding="utf-8",
    )
    return load(root)


def name_templates(config, table):
    """``config``'s repository with ``[templates]`` as ``table`` (TOML lines), reloaded."""
    (config.root / ".lifecycle.toml").write_text(f"[templates]\n{table}", encoding="utf-8")
    return load(config.root)


def copy_era(config, kit="1.1.0"):
    """``config``'s repository as it was before 0.8.0: the method copied into its guides
    folder, each file's digest in a lock of the old shape."""
    import json

    digests = {}
    for name in guides.method_files():
        path = config.guides_dir / name
        body = (guides.METHOD / name).read_text(encoding="utf-8")
        path.write_text(body, encoding="utf-8", newline="\n")
        digests[name] = guides.digest(path)
    lock = {"kit": kit, "guides": digests}
    (config.root / guides.LOCK).write_text(json.dumps(lock), encoding="utf-8")


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def commit(cwd, name, text=None):
    (Path(cwd) / f"{name}.txt").write_text(text or name, encoding="utf-8")
    git(cwd, "add", "-A")
    git(cwd, "commit", "-q", "-m", name)
    return git(cwd, "rev-parse", "HEAD")


class Clone:
    """A bare ``origin`` on ``next``, a primary checkout of it, and its linked worktrees."""

    def __init__(self, tmp_path, files=None):
        self.tmp = tmp_path
        seed = tmp_path / "seed"
        seed.mkdir()
        git(seed, "init", "-q", "-b", "next")
        files = {".lifecycle.toml": '[branches]\nintegration = "next"\n', **(files or {})}
        for name, text in files.items():
            (seed / name).parent.mkdir(parents=True, exist_ok=True)
            (seed / name).write_text(text, encoding="utf-8")
        commit(seed, "shared")
        self.origin = tmp_path / "origin.git"
        git(tmp_path, "clone", "-q", "--bare", str(seed), str(self.origin))
        self.primary = tmp_path / "primary"
        git(tmp_path, "clone", "-q", str(self.origin), str(self.primary))

    def worktree(self, name, *extra):
        path = self.tmp / name
        git(self.primary, "worktree", "add", "-q", *extra, str(path), "origin/next")
        return path

    def task(self, name):
        """A linked worktree on a branch of its own, cut from origin's next."""
        return self.worktree(name, "-b", name)

    def land(self, tree, name=None):
        """A commit made in ``tree`` and pushed to origin's next, as complete pushes."""
        made = commit(tree, name or tree.name)
        git(tree, "push", "-q", "origin", "HEAD:next")
        return made

    def elsewhere(self, name):
        """A commit on origin's next made in another clone: a merge on GitHub."""
        other = self.tmp / f"other-{name}"
        if not other.exists():
            git(self.tmp, "clone", "-q", str(self.origin), str(other))
        git(other, "pull", "-q", "--ff-only")
        commit(other, name)
        git(other, "push", "-q", "origin", "HEAD:next")


@pytest.fixture
def clone_of(tmp_path, monkeypatch):
    """Makes a clone on ``next`` with a bare origin, its seed holding ``files`` beside the
    settings; a test makes its linked worktrees."""
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    return lambda files=None: Clone(tmp_path, files)


@pytest.fixture
def clone(clone_of):
    return clone_of()
