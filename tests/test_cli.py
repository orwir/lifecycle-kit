import io
import json
from pathlib import Path

from lifecycle import cli, hook


def run(monkeypatch, capsys, argv, stdin="", cwd=None):
    if cwd:
        monkeypatch.chdir(cwd)
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin.encode("utf-8"))))
    code = cli.main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_outside_the_kit_says_so(monkeypatch, capsys, tmp_path):
    code, _, err = run(monkeypatch, capsys, ["doctor"], cwd=tmp_path)
    assert code == 1 and "not on the kit" in err


def test_doctor_require_current_fails_a_blocked_repo(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["doctor", "--require-current"], cwd=repo.root)
    assert code == 1 and out.startswith("block:")


def test_upgrade_names_changed_templates(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt"], cwd=repo.root)
    assert code == 0 and "templates changed" in out and "agents_template.md" in out


def test_the_pre_bash_hook_blocks_with_exit_2(monkeypatch, capsys):
    event = json.dumps({"tool_input": {"command": "cd /tmp && ls"}})
    code, _, err = run(monkeypatch, capsys, ["hook", "pre-bash"], stdin=event)
    assert code == 2 and "cd <absolute path>" in err


def test_a_broken_guard_blocks_only_the_reviewer(monkeypatch, capsys):
    def broken(event):
        raise RuntimeError("boom")

    monkeypatch.setattr(hook, "pre_bash", broken)
    session = json.dumps({"tool_input": {"command": "ls"}})
    assert run(monkeypatch, capsys, ["hook", "pre-bash"], stdin=session)[0] == 0
    reviewer = json.dumps({"tool_input": {"command": "ls"}, "agent_type": hook.REVIEWER})
    assert run(monkeypatch, capsys, ["hook", "pre-bash"], stdin=reviewer)[0] == 2


def test_the_push_guard_reads_the_protected_branch(monkeypatch, capsys, repo):
    monkeypatch.delenv("PRE_COMMIT_REMOTE_BRANCH", raising=False)
    monkeypatch.chdir(repo.root)
    monkeypatch.setattr("sys.stdin", io.StringIO("refs/heads/x a refs/heads/master b\n"))
    assert cli.main(["guard", "push"]) == 1


def test_config_prints_the_resolved_settings(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["config"], cwd=repo.root)
    assert code == 0 and json.loads(out)["branches"]["protected"] == "master"


def test_dash_c_runs_in_another_directory(monkeypatch, capsys, repo, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["-C", str(repo.root), "config"]) == 0
    assert json.loads(capsys.readouterr().out)["root"] == str(repo.root)


def test_a_reviewer_event_in_any_language_is_read(monkeypatch, capsys, repo):
    event = {"tool_input": {"command": "git stash  # сяэАН"}, "agent_type": hook.REVIEWER}
    event["cwd"] = str(repo.root)
    payload = json.dumps(event, ensure_ascii=False)
    code, _, err = run(monkeypatch, capsys, ["hook", "pre-bash"], stdin=payload)
    assert code == 2 and "BLOCKED for the reviewer" in err


def test_an_unreadable_reviewer_event_still_blocks(monkeypatch, capsys):
    payload = '{"agent_type": "lifecycle:reviewer", "tool_input": {'
    code, _, err = run(monkeypatch, capsys, ["hook", "pre-bash"], stdin=payload)
    assert code == 2 and "guard failed" in err


def test_where_names_the_folder_holding_the_reviewer(monkeypatch, capsys):
    code, out, _ = run(monkeypatch, capsys, ["where"])
    assert code == 0 and (Path(out.strip()) / "agents" / "reviewer.md").is_file()
