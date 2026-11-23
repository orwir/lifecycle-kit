import subprocess

import pytest
from conftest import commit, copy_era
from lifecycle import changelog, doctor, guides, kit_repository
from lifecycle.config import load
from lifecycle.guides import upgrade


def levels(findings):
    return [finding.level for finding in findings]


def test_current_and_clean_says_nothing(repo):
    upgrade(repo, adopt=True)
    assert doctor.check(repo, installed="1.2.0") == []


def test_a_release_that_asks_nothing_is_silent(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text("## v1.3.0\n\n- a skill changed\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    assert doctor.check(repo, installed="1.3.0") == []


def test_a_changed_guide_asks_nothing(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    upgrade(repo, adopt=True)
    (guides.METHOD / "task_review.md").write_text("# Task review, 1.3\n", encoding="utf-8")
    assert doctor.check(repo, installed="1.3.0") == []


def test_a_step_owes_an_upgrade(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (finding,) = doctor.check(repo, installed="1.3.0")
    assert (finding.level, finding.fix) == (doctor.BLOCK, doctor.UPGRADE)
    assert finding.details == ("Upgrade 1.3.0: add `x.json`",)


def test_a_changed_template_owes_an_upgrade(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    upgrade(repo, adopt=True)
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    (finding,) = doctor.check(repo, installed="1.3.0")
    assert (finding.level, finding.fix) == (doctor.BLOCK, doctor.UPGRADE)
    assert finding.details == ("template pr_template.md -> .github/pull_request_template.md",)


def test_a_template_new_to_the_repository_owes_an_upgrade(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    upgrade(repo, adopt=True)
    (guides.METHOD / "issue_template_bug.md").write_text("## Goal\n", encoding="utf-8")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert finding.details == ("template issue_template_bug.md -> .github/ISSUE_TEMPLATE/bug.md",)


def test_a_template_the_kit_dropped_asks_nothing(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    upgrade(repo, adopt=True)
    (guides.METHOD / "pr_template.md").unlink()
    assert doctor.check(repo, installed="1.3.0") == []


def test_a_copy_from_before_the_move_owes_an_upgrade(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    copy_era(repo, kit="1.2.0")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert (finding.level, finding.fix) == (doctor.BLOCK, doctor.UPGRADE)
    assert "still holds a copy of the method in docs/guides" in finding.message
    assert finding.message.endswith("a task whose edits are in the tree lands before the upgrade")


def test_an_installed_kit_older_than_the_repo_blocks(repo):
    upgrade(repo, adopt=True)
    message = doctor.check(repo, installed="1.1.9")[0].message
    assert "update the kit before the next task" in message


def test_a_repo_not_on_the_kit_blocks(repo):
    assert levels(doctor.check(repo, installed="1.2.0")) == [doctor.BLOCK]


def test_a_first_move_is_sent_to_the_upgrade_skill(repo):
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert finding.fix == doctor.ADOPT
    assert (
        doctor.UPGRADE_SKILL in finding.message and "`lifecycle upgrade --adopt`" in finding.message
    )
    assert finding.message.startswith("not on the kit yet: before the next task, ")
    assert "compares each guide named like one of the kit's with the kit's, then runs" in (
        finding.message
    )


def test_a_gist_mirror_is_a_copy_with_no_record(repo):
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert "not on the kit yet" in finding.message and finding.fix == doctor.ADOPT


def test_a_finding_names_its_fix_and_what_changed(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## v1.3.0\n\n- skills upgrade inside the task\n\n"
        "## v1.2.1\n\n- a guide wording fix\n\n## v1.2.0\n\n- already here\n",
        encoding="utf-8",
    )
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (finding,) = doctor.check(repo, installed="1.3.0")
    assert (finding.level, finding.fix) == (doctor.BLOCK, doctor.UPGRADE)
    assert finding.details == (
        "Upgrade 1.3.0: add `x.json`",
        "skills upgrade inside the task",
        "a guide wording fix",
    )


def test_a_long_list_of_changes_is_cut(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    lines = "".join(f"- change {n}\n" for n in range(12))
    (tmp_path / "CHANGELOG.md").write_text(f"## v1.3.0\n\n{lines}", encoding="utf-8")
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    details = doctor.check(repo, installed="1.3.0")[0].details
    assert len(details) == doctor.CHANGES_SHOWN + 1 and "5 more" in details[-1]


def test_an_installed_kit_older_than_the_pin_needs_updating(repo):
    upgrade(repo, adopt=True)
    assert doctor.check(repo, installed="1.1.0")[0].fix == doctor.UPDATE_KIT


def test_both_heading_shapes_are_read_and_another_lends_its_entries_to_none(monkeypatch, tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.5.0 — dated\n\n- dropped\n\n## [1.4.0] — 2026-11-21\n\n### Changed\n- dated\n\n"
        "## v1.3.0\n\n- an older kit's push\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    assert doctor.changes_since("1.2.0", "1.5.0") == ["Changed: dated", "an older kit's push"]


def test_every_release_heading_in_the_kit_changelog_and_upgrading_is_read():
    """Every heading but the section a task's entries wait in, which no repository reads."""
    for name in ("CHANGELOG.md", "UPGRADING.md"):
        lines = (doctor.KIT_ROOT / name).read_text(encoding="utf-8").splitlines()
        headings = [line for line in lines if line.startswith("## ")]
        released = [line for line in headings if line != changelog.UNRELEASED]
        assert released and all(changelog.release_of(line) for line in released)


def test_an_unreleased_section_reaches_no_repository(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text(
        f"{changelog.UNRELEASED}\n\n### Added\n- Repositories: waits\n- not yet\n\n"
        "## [1.3.0] — 2026-11-22\n\n### Added\n- Repositories: shipped\n- shipped\n",
        encoding="utf-8",
    )
    (tmp_path / "UPGRADING.md").write_text(
        f"{changelog.UNRELEASED}\n\n- waits in `x.toml`\n\n"
        "## [1.3.0] — 2026-11-22\n\n- shipped in `y.toml`\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (finding,) = doctor.check(repo, installed="9.0.0")
    assert finding.details == ("Upgrade 1.3.0: shipped in `y.toml`", "Added: shipped")


def test_a_missing_upgrading_or_a_stray_heading_in_it_lists_no_steps(monkeypatch, tmp_path):
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    assert doctor.steps_since("0.0.0", "1.4.0") == []
    (tmp_path / "UPGRADING.md").write_text(
        "## [1.4.0] dated wrong\n\n- dropped in `a.toml`\n\n## [1.3.0] — 2026-11-21\n\n"
        "- taken in `b.toml`\n",
        encoding="utf-8",
    )
    assert doctor.steps_since("0.0.0", "1.4.0") == ["Upgrade 1.3.0: taken in `b.toml`"]


def test_a_kit_issue_reads_as_the_kits_outside_it(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text(
        "## [1.3.0] — 2026-11-21\n\n### Fixed\n- a fix (#9)\n", encoding="utf-8"
    )
    (tmp_path / "UPGRADING.md").write_text(
        "## [1.3.0] — 2026-11-21\n\n- add `x.json`, as #9 says\n", encoding="utf-8"
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (finding,) = doctor.check(repo, installed="1.3.0")
    kit = kit_repository()
    assert finding.details == (
        f"Upgrade 1.3.0: add `x.json`, as {kit}#9 says",
        f"Fixed: a fix ({kit}#9)",
    )


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def test_the_steps_are_shown_past_the_cut_in_place_of_their_claims(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    lines = "".join(f"- change {n}\n" for n in range(12)) + "- Repositories: a hook\n"
    (tmp_path / "CHANGELOG.md").write_text(f"## v1.3.0\n\n{lines}", encoding="utf-8")
    (tmp_path / "UPGRADING.md").write_text(
        "## v1.3.0\n\n- add a hook in `.githooks/pre-push`\n", encoding="utf-8"
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    details = doctor.check(repo, installed="1.3.0")[0].details
    assert details[0] == "Upgrade 1.3.0: add a hook in `.githooks/pre-push`"
    assert len(details) == doctor.CHANGES_SHOWN + 1 and "Repositories: a hook" not in details


def test_a_finding_lists_the_steps_oldest_release_first(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "UPGRADING.md").write_text(
        "## [1.4.0] — 2026-11-22\n\n- then `b.toml`\n- and `c.toml`\n\n"
        "## [1.3.0] — 2026-11-21\n\n- first `a.toml`\n\n"
        "## [1.2.0] — 2026-11-20\n\n- had `z.toml`\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    assert doctor.check(repo, installed="1.4.0")[0].details == (
        "Upgrade 1.3.0: first `a.toml`",
        "Upgrade 1.4.0: then `b.toml`",
        "Upgrade 1.4.0: and `c.toml`",
    )


def test_the_kits_own_repository_asks_for_no_lock(kit_checkout):
    assert doctor.check(kit_checkout, installed="9.9.9") == []


def test_a_method_folder_without_the_kits_manifest_is_any_repository(kit_checkout):
    manifest = kit_checkout.root / ".claude-plugin" / "plugin.json"
    for body in ('{"name": "another-plugin"}', "{not json", "[]"):
        manifest.write_text(body, encoding="utf-8")
        assert [f.fix for f in doctor.check(kit_checkout, installed="9.9.9")] == [doctor.ADOPT]
    manifest.unlink()
    assert [f.fix for f in doctor.check(kit_checkout, installed="9.9.9")] == [doctor.ADOPT]


OWED = (
    "## v1.3.0\n\n- a later line in `later.toml`\n\n"
    "## v1.2.0\n\n- add `b.json`\n\n"
    "## v1.1.0\n\n- add `a.cfg`\n"
)


def test_a_repo_not_on_the_kit_is_shown_every_step_it_will_owe(repo, monkeypatch, tmp_path):
    (tmp_path / "UPGRADING.md").write_text(OWED, encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    owed = ("Upgrade 1.1.0: add `a.cfg`", "Upgrade 1.2.0: add `b.json`")
    (finding,) = doctor.check(repo, installed="1.2.0")
    assert (finding.fix, finding.details) == (doctor.ADOPT, owed)


def kit_clone(config, monkeypatch, integration="main"):
    """``config``'s kit checkout as a clone: one commit, on ``integration``, which is also
    the release ``origin/HEAD`` serves; the config reloaded with that integration branch."""
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    root = config.root
    (root / ".lifecycle.toml").write_text(
        f'[branches]\nintegration = "{integration}"\n', encoding="utf-8"
    )
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "release 9.9.9")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(root, "update-ref", f"refs/remotes/origin/{integration}", "HEAD")
    git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return load(root)


def land(config, branch, message="a task"):
    """One more commit on ``origin/<branch>``, made off the side so HEAD stays put."""
    root = config.root
    tree = subprocess.run(
        ["git", "-C", str(root), "write-tree"], check=True, capture_output=True, text=True
    ).stdout.strip()
    parent = f"refs/remotes/origin/{branch}"
    commit = subprocess.run(
        ["git", "-C", str(root), "commit-tree", tree, "-p", parent, "-m", message],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    git(root, "update-ref", parent, commit)


def test_the_kit_notes_an_installed_kit_older_than_the_served_release(kit_checkout, monkeypatch):
    kit = kit_clone(kit_checkout, monkeypatch)
    (finding,) = doctor.check(kit, installed="9.9.8")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.UPDATE_KIT)
    assert "latest release is 9.9.9" in finding.message and "9.9.8" in finding.message
    assert "the rounds run on 9.9.8's skills until it is updated" in finding.message
    assert doctor.check(kit, installed="9.9.9") == []


def test_an_unshipped_bump_or_a_local_tag_is_not_the_served_release(kit_checkout, monkeypatch):
    kit = kit_clone(kit_checkout, monkeypatch, integration="next")
    manifest = kit.root / ".claude-plugin" / "plugin.json"
    manifest.write_text('{"name": "lifecycle", "version": "10.0.0"}\n', encoding="utf-8")
    git(kit.root, "commit", "-q", "-am", "chore(release): v10.0.0")
    git(kit.root, "update-ref", "refs/remotes/origin/next", "HEAD")
    git(kit.root, "tag", "v10.0.0")
    assert doctor.check(kit, installed="9.9.9") == []


def test_the_kit_notes_nothing_with_no_origin_head(kit_checkout, monkeypatch):
    kit = kit_clone(kit_checkout, monkeypatch)
    git(kit.root, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    assert doctor.check(kit, installed="9.9.8") == []


def test_the_kit_notes_a_fresh_branch_behind_its_integration_branch(kit_checkout, monkeypatch):
    kit = kit_clone(kit_checkout, monkeypatch, integration="next")
    assert doctor.check(kit, installed="9.9.9") == []
    land(kit, "next")
    land(kit, "next")
    (finding,) = doctor.check(kit, installed="9.9.9")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.REBASE)
    assert "2 commit(s) behind origin/next" in finding.message
    assert "`git rebase origin/next`" in finding.message and "AGENTS.md again" in finding.message


def test_a_branch_with_a_commit_of_its_own_is_not_noted(kit_checkout, monkeypatch):
    kit = kit_clone(kit_checkout, monkeypatch, integration="next")
    land(kit, "next")
    (kit.root / "work.txt").write_text("a task under way\n", encoding="utf-8")
    git(kit.root, "add", "work.txt")
    git(kit.root, "commit", "-q", "-m", "wip")
    assert doctor.check(kit, installed="9.9.9") == []


def test_a_tree_holding_a_tasks_edits_is_not_noted(kit_checkout, monkeypatch):
    """A task's edits stay uncommitted until Complete, and git refuses a rebase over them:
    the task started on the integration branch, and its push rebases."""
    kit = kit_clone(kit_checkout, monkeypatch, integration="next")
    land(kit, "next")
    (kit.root / "method" / "task_review.md").write_text("# edited\n", encoding="utf-8")
    assert doctor.check(kit, installed="9.9.9") == []
    git(kit.root, "checkout", "--", "method/task_review.md")
    (kit.root / "new.md").write_text("a new file\n", encoding="utf-8")
    assert doctor.check(kit, installed="9.9.9") == []


def test_a_hotfix_branch_is_not_sent_to_the_integration_branch(kit_checkout, monkeypatch):
    """A hotfix is cut from the last release to ship without what has landed since."""
    kit = kit_clone(kit_checkout, monkeypatch, integration="next")
    land(kit, "next")
    git(kit.root, "switch", "-q", "-c", "hotfix/urgent")
    assert doctor.check(kit, installed="9.9.9") == []


def test_each_change_line_opens_with_its_group(repo, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (tmp_path / "CHANGELOG.md").write_text(
        "## [1.3.0] — 2026-11-22\n\n### Added\n- a skill\n\n### Changed\n- a brief\n\n"
        "### Fixed\n- a guard\n\n### Removed\n- `lifecycle gone`\n",
        encoding="utf-8",
    )
    (tmp_path / "UPGRADING.md").write_text("## v1.3.0\n\n- add `x.json`\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    (finding,) = doctor.check(repo, installed="1.3.0")
    assert finding.details[1:] == (
        "Added: a skill",
        "Changed: a brief",
        "Fixed: a guard",
        "Removed: `lifecycle gone`",
    )


def test_a_repositories_entry_under_a_group_is_left_out(monkeypatch, tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(
        "## [1.3.0] — 2026-11-22\n\n### Changed\n- Repositories: a hook\n- a brief\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor, "KIT_ROOT", tmp_path)
    assert doctor.changes_since("1.2.0", "1.3.0") == ["Changed: a brief"]


KIT_FILES = {
    "method/task_review.md": "# Task review, canonical\n",
    ".claude-plugin/plugin.json": '{"name": "lifecycle", "version": "9.9.9"}\n',
}


def tidy_notes(root):
    return [f for f in doctor.check(load(root), installed="9.9.9") if f.fix == doctor.TIDY]


@pytest.mark.parametrize("files", [KIT_FILES, None], ids=["kit", "repository"])
def test_a_primary_checkout_behind_origin_is_noted_from_a_linked_worktree(clone_of, files):
    """A push from a worktree moves the remote-tracking branch every checkout shares,
    and leaves the primary checkout's own branch behind it."""
    clone = clone_of(files)
    tree = clone.task("task-1")
    assert tidy_notes(tree) == []
    clone.land(tree)
    (finding,) = tidy_notes(tree)
    assert finding.level == doctor.NOTE
    assert finding.message.startswith(
        f"the primary checkout ({clone.primary.as_posix()}) has next 1 commit(s) behind "
        "origin/next: `lifecycle tidy` fast-forwards it;"
    )
    assert "a session there reads its older AGENTS.md" in finding.message


def test_a_repositorys_primary_checkout_notes_itself(clone_of):
    clone = clone_of()
    clone.land(clone.task("task-1"))
    (finding,) = tidy_notes(clone.primary)
    assert "1 commit(s) behind origin/next" in finding.message


def test_the_kits_primary_checkout_gets_one_note_beside_its_rebase_note(clone_of):
    clone = clone_of(KIT_FILES)
    clone.land(clone.task("task-1"))
    fixes = [f.fix for f in doctor.check(load(clone.primary), installed="9.9.9")]
    assert fixes == [doctor.REBASE]


@pytest.mark.parametrize("state", ["level", "diverged", "no-origin"])
def test_a_primary_checkout_that_cannot_fast_forward_is_not_noted(clone_of, state):
    clone = clone_of()
    tree = clone.task("task-1")
    if state != "level":
        clone.land(tree)
    if state == "diverged":
        commit(clone.primary, "own")
    if state == "no-origin":
        git(clone.primary, "update-ref", "-d", "refs/remotes/origin/next")
    assert tidy_notes(tree) == [] and tidy_notes(clone.primary) == []
