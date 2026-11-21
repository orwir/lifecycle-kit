from lifecycle import hook
from lifecycle.guides import upgrade


def bash(command, **event):
    return hook.pre_bash({"tool_input": {"command": command}, **event})


def test_a_sessions_here_string_passes_the_kits_hook():
    assert bash("git commit -m @'\nsubject\n'@") is None


def test_a_sessions_cd_prefix_passes_the_kits_hook():
    assert bash("cd /d/projects/x && git status") is None


def test_the_main_session_may_write():
    assert bash("pytest tests/ && git stash") is None


def test_the_reviewer_may_only_read(repo):
    cwd = str(repo.root)
    assert bash("git diff", agent_type=hook.REVIEWER, cwd=cwd) is None
    assert "BLOCKED for the reviewer" in bash("git stash", agent_type=hook.REVIEWER, cwd=cwd)


def test_the_reviewer_runs_the_repository_checks(repo):
    (repo.root / ".lifecycle.toml").write_text(
        '[review]\nallow = ["make lint"]\n', encoding="utf-8"
    )
    assert bash("make lint", agent_type=hook.REVIEWER, cwd=str(repo.root)) is None


def test_session_start_is_quiet_outside_the_kit(tmp_path):
    assert hook.session_start({"cwd": str(tmp_path)}) == ""


def test_session_start_names_what_waits(repo):
    assert "lifecycle upgrade" in hook.session_start({"cwd": str(repo.root)})


def test_session_start_is_quiet_when_current(repo, monkeypatch):
    upgrade(repo, adopt=True)
    monkeypatch.setattr(hook.doctor, "kit_version", lambda: "1.2.0")
    assert hook.session_start({"cwd": str(repo.root)}) == ""


def test_session_start_says_nothing_of_a_release_that_asks_nothing(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a change\n", encoding="utf-8")
    monkeypatch.setattr(hook.doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(hook.doctor, "kit_version", lambda: "1.3.0")
    assert hook.session_start({"cwd": str(repo.root)}) == ""


def test_session_start_lists_what_an_owed_upgrade_brings(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a change\n", encoding="utf-8")
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(hook.doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(hook.doctor, "kit_version", lambda: "1.3.0")
    text = hook.session_start({"cwd": str(repo.root)})
    assert "runs the upgrade skill" in text and "\n  - a change" in text


def test_session_start_is_quiet_in_the_kits_own_repository(kit_checkout):
    assert hook.session_start({"cwd": str(kit_checkout.root)}) == ""
