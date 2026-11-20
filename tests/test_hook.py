from lifecycle import hook
from lifecycle.guides import upgrade


def bash(command, **event):
    return hook.pre_bash({"tool_input": {"command": command}, **event})


def test_a_here_string_is_blocked():
    assert bash("git commit -m @'\nsubject\n'@") == hook.HERESTRING
    assert bash('x = @"\nbody\n"@') == hook.HERESTRING


def test_an_at_sign_inside_quotes_is_not_a_here_string():
    assert bash("ssh deploy@'host' && echo 'done'@home") is None


def test_cd_to_an_absolute_path_is_blocked():
    assert bash("cd /d/projects/x && git status") == hook.CD_ABSOLUTE
    assert bash('cd "C:\\Users\\x" && ls') == hook.CD_ABSOLUTE
    assert bash("cd ~/x") == hook.CD_ABSOLUTE


def test_a_relative_cd_passes():
    assert bash("cd docs && ls") is None


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


def test_session_start_lists_what_the_kit_changed(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a change\n", encoding="utf-8")
    monkeypatch.setattr(hook.doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(hook.doctor, "kit_version", lambda: "1.3.0")
    text = hook.session_start({"cwd": str(repo.root)})
    assert "the next task upgrades first" in text and "\n  - a change" in text


def test_session_start_says_a_newer_kit_is_out(repo, monkeypatch):
    from lifecycle import latest

    upgrade(repo, adopt=True)
    monkeypatch.setattr(hook.doctor, "kit_version", lambda: "1.2.0")
    monkeypatch.setattr(latest, "latest_release", lambda: "1.4.0")
    assert "kit 1.4.0 is out" in hook.session_start({"cwd": str(repo.root)})


def test_session_start_is_quiet_in_the_kits_own_repository(kit_checkout):
    assert hook.session_start({"cwd": str(kit_checkout.root)}) == ""
