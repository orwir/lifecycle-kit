"""`lifecycle base` is the commit the work round measures a task from: where HEAD forked
from the integration branch, read here or on origin, whichever exists, never from a stale
local branch alone. The review skill and the hand-off packet take it from there."""

import re
import subprocess
from pathlib import Path

import pytest
from lifecycle import cli
from lifecycle.base import BaseError, base

KIT = Path(__file__).resolve().parents[1]


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def commit(cwd, message):
    (Path(cwd) / "f.txt").write_text(message, encoding="utf-8")
    git(cwd, "add", "-A")
    git(cwd, "commit", "-q", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


@pytest.fixture
def origin(tmp_path, monkeypatch):
    """A repository with three commits on ``main``, which clones take as ``origin``."""
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    root = tmp_path / "origin"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    for n in (1, 2, 3):
        commit(root, f"c{n}")
    return root


def on_next(origin):
    """A commit on ``next`` in ``origin``, which a clone then fetches but does not check out."""
    git(origin, "switch", "-q", "-c", "next")
    forked = commit(origin, "c4 on next")
    git(origin, "switch", "-q", "main")
    return forked


def clone(origin, tmp_path):
    root = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(origin), str(root)], check=True)
    return root


def test_a_stale_local_branch_gives_way_to_origins_fork_point(origin, tmp_path):
    root = clone(origin, tmp_path)
    git(root, "reset", "-q", "--hard", "HEAD~2")
    git(root, "switch", "-q", "-c", "task", "origin/main")
    commit(root, "the task")
    assert base(root, "main") == git(origin, "rev-parse", "main")


def test_with_no_local_branch_the_fork_point_is_origins(origin, tmp_path):
    forked = on_next(origin)
    root = clone(origin, tmp_path)
    git(root, "switch", "-q", "-c", "task", "origin/next")
    commit(root, "the task")
    assert git(root, "branch", "--list", "next") == ""
    assert base(root, "next") == forked


def test_with_no_origin_remote_the_fork_point_is_the_local_branchs(origin):
    forked = git(origin, "rev-parse", "HEAD")
    git(origin, "switch", "-q", "-c", "task")
    commit(origin, "the task")
    assert base(origin, "main") == forked


def test_local_commits_not_yet_pushed_stay_in_the_base(origin, tmp_path):
    root = clone(origin, tmp_path)
    unpushed = commit(root, "local only")
    git(root, "switch", "-q", "-c", "task")
    commit(root, "the task")
    assert base(root, "main") == unpushed


def test_a_tag_named_like_the_branch_never_stands_in(origin, tmp_path):
    forked = on_next(origin)
    root = clone(origin, tmp_path)
    git(root, "switch", "-q", "-c", "task", "origin/next")
    commit(root, "the task")
    git(root, "tag", "next")
    assert base(root, "next") == forked


def test_on_the_integration_branch_the_base_is_heads_full_sha(origin, tmp_path):
    root = clone(origin, tmp_path)
    git(root, "reset", "-q", "--hard", "HEAD~1")
    head = git(root, "rev-parse", "HEAD")
    assert base(root, "main") == head and len(head) == 40


def test_lifecycle_base_prints_the_sha(origin, tmp_path, monkeypatch, capsys):
    root = clone(origin, tmp_path)
    (root / ".lifecycle.toml").write_text('[branches]\nintegration = "main"\n', encoding="utf-8")
    git(root, "switch", "-q", "-c", "task")
    commit(root, "the task")
    monkeypatch.chdir(root)
    assert cli.main(["base"]) == 0
    assert capsys.readouterr().out == git(origin, "rev-parse", "main") + "\n"


def test_no_integration_branch_anywhere_exits_1_and_says_to_fetch(
    origin, tmp_path, monkeypatch, capsys
):
    root = clone(origin, tmp_path)
    (root / ".lifecycle.toml").write_text('[branches]\nintegration = "trunk"\n', encoding="utf-8")
    monkeypatch.chdir(root)
    assert cli.main(["base"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("lifecycle: neither trunk nor origin/trunk is a branch in this clone")
    assert "`git fetch origin`" in err


def test_a_branch_sharing_no_commit_with_it_exits_1_and_says_to_fetch(
    origin, tmp_path, monkeypatch, capsys
):
    root = clone(origin, tmp_path)
    (root / ".lifecycle.toml").write_text('[branches]\nintegration = "main"\n', encoding="utf-8")
    git(root, "switch", "-q", "--orphan", "unrelated")
    commit(root, "a history of its own")
    monkeypatch.chdir(root)
    assert cli.main(["base"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("lifecycle: HEAD shares no commit with main or origin/main")
    assert "`git fetch origin`" in err


@pytest.mark.parametrize("where", ["a branch with no commit yet", "no git repository"])
def test_no_commit_at_head_is_refused_as_such(origin, tmp_path, monkeypatch, where):
    if where == "no git repository":
        root = tmp_path / "plain"
        root.mkdir()
        monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    else:
        root = clone(origin, tmp_path)
        git(root, "switch", "-q", "--orphan", "empty")
    with pytest.raises(BaseError, match=r"^no commit at HEAD \(not a git repository, or no"):
        base(root, "main")


def test_the_work_round_reads_its_base_only_from_lifecycle_base():
    """A skill or guide that runs ``merge-base`` itself reads the integration branch by a
    name that can be stale or missing here: the base comes from ``lifecycle base``."""
    texts = {
        path.relative_to(KIT).as_posix(): path.read_text(encoding="utf-8")
        for folder in ("skills", "method")
        for path in sorted((KIT / folder).rglob("*.md"))
    }
    assert [path for path, text in texts.items() if "merge-base" in text] == []
    review = texts["skills/review/SKILL.md"]
    assert "`lifecycle base`" in review and "git diff --stat <base>" in review
    assert re.search(
        r"^Diff: git diff HEAD \| git diff <the base", texts["method/task_review.md"], re.M
    )
