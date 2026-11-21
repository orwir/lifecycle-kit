import re
import subprocess

from conftest import name_templates
from lifecycle import doctor, guides
from lifecycle.guides import read_lock, upgrade, write_lock


def levels(findings):
    return [finding.level for finding in findings]


def test_current_and_clean_says_nothing(repo):
    upgrade(repo, adopt=True)
    assert doctor.check(repo, installed="1.2.0") == []


def test_a_minor_release_behind_blocks_a_round(repo):
    upgrade(repo, adopt=True)
    assert levels(doctor.check(repo, installed="1.3.0")) == [doctor.BLOCK]


def test_a_patch_release_behind_is_a_note(repo):
    upgrade(repo, adopt=True)
    assert levels(doctor.check(repo, installed="1.2.4")) == [doctor.NOTE]


def test_an_installed_kit_older_than_the_repo_blocks(repo):
    upgrade(repo, adopt=True)
    assert "update the kit" in doctor.check(repo, installed="1.1.9")[0].message


def test_an_unpushed_edit_is_named(repo):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("changed\n", encoding="utf-8")
    assert "task_review.md" in doctor.check(repo, installed="1.2.0")[0].message


def test_a_repo_not_on_the_kit_blocks(repo):
    assert levels(doctor.check(repo, installed="1.2.0")) == [doctor.BLOCK]


def test_a_gist_mirror_stops_for_its_own_move(repo):
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert "gist" in finding.message and finding.fix == doctor.ADOPT


def test_a_finding_names_its_fix_and_what_changed(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## v1.3.0\n\n- skills upgrade inside the task\n\n"
        "## v1.2.1\n\n- a guide wording fix\n\n## v1.2.0\n\n- already here\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (finding,) = doctor.check(repo, installed="1.3.0")
    assert (finding.level, finding.fix) == (doctor.BLOCK, doctor.UPGRADE)
    assert finding.details == ("skills upgrade inside the task", "a guide wording fix")


def test_a_patch_behind_also_names_the_upgrade(repo):
    upgrade(repo, adopt=True)
    assert doctor.check(repo, installed="1.2.4")[0].fix == doctor.UPGRADE


def test_a_long_list_of_changes_is_cut(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    lines = "".join(f"- change {n}\n" for n in range(12))
    (tmp_path / "CHANGELOG.md").write_text(f"## v1.3.0\n\n{lines}", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    details = doctor.check(repo, installed="1.3.0")[0].details
    assert len(details) == doctor.CHANGES_SHOWN + 1 and "4 more" in details[-1]


def pushed(repo, release):
    lock = read_lock(repo.root)
    lock.pushed = {"task_review.md": release}
    write_lock(repo.root, lock)


def test_the_note_after_a_guide_push_stops_nothing(repo):
    upgrade(repo, adopt=True)
    pushed(repo, "1.2.1")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.UPDATE_KIT)


def test_behind_with_a_push_still_out_needs_the_kit_updated_first(repo):
    upgrade(repo, adopt=True)
    pushed(repo, "1.3.1")
    (finding,) = doctor.check(repo, installed="1.3.0")
    assert (finding.level, finding.fix) == (doctor.BLOCK, doctor.UPDATE_KIT)
    pushed(repo, "1.2.2")
    (finding,) = doctor.check(repo, installed="1.2.1")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.UPDATE_KIT)


def test_an_installed_kit_older_than_the_pin_needs_updating(repo):
    upgrade(repo, adopt=True)
    assert doctor.check(repo, installed="1.1.0")[0].fix == doctor.UPDATE_KIT


def test_a_heading_in_another_shape_lends_its_entries_to_no_release(monkeypatch, tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.4.0 — dated\n\n- dropped\n\n## v1.3.0\n\n- taken\n", encoding="utf-8"
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    assert doctor.changes_since("1.2.0", "1.4.0") == ["taken"]


def test_every_release_heading_in_the_kit_changelog_is_read():
    lines = (doctor.KIT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    headings = [line for line in lines if line.startswith("## ")]
    assert headings and all(doctor._HEADING.match(line) for line in headings)


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def test_an_upgrade_in_the_tree_is_read_from_the_tree(repo, monkeypatch, tmp_path):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    upgrade(repo, adopt=True)
    installed = repo.root / ".github" / "pull_request_template.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("a\nb\nc\nd\n", encoding="utf-8")
    git(repo.root, "init", "-q")
    git(repo.root, "add", "-A")
    git(repo.root, "commit", "-q", "-m", "on 1.2.0")
    assert doctor.upgraded(repo) is None
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a change\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    upgrade(repo)
    assert doctor.upgraded(repo) == {
        "from": "1.2.0",
        "to": "1.3.0",
        "changes": ["a change"],
        "required": [],
        "guides": ["pr_template.md"],
        "deleted": [],
        "installed": [".github/pull_request_template.md"],
    }


def committed_repo(repo, monkeypatch):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    upgrade(repo, adopt=True)
    git(repo.root, "init", "-q", "-b", "main")
    git(repo.root, "add", "-A")
    git(repo.root, "commit", "-q", "-m", "on 1.2.0")


def test_no_upgrade_when_the_lock_matches_the_base(repo, monkeypatch, capsys):
    from lifecycle import cli

    committed_repo(repo, monkeypatch)
    monkeypatch.chdir(repo.root)
    assert cli.main(["upgraded"]) == 0
    assert "no upgrade the integration branch lacks" in capsys.readouterr().out


def test_an_upgrade_in_a_wip_commit_on_a_branch_still_counts(repo, monkeypatch):
    committed_repo(repo, monkeypatch)
    git(repo.root, "switch", "-q", "-c", "feat/x")
    (guides.METHOD / "task_review.md").write_text("# Task review, 1.3\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    upgrade(repo)
    git(repo.root, "commit", "-q", "-am", "wip")
    found = doctor.upgraded(repo)
    assert (found["from"], found["to"], found["guides"]) == ("1.2.0", "1.3.0", ["task_review.md"])


def test_the_tasks_own_guide_edits_are_not_the_kits(repo, monkeypatch):
    committed_repo(repo, monkeypatch)
    (guides.METHOD / "task_review.md").write_text("# Task review, 1.3\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    upgrade(repo)
    (repo.guides_dir / "agents_template.md").write_text("# AGENTS, ours\n", encoding="utf-8")
    assert doctor.upgraded(repo)["guides"] == ["task_review.md"]


def test_a_guide_the_kit_dropped_is_listed_as_deleted(repo, monkeypatch):
    committed_repo(repo, monkeypatch)
    (guides.METHOD / "agents_template.md").unlink()
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    upgrade(repo)
    assert doctor.upgraded(repo)["deleted"] == ["agents_template.md"]


def test_a_newer_kit_out_is_a_note_that_stops_nothing(repo):
    upgrade(repo, adopt=True)
    (finding,) = doctor.check(repo, installed="1.2.0", latest="1.3.0")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.UPDATE_KIT)
    assert "1.3.0 is out" in finding.message
    assert doctor.check(repo, installed="1.2.0", latest="1.2.0") == []
    assert doctor.check(repo, installed="1.2.0", latest="1.1.9") == []


def test_one_remedy_is_said_once(repo):
    upgrade(repo, adopt=True)
    findings = doctor.check(repo, installed="1.1.0", latest="1.3.0")
    assert [f.fix for f in findings] == [doctor.UPDATE_KIT] and "is out" not in findings[0].message


def test_repositories_lines_are_shown_past_the_cut(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    lines = "".join(f"- change {n}\n" for n in range(12)) + "- Repositories: add a hook\n"
    (tmp_path / "CHANGELOG.md").write_text(f"## v1.3.0\n\n{lines}", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    details = doctor.check(repo, installed="1.3.0")[0].details
    assert details[0] == "Repositories: add a hook" and len(details) == doctor.CHANGES_SHOWN + 1


def test_a_release_names_what_every_repository_must_change(repo, monkeypatch, tmp_path):
    committed_repo(repo, monkeypatch)
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.3.0\n\n- Repositories: allow `lifecycle upgraded` in .claude/settings.json\n"
        "- a change\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    (guides.METHOD / "task_review.md").write_text("# Task review, 1.3\n", encoding="utf-8")
    upgrade(repo)
    assert doctor.upgraded(repo)["required"] == [
        "allow `lifecycle upgraded` in .claude/settings.json"
    ]


def test_every_repositories_line_names_the_file_it_changes():
    lines = (doctor.KIT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    required = [line for line in lines if line.startswith("- " + doctor.REPOSITORIES)]
    named = re.compile(r"`[^`\s]*[./][^`\s]*`")
    assert required and all(named.search(line) for line in required)


def test_a_first_move_owes_every_repositories_line_up_to_its_release(repo, monkeypatch, tmp_path):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    git(repo.root, "init", "-q", "-b", "main")
    git(repo.root, "add", "-A")
    git(repo.root, "commit", "-q", "-m", "before the kit")
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.3.0\n\n- Repositories: a later line in `later.toml`\n\n"
        "## v1.2.0\n\n- Repositories: add `b.json`\n- a change\n\n"
        "## v1.1.0\n\n- Repositories: add `a.cfg`\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    upgrade(repo, adopt=True)
    found = doctor.upgraded(repo)
    assert (found["from"], found["to"], found["changes"]) == (None, "1.2.0", [])
    assert found["required"] == ["add `b.json`", "add `a.cfg`"]


def test_templates_installed_whole_follow_the_mapping(repo, monkeypatch):
    repo = name_templates(repo, '"pr_template.md" = "docs/pr.md"\n')
    (repo.root / "docs" / "pr.md").write_text("a\nb\nc\nd\n", encoding="utf-8")
    committed_repo(repo, monkeypatch)
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    upgrade(repo)
    assert doctor.upgraded(repo)["installed"] == ["docs/pr.md"]


def test_the_kits_own_repository_asks_for_no_lock(kit_checkout):
    assert doctor.check(kit_checkout, installed="9.9.9") == []
    (finding,) = doctor.check(kit_checkout, installed="9.9.9", latest="10.0.0")
    assert finding.fix == doctor.UPDATE_KIT


def test_a_method_folder_without_the_kits_manifest_is_any_repository(kit_checkout):
    manifest = kit_checkout.root / ".claude-plugin" / "plugin.json"
    for body in ('{"name": "another-plugin"}', "{not json", "[]"):
        manifest.write_text(body, encoding="utf-8")
        assert [f.fix for f in doctor.check(kit_checkout, installed="9.9.9")] == [doctor.ADOPT]
    manifest.unlink()
    assert [f.fix for f in doctor.check(kit_checkout, installed="9.9.9")] == [doctor.ADOPT]


def test_a_repo_not_on_the_kit_is_shown_every_line_it_will_owe(repo, monkeypatch, tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.3.0\n\n- Repositories: a later line in `later.toml`\n\n"
        "## v1.2.0\n\n- Repositories: add `b.json`\n- a change\n\n"
        "## v1.1.0\n\n- Repositories: add `a.cfg`\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    owed = ("Repositories: add `b.json`", "Repositories: add `a.cfg`")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert (finding.fix, finding.details) == (doctor.ADOPT, owed)
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert "gist" in finding.message and (finding.fix, finding.details) == (doctor.ADOPT, owed)


def test_the_kit_notes_an_installed_kit_older_than_its_release(kit_checkout, monkeypatch):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    git(kit_checkout.root, "init", "-q", "-b", "main")
    git(kit_checkout.root, "add", "-A")
    git(kit_checkout.root, "commit", "-q", "-m", "v9.9.9")
    (finding,) = doctor.check(kit_checkout, installed="9.9.8", latest="9.9.9")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.UPDATE_KIT)
    assert "main is at 9.9.9" in finding.message and "9.9.8" in finding.message
    assert doctor.check(kit_checkout, installed="9.9.9") == []
    manifest = kit_checkout.root / ".claude-plugin" / "plugin.json"
    manifest.write_text('{"name": "lifecycle", "version": "10.0.0"}\n', encoding="utf-8")
    assert doctor.check(kit_checkout, installed="9.9.9") == []
