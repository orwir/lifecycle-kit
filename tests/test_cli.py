import io
import json
import subprocess
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
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(doctor, "kit_version", lambda: "1.3.0")
    code, out, _ = run(monkeypatch, capsys, ["doctor"], cwd=repo.root)
    assert code == 0 and out.startswith("block:") and "\n  - a change" in out


def test_doctor_says_nothing_of_a_release_that_asks_nothing(monkeypatch, capsys, repo, tmp_path):
    from lifecycle import doctor, guides

    guides.upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a change\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(doctor, "kit_version", lambda: "1.3.0")
    code, out, _ = run(monkeypatch, capsys, ["doctor"], cwd=repo.root)
    assert code == 0 and out.startswith("on kit ") and out.endswith(", nothing to do\n")


def test_a_first_upgrade_names_each_template_to_port_and_where_to_read_it(
    monkeypatch, capsys, repo
):
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt"], cwd=repo.root)
    assert code == 0 and out.startswith("kit none -> 1.2.0\n")
    assert "port agents_template.md -> AGENTS.md, read whole: " in out


def test_the_pre_bash_hook_blocks_with_exit_2(monkeypatch, capsys, repo):
    event = {"tool_input": {"command": "git stash"}, "agent_type": hook.REVIEWER}
    event["cwd"] = str(repo.root)
    code, _, err = run(monkeypatch, capsys, ["hook", "pre-bash"], stdin=json.dumps(event))
    assert code == 2 and "BLOCKED for the reviewer" in err


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
    (repo.root / "AGENTS.md").write_text("# AGENTS\nours\n", encoding="utf-8")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    (guides.METHOD / "agents_template.md").write_text("# AGENTS, new\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    code, out, _ = run(monkeypatch, capsys, ["upgrade"], cwd=repo.root)
    assert code == 0 and "replaced with the new template, unchanged since the old: .github/" in out
    assert "port agents_template.md -> AGENTS.md, by what the template changed:" in out
    assert "-# AGENTS\n+# AGENTS, new\n" in out and "port pr_template.md" not in out


def test_the_move_from_copies_names_what_it_deletes(monkeypatch, capsys, repo):
    from conftest import copy_era

    copy_era(repo, kit="1.2.0")
    code, out, _ = run(monkeypatch, capsys, ["upgrade"], cwd=repo.root)
    assert code == 0 and "deleted the kit's copy in docs/guides: agents_template.md" in out


def test_the_removed_subcommands_are_usage_errors(monkeypatch, capsys, repo):
    monkeypatch.chdir(repo.root)
    for argv in (["upgraded"], ["guides", "check"], ["guides", "push", "-F", "x"]):
        with pytest.raises(SystemExit) as exited:
            cli.main(argv)
        assert exited.value.code == 2 and "invalid choice" in capsys.readouterr().err


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


def test_named_templates_replace_the_defaults_on_the_port_line(monkeypatch, capsys, repo):
    from conftest import name_templates
    from lifecycle import guides

    name_templates(repo, '"idea_gauntlet.md" = "AGENTS.md"\n')
    (guides.METHOD / "idea_gauntlet.md").write_text("# Gauntlet\n", encoding="utf-8")
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt"], cwd=repo.root)
    assert code == 0 and "port idea_gauntlet.md -> AGENTS.md" in out
    assert "agents_template.md" not in out


def test_config_prints_the_templates(monkeypatch, capsys, repo):
    code, out, _ = run(monkeypatch, capsys, ["config"], cwd=repo.root)
    templates = json.loads(out)["templates"]
    assert code == 0 and templates["pr_template.md"] == ".github/pull_request_template.md"


def test_doctor_and_session_start_ask_no_remote(monkeypatch, capsys, repo):
    from lifecycle import guides

    started = []
    real = subprocess.Popen

    class Recorded(real):
        def __init__(self, args, *rest, **kwargs):
            started.append(args if isinstance(args, str) else " ".join(map(str, args)))
            super().__init__(args, *rest, **kwargs)

    guides.upgrade(repo, adopt=True)
    monkeypatch.setattr(subprocess, "Popen", Recorded)
    assert run(monkeypatch, capsys, ["doctor"], cwd=repo.root)[0] == 0
    hook.session_start({"cwd": str(repo.root)})
    assert [command for command in started if "ls-remote" in command] == []


def test_a_dry_run_says_what_it_would_do(monkeypatch, capsys, repo):
    from conftest import copy_era

    copy_era(repo, kit="1.2.0")
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--dry-run"], cwd=repo.root)
    assert code == 0 and "(dry run)" in out and "would delete the kit's copy" in out
    assert (repo.guides_dir / "agents_template.md").is_file()


def test_an_upgrade_with_nothing_to_change_says_so(monkeypatch, capsys, repo):
    from lifecycle import guides

    guides.upgrade(repo, adopt=True)
    code, out, _ = run(monkeypatch, capsys, ["upgrade"], cwd=repo.root)
    assert code == 0 and out.endswith("nothing to change beyond the lock\n")
