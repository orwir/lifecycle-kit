import subprocess

from conftest import copy_era
from lifecycle import changelog, doctor, guides, kit_repository
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
    assert doctor.changes_since("1.2.0", "1.5.0") == ["dated", "an older kit's push"]


def test_every_release_heading_in_the_kit_changelog_and_upgrading_is_read():
    for name in ("CHANGELOG.md", "UPGRADING.md"):
        lines = (doctor.KIT_ROOT / name).read_text(encoding="utf-8").splitlines()
        headings = [line for line in lines if line.startswith("## ")]
        assert headings and all(changelog.release_of(line) for line in headings)


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
        f"a fix ({kit}#9)",
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


def test_the_kit_notes_an_installed_kit_older_than_its_release(kit_checkout, monkeypatch):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    git(kit_checkout.root, "init", "-q", "-b", "main")
    git(kit_checkout.root, "add", "-A")
    git(kit_checkout.root, "commit", "-q", "-m", "v9.9.9")
    (finding,) = doctor.check(kit_checkout, installed="9.9.8")
    assert (finding.level, finding.fix) == (doctor.NOTE, doctor.UPDATE_KIT)
    assert "main is at 9.9.9" in finding.message and "9.9.8" in finding.message
    assert "the rounds run on 9.9.8's skills until it is updated" in finding.message
    assert "before the next round" not in finding.message
    assert doctor.check(kit_checkout, installed="9.9.9") == []
    manifest = kit_checkout.root / ".claude-plugin" / "plugin.json"
    manifest.write_text('{"name": "lifecycle", "version": "10.0.0"}\n', encoding="utf-8")
    assert doctor.check(kit_checkout, installed="9.9.9") == []
