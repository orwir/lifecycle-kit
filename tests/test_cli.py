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
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.3.0\n\n### Removed\n- `lifecycle gone`\n", encoding="utf-8"
    )
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(doctor, "kit_version", lambda: "1.3.0")
    code, out, _ = run(monkeypatch, capsys, ["doctor"], cwd=repo.root)
    assert code == 0 and out.startswith("block:") and "\n  - Removed: `lifecycle gone`" in out
    code, out, _ = run(monkeypatch, capsys, ["doctor", "--json"], cwd=repo.root)
    assert code == 0 and "Removed: `lifecycle gone`" in json.loads(out)[0]["details"]


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


def test_a_first_move_names_what_it_keeps_to_compare(monkeypatch, capsys, repo):
    (repo.guides_dir / "task_review.md").write_text("our own\n", encoding="utf-8")
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt", "--dry-run"], cwd=repo.root)
    keeps = (
        "named like the kit's but not its text, to compare with the kit's: "
        "docs/guides/task_review.md"
    )
    assert code == 0 and f"would keep, {keeps}\n" in out and "delete" not in out
    code, out, _ = run(monkeypatch, capsys, ["upgrade", "--adopt"], cwd=repo.root)
    assert code == 0 and f"kept, {keeps}\n" in out
    assert (repo.guides_dir / "task_review.md").is_file()


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


SETUP_REPO = {
    "id": "R",
    "nameWithOwner": "o/r",
    "name": "r",
    "owner": {"login": "o"},
    "visibility": "PUBLIC",
    "url": "https://github.com/o/r",
}


def fake_setup(monkeypatch, public=False, parked=(), rename=None):
    from lifecycle import board

    seen = {}
    monkeypatch.setattr(board, "gh", lambda *args, stdin=None: json.dumps(SETUP_REPO))

    def setup(repo, owner, number, report):
        seen.update(owner=owner, number=number)
        report("cards to write: 1")
        done = board.Setup(owner or "o", number or 7, "https://github.com/users/o/projects/7")
        done.workflows, done.public = ['turn on "Item closed" with Status: Done'], public
        done.parked, done.rename = list(parked), rename
        return done

    monkeypatch.setattr(board, "setup", setup)
    return seen


def test_board_setup_runs_with_no_settings_file(monkeypatch, capsys, tmp_path):
    seen = fake_setup(monkeypatch)
    code, out, _ = run(monkeypatch, capsys, ["board", "setup"], cwd=tmp_path)
    assert code == 0 and seen == {"owner": None, "number": None}
    assert out.splitlines()[0] == "cards to write: 1"
    assert '  [board]\n  owner = "o"\n  number = 7\n' in out
    assert "/projects/7/workflows" in out and '  turn on "Item closed" with Status: Done' in out
    assert "gh project edit 7 --owner o --visibility PUBLIC" in out


def test_board_setup_runs_where_the_settings_name_no_board(monkeypatch, capsys, repo):
    fake_setup(monkeypatch, public=True)
    code, out, _ = run(monkeypatch, capsys, ["board", "setup", "--number", "4"], cwd=repo.root)
    assert code == 0 and "number = 4" in out and "--visibility" not in out


def test_board_setup_fixes_the_board_the_settings_name(monkeypatch, capsys, repo):
    (repo.root / ".lifecycle.toml").write_text(
        '[branches]\nintegration = "main"\n\n[board]\nowner = "team"\nnumber = 9\n',
        encoding="utf-8",
    )
    seen = fake_setup(monkeypatch)
    code, out, _ = run(monkeypatch, capsys, ["board", "setup"], cwd=repo.root)
    assert code == 0 and seen == {"owner": "team", "number": 9} and "[board]" not in out


PARKED = "left in Backlog though its plan has a status: 2 card(s); the maintainer's call to move"


def test_board_setup_lists_the_cards_it_left_in_backlog_under_a_plan(monkeypatch, capsys, repo):
    (repo.root / ".lifecycle.toml").write_text(
        '[branches]\nintegration = "main"\n\n[board]\nowner = "team"\nnumber = 9\n',
        encoding="utf-8",
    )
    fake_setup(monkeypatch, parked=[12, 3])
    code, out, _ = run(monkeypatch, capsys, ["board", "setup"], cwd=repo.root)
    assert code == 0 and f"{PARKED} each one under way:\n" in out
    assert '  lifecycle board 3 "In Progress"\n  lifecycle board 12 "In Progress"\n' in out


def test_the_moves_for_another_board_wait_for_its_board_lines(monkeypatch, capsys, repo):
    (repo.root / ".lifecycle.toml").write_text(
        '[branches]\nintegration = "main"\n\n[board]\nowner = "team"\nnumber = 9\n',
        encoding="utf-8",
    )
    fake_setup(monkeypatch, parked=[12, 3])
    code, out, _ = run(monkeypatch, capsys, ["board", "setup", "--number", "4"], cwd=repo.root)
    tail = f"{PARKED} each one under way, once .lifecycle.toml names this board:\n"
    assert code == 0 and out.index("number = 4") < out.index(tail)


def test_board_setup_with_nothing_left_in_backlog_lists_nothing(monkeypatch, capsys, tmp_path):
    fake_setup(monkeypatch)
    code, out, _ = run(monkeypatch, capsys, ["board", "setup"], cwd=tmp_path)
    assert code == 0 and "left in Backlog" not in out and "rename" not in out


def test_board_setup_names_the_rename_of_a_fresh_table_view(monkeypatch, capsys, tmp_path):
    fake_setup(monkeypatch, rename="https://github.com/users/o/projects/7/views/1")
    code, out, _ = run(monkeypatch, capsys, ["board", "setup"], cwd=tmp_path)
    assert (
        code == 0
        and (
            'in the web UI, https://github.com/users/o/projects/7/views/1: rename "View 1" to '
            '"Table" (no API renames a view)\n'
        )
        in out
    )


def test_board_moves_a_card_by_its_number(monkeypatch, capsys, repo):
    from lifecycle import board

    (repo.root / ".lifecycle.toml").write_text(
        '[branches]\nintegration = "main"\n\n[board]\nowner = "o"\nnumber = 9\n', encoding="utf-8"
    )
    moved = []
    monkeypatch.setattr(board, "move", lambda *args: moved.append(args) or "ITEM")
    code, out, _ = run(monkeypatch, capsys, ["board", "4", "In Progress"], cwd=repo.root)
    assert code == 0 and moved == [(4, "In Progress", "o", 9)] and "#4: In Progress" in out


@pytest.mark.parametrize(
    ("argv", "says"),
    [
        (["board", "setup", "Done"], "takes no column"),
        (["board", "4"], "needs a column"),
        (["board", "four", "Done"], "not an issue number or setup"),
        (["board", "4", "Done", "--number", "3"], "--number is setup's"),
    ],
)
def test_a_board_call_out_of_shape_is_a_usage_error(monkeypatch, capsys, repo, argv, says):
    monkeypatch.chdir(repo.root)
    with pytest.raises(SystemExit) as exited:
        cli.main(argv)
    assert exited.value.code == 2 and says in capsys.readouterr().err
