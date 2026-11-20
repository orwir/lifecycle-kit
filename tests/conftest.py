import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from lifecycle import guides
from lifecycle.config import load


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repository on the kit with a two-file method at release 1.2.0."""
    method = tmp_path / "kit" / "method"
    method.mkdir(parents=True)
    (method / "task_review.md").write_text("# Task review\n", encoding="utf-8")
    (method / "agents_template.md").write_text("# AGENTS\n", encoding="utf-8")
    monkeypatch.setattr(guides, "METHOD", method)
    monkeypatch.setattr(guides, "kit_version", lambda: "1.2.0")
    root = tmp_path / "repo"
    (root / "docs" / "guides").mkdir(parents=True)
    (root / ".lifecycle.toml").write_text('[branches]\nprotected = "master"\n', encoding="utf-8")
    return load(root)
