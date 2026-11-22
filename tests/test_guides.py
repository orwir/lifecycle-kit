import json

import pytest
from conftest import copy_era, name_templates
from lifecycle import guides
from lifecycle.guides import LOCK, GuidesError, read_lock, upgrade

PR = ".github/pull_request_template.md"


def pr_target(repo, body):
    path = repo.root / PR
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def kit_at(monkeypatch, version):
    monkeypatch.setattr(guides, "kit_version", lambda: version)


def test_a_repo_with_no_record_needs_adopt(repo):
    with pytest.raises(GuidesError, match="--adopt"):
        upgrade(repo)
    assert read_lock(repo.root) is None


def test_adopt_records_the_release_and_each_followed_templates_text(repo):
    changes = upgrade(repo, adopt=True)
    lock = read_lock(repo.root)
    assert (lock.kit, lock.guides) == ("1.2.0", {})
    assert lock.templates == {"agents_template.md": "# AGENTS\n", "pr_template.md": "a\nb\nc\nd\n"}
    assert [(p.name, p.target, p.diff) for p in changes.ports] == [
        ("agents_template.md", "AGENTS.md", ""),
        ("pr_template.md", PR, ""),
    ]
    assert not any(repo.guides_dir.iterdir())


def test_adopt_deletes_only_the_kits_text_and_keeps_the_rest_named_like_it(repo):
    (guides.METHOD / "README.md").write_text("# The method\n", encoding="utf-8")
    (repo.guides_dir / "README.md").write_text("Our own guides\n", encoding="utf-8")
    (repo.guides_dir / "task_review.md").write_text("an older copy\n", encoding="utf-8")
    (repo.guides_dir / "agents_template.md").write_bytes(b"# AGENTS\r\n")
    (repo.guides_dir / "design_language.md").write_text("ours\n", encoding="utf-8")
    planned = upgrade(repo, adopt=True, dry_run=True)
    assert planned.deleted == ["agents_template.md"]
    assert planned.kept == ["README.md", "task_review.md"]
    assert len(list(repo.guides_dir.iterdir())) == 4
    changes = upgrade(repo, adopt=True)
    assert (changes.deleted, changes.kept) == (planned.deleted, planned.kept)
    assert sorted(p.name for p in repo.guides_dir.iterdir()) == [
        "README.md",
        "design_language.md",
        "task_review.md",
    ]


def test_adopt_keeps_a_kit_named_guide_in_another_encoding(repo):
    (repo.guides_dir / "task_review.md").write_text("Наши гайды\n", encoding="utf-16")
    changes = upgrade(repo, adopt=True)
    assert (changes.deleted, changes.kept) == ([], ["task_review.md"])
    assert (repo.guides_dir / "task_review.md").is_file()


def test_a_gist_mirror_is_a_copy_with_no_record(repo):
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    with pytest.raises(GuidesError, match="no record of the kit release it follows"):
        upgrade(repo)
    upgrade(repo, adopt=True)
    assert read_lock(repo.root).kit == "1.2.0"


def test_the_move_from_copies_deletes_the_kits_files_and_keeps_its_own(repo):
    copy_era(repo)
    (repo.guides_dir / "design_language.md").write_text("ours\n", encoding="utf-8")
    changes = upgrade(repo)
    assert changes.deleted == ["agents_template.md", "pr_template.md", "task_review.md"]
    assert [p.name for p in repo.guides_dir.iterdir()] == ["design_language.md"]
    written = json.loads((repo.root / LOCK).read_text(encoding="utf-8"))
    assert written["kit"] == "1.2.0" and "guides" not in written
    assert set(written["templates"]) == {"agents_template.md", "pr_template.md"}


def test_an_edited_copy_stops_the_move_with_nothing_written(repo):
    copy_era(repo)
    before = (repo.root / LOCK).read_text(encoding="utf-8")
    (repo.guides_dir / "task_review.md").write_text(
        "an edit the kit never took\n", encoding="utf-8"
    )
    with pytest.raises(GuidesError, match=r"task_review\.md"):
        upgrade(repo)
    assert (repo.root / LOCK).read_text(encoding="utf-8") == before
    assert (repo.guides_dir / "agents_template.md").is_file()


def test_a_crlf_checkout_of_a_copy_is_not_an_edit(repo):
    copy_era(repo)
    copy = repo.guides_dir / "pr_template.md"
    copy.write_bytes(copy.read_bytes().replace(b"\n", b"\r\n"))
    assert "pr_template.md" in upgrade(repo).deleted


def test_the_move_takes_a_templates_old_text_from_the_copy(repo):
    copy_era(repo)
    target = pr_target(repo, "a\nb\nc\nd\n")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    assert PR in upgrade(repo).installed
    assert target.read_text(encoding="utf-8") == "a\nb\nc\nD\n"


def test_a_template_installed_word_for_word_takes_the_new_text(repo, monkeypatch):
    upgrade(repo, adopt=True)
    target = pr_target(repo, "a\nb\nc\nd\n")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    kit_at(monkeypatch, "1.3.0")
    changes = upgrade(repo)
    assert (changes.installed, changes.ports) == ([PR], [])
    assert target.read_text(encoding="utf-8") == "a\nb\nc\nD\n"
    assert read_lock(repo.root).templates["pr_template.md"] == "a\nb\nc\nD\n"


def test_an_adapted_template_gets_its_diff_from_the_locks_old_text(repo, monkeypatch):
    upgrade(repo, adopt=True)
    target = pr_target(repo, "a\nb\nc\nd\nours\n")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    kit_at(monkeypatch, "1.3.0")
    (port,) = upgrade(repo).ports
    assert (port.name, port.target) == ("pr_template.md", PR)
    assert "-d\n" in port.diff and "+D\n" in port.diff
    assert "(kit 1.2.0)" in port.diff and "(kit 1.3.0)" in port.diff
    assert target.read_text(encoding="utf-8") == "a\nb\nc\nd\nours\n"


def test_a_template_new_to_the_repository_is_read_whole(repo, monkeypatch):
    upgrade(repo, adopt=True)
    (guides.METHOD / "issue_template_bug.md").write_text("## Goal\n", encoding="utf-8")
    kit_at(monkeypatch, "1.3.0")
    (port,) = upgrade(repo).ports
    assert (port.name, port.target, port.diff) == (
        "issue_template_bug.md",
        ".github/ISSUE_TEMPLATE/bug.md",
        "",
    )
    assert read_lock(repo.root).templates["issue_template_bug.md"] == "## Goal\n"


def test_a_template_the_kit_dropped_leaves_the_lock_and_its_target(repo, monkeypatch):
    upgrade(repo, adopt=True)
    target = pr_target(repo, "a\nb\nc\nd\n")
    (guides.METHOD / "pr_template.md").unlink()
    kit_at(monkeypatch, "1.3.0")
    changes = upgrade(repo)
    assert (changes.installed, changes.ports) == ([], [])
    assert "pr_template.md" not in read_lock(repo.root).templates
    assert target.read_text(encoding="utf-8") == "a\nb\nc\nd\n"


def test_a_changed_guide_changes_nothing_in_the_repository(repo, monkeypatch):
    upgrade(repo, adopt=True)
    (guides.METHOD / "task_review.md").write_text("# Task review, 1.3\n", encoding="utf-8")
    kit_at(monkeypatch, "1.3.0")
    changes = upgrade(repo)
    assert (changes.installed, changes.ports, changes.deleted) == ([], [], [])
    assert not any(repo.guides_dir.iterdir())


def test_a_dry_run_writes_nothing(repo, monkeypatch):
    upgrade(repo, adopt=True)
    before = (repo.root / LOCK).read_text(encoding="utf-8")
    target = pr_target(repo, "a\nb\nc\nd\n")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    kit_at(monkeypatch, "1.3.0")
    assert upgrade(repo, dry_run=True).installed == [PR]
    assert target.read_text(encoding="utf-8") == "a\nb\nc\nd\n"
    assert (repo.root / LOCK).read_text(encoding="utf-8") == before


def test_a_named_template_is_replaced_where_its_mapping_puts_it(repo, monkeypatch):
    upgrade(repo, adopt=True)
    repo = name_templates(repo, '"pr_template.md" = "docs/pr.md"\n')
    mapped = repo.root / "docs" / "pr.md"
    mapped.write_text("a\nb\nc\nd\n", encoding="utf-8")
    unmapped = pr_target(repo, "a\nb\nc\nd\n")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    kit_at(monkeypatch, "1.3.0")
    assert upgrade(repo).installed == ["docs/pr.md"]
    assert mapped.read_text(encoding="utf-8") == "a\nb\nc\nD\n"
    assert unmapped.read_text(encoding="utf-8") == "a\nb\nc\nd\n"


def test_a_named_template_the_method_lacks_stops_the_upgrade(repo):
    repo = name_templates(repo, '"idea_gauntlt.md" = "AGENTS.md"\n')
    with pytest.raises(GuidesError, match=r"idea_gauntlt.md"):
        upgrade(repo, adopt=True)
    assert read_lock(repo.root) is None


def test_an_installed_kit_older_than_the_lock_stops_the_upgrade(repo, monkeypatch):
    upgrade(repo, adopt=True)
    kit_at(monkeypatch, "1.1.0")
    with pytest.raises(GuidesError, match="update the installed kit"):
        upgrade(repo)


def test_the_kits_own_repository_is_never_upgraded(kit_checkout):
    for adopt in (False, True):
        with pytest.raises(GuidesError, match="canonical"):
            upgrade(kit_checkout, adopt=adopt)
    assert read_lock(kit_checkout.root) is None
    canonical = kit_checkout.root / "method" / "task_review.md"
    assert canonical.read_text(encoding="utf-8") == "# Task review, canonical\n"
