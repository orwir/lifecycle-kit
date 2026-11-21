import io
import json
from pathlib import Path

import pytest
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


def test_doctor_prints_each_finding_and_its_details(monkeypatch, capsys, repo, tmp_path):
    from lifecycle import doctor, guides

    guides.upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a change\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(doctor, "kit_version", lambda: "1.3.0")
    code, out, _ = run(monkeypatch, capsys, ["doctor"], cwd=repo.root)
    assert code == 0 and out.startswith("block:") and "\n  - a change" in out


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


def test_the_guards_are_gone(monkeypatch, capsys, repo):
    monkeypatch.chdir(repo.root)
    with pytest.raises(SystemExit) as exited:
        cli.main(["guard", "push"])
    assert exited.value.code == 2 and "invalid choice: 'guard'" in capsys.readouterr().err


def test_config_prints_the_resolved_settings(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["config"], cwd=repo.root)
    assert code == 0 and json.loads(out)["branches"] == {"integration": "main"}


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


def test_doctor_json_names_the_fix_of_a_repo_not_on_the_kit(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["doctor", "--json"], cwd=repo.root)
    assert code == 0 and json.loads(out)[0]["fix"] == "adopt"


def test_upgrade_names_installed_templates_and_leaves_them_off_the_port_list(
    monkeypatch, capsys, repo
):
    from lifecycle import guides

    guides.upgrade(repo, adopt=True)
    installed = repo.root / ".github" / "pull_request_template.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("a\nb\nc\nd\n", encoding="utf-8")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    (guides.METHOD / "agents_template.md").write_text("# AGENTS, new\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    code, out, _ = run(monkeypatch, capsys, ["upgrade"], cwd=repo.root)
    assert code == 0 and "installed unchanged from the old template: .github/" in out
    port_line = next(line for line in out.splitlines() if line.startswith("templates changed"))
    assert "agents_template.md" in port_line and "pr_template.md" not in port_line


def test_upgraded_reports_a_first_upgrade_from_no_lock(monkeypatch, capsys, repo):
    from lifecycle import guides

    guides.upgrade(repo, adopt=True)
    code, out, _ = run(monkeypatch, capsys, ["upgraded"], cwd=repo.root)
    assert code == 0 and "kit none -> 1.2.0" in out


def test_doctor_says_a_newer_kit_is_out(monkeypatch, capsys, repo):
    from lifecycle import doctor, guides, latest

    guides.upgrade(repo, adopt=True)
    monkeypatch.setattr(doctor, "kit_version", lambda: "1.2.0")
    monkeypatch.setattr(latest, "latest_release", lambda: "1.4.0")
    code, out, _ = run(monkeypatch, capsys, ["doctor"], cwd=repo.root)
    assert code == 0 and "kit 1.4.0 is out" in out


def test_upgraded_names_what_the_release_requires(monkeypatch, capsys, repo):
    from lifecycle import doctor

    found = {"from": "1.2.0", "to": "1.3.0", "changes": [], "required": ["add a hook"],
             "guides": [], "deleted": [], "installed": []}  # fmt: skip
    monkeypatch.setattr(doctor, "upgraded", lambda config, base=None: found)
    code, out, _ = run(monkeypatch, capsys, ["upgraded"], cwd=repo.root)
    assert code == 0 and "required of this repository: add a hook" in out


def test_output_is_utf8_whatever_the_console_page(tmp_path):
    import os
    import subprocess
    import sys

    folder = tmp_path / "проект"
    folder.mkdir()
    (folder / ".lifecycle.toml").write_text("", encoding="utf-8")
    tools = Path(__file__).resolve().parents[1] / "tools" / "lifecycle"
    result = subprocess.run(
        [sys.executable, str(tools), "-C", str(folder), "config"],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
        check=False,
    )
    assert result.returncode == 0 and "проект" in result.stdout.decode("utf-8")


def test_the_port_line_names_each_template_with_its_target(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt"], cwd=repo.root)
    port_line = next(line for line in out.splitlines() if line.startswith("templates changed"))
    assert code == 0 and "agents_template.md -> AGENTS.md" in port_line


def test_named_templates_replace_the_defaults_on_the_port_line(monkeypatch, capsys, repo):
    from conftest import name_templates
    from lifecycle import guides

    name_templates(repo, '"idea_gauntlet.md" = "AGENTS.md"\n')
    (guides.METHOD / "idea_gauntlet.md").write_text("# Gauntlet\n", encoding="utf-8")
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt"], cwd=repo.root)
    port_line = next(line for line in out.splitlines() if line.startswith("templates changed"))
    assert code == 0 and "idea_gauntlet.md -> AGENTS.md" in port_line
    assert "agents_template.md" not in port_line


def test_config_prints_the_templates(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["config"], cwd=repo.root)
    templates = json.loads(out)["templates"]
    assert code == 0 and templates["pr_template.md"] == ".github/pull_request_template.md"
