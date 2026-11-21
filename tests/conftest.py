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


@pytest.fixture(autouse=True)
def no_network(tmp_path, monkeypatch):
    """No test reaches the kit's real remote: a guide push clones a remote that is not there."""
    monkeypatch.setenv("LIFECYCLE_KIT_REMOTE", str(tmp_path / "no-kit.git"))


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
        '[branches]\nintegration = "main"\n\n[guides]\npath = "method"\n',
        encoding="utf-8",
    )
    return load(root)


def name_templates(config, table):
    """``config``'s repository with ``[templates]`` as ``table`` (TOML lines), reloaded."""
    (config.root / ".lifecycle.toml").write_text(f"[templates]\n{table}", encoding="utf-8")
    return load(config.root)
