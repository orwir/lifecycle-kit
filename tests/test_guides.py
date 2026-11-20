import pytest
from conftest import name_templates
from lifecycle import guides
from lifecycle.guides import GuidesError, read_lock, upgrade


def test_a_repo_with_no_record_needs_adopt(repo):
    with pytest.raises(GuidesError, match="--adopt"):
        upgrade(repo)


def test_adopt_copies_the_method_and_pins_it(repo):
    (repo.guides_dir / "design_language.md").write_text("own\n", encoding="utf-8")
    changed = upgrade(repo, adopt=True)
    assert changed == ["agents_template.md", "pr_template.md", "task_review.md"]
    lock = read_lock(repo.root)
    assert lock.kit == "1.2.0" and set(lock.guides) == {
        "agents_template.md",
        "pr_template.md",
        "task_review.md",
    }
    assert (repo.guides_dir / "design_language.md").read_text(encoding="utf-8") == "own\n"


def test_a_crlf_checkout_is_not_an_edit(repo):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_bytes(b"# Task review\r\n")
    assert guides.local_edits(repo, read_lock(repo.root)) == []


def test_a_file_the_kit_dropped_leaves_the_copy(repo, monkeypatch):
    upgrade(repo, adopt=True)
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    (guides.METHOD / "agents_template.md").unlink()
    assert upgrade(repo) == ["agents_template.md"]
    assert not (repo.guides_dir / "agents_template.md").exists()


def test_dry_run_writes_nothing(repo):
    assert upgrade(repo, adopt=True, dry_run=True) == [
        "agents_template.md",
        "pr_template.md",
        "task_review.md",
    ]
    assert read_lock(repo.root) is None
    assert not (repo.guides_dir / "task_review.md").exists()


def test_a_gist_mirror_with_edits_is_refused(repo, monkeypatch):
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    monkeypatch.setattr(guides, "_gist_mirror_edits", lambda config, rev: ["README.md"])
    with pytest.raises(GuidesError, match="gist mirror"):
        upgrade(repo)


def test_a_clean_gist_mirror_moves_to_the_kit(repo, monkeypatch):
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    monkeypatch.setattr(guides, "_gist_mirror_edits", lambda config, rev: [])
    upgrade(repo)
    assert not (repo.guides_dir / ".gist-revision").exists()
    assert read_lock(repo.root).kit == "1.2.0"


def test_the_same_release_again_is_a_no_op(repo):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Edited\n", encoding="utf-8")
    assert upgrade(repo) == []
    assert (repo.guides_dir / "task_review.md").read_text(encoding="utf-8") == "# Edited\n"


def test_a_new_kit_file_never_overwrites_a_guide_of_the_repository(repo, monkeypatch):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "design_language.md").write_text("ours\n", encoding="utf-8")
    (guides.METHOD / "design_language.md").write_text("the kit's\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    with pytest.raises(GuidesError, match=r"design_language.md"):
        upgrade(repo)
    assert (repo.guides_dir / "design_language.md").read_text(encoding="utf-8") == "ours\n"


def test_a_template_installed_word_for_word_takes_the_new_text(repo, monkeypatch):
    (guides.METHOD / "pr_template.md").write_text("## Summary\n", encoding="utf-8")
    upgrade(repo, adopt=True)
    installed = repo.root / ".github" / "pull_request_template.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("## Summary\n", encoding="utf-8")
    (guides.METHOD / "pr_template.md").write_text(
        "## Summary\n\n## Verification\n", encoding="utf-8"
    )
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    changes = upgrade(repo)
    assert changes.installed == [".github/pull_request_template.md"]
    assert installed.read_text(encoding="utf-8") == "## Summary\n\n## Verification\n"


def test_an_adapted_template_is_left_for_the_port(repo, monkeypatch):
    (guides.METHOD / "pr_template.md").write_text("## Summary\n", encoding="utf-8")
    upgrade(repo, adopt=True)
    installed = repo.root / ".github" / "pull_request_template.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("## Summary\n\nOurs.\n", encoding="utf-8")
    (guides.METHOD / "pr_template.md").write_text(
        "## Summary\n\n## Verification\n", encoding="utf-8"
    )
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    assert upgrade(repo).installed == []
    assert installed.read_text(encoding="utf-8") == "## Summary\n\nOurs.\n"


def test_a_dry_run_leaves_installed_templates_alone(repo, monkeypatch):
    upgrade(repo, adopt=True)
    installed = repo.root / ".github" / "pull_request_template.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("a\nb\nc\nd\n", encoding="utf-8")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    assert upgrade(repo, dry_run=True).installed == [".github/pull_request_template.md"]
    assert installed.read_text(encoding="utf-8") == "a\nb\nc\nd\n"


def test_a_named_template_is_replaced_where_its_mapping_puts_it(repo, monkeypatch):
    upgrade(repo, adopt=True)
    repo = name_templates(repo, '"pr_template.md" = "docs/pr.md"\n')
    mapped = repo.root / "docs" / "pr.md"
    unmapped = repo.root / ".github" / "pull_request_template.md"
    for path in (mapped, unmapped):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("a\nb\nc\nd\n", encoding="utf-8")
    (guides.METHOD / "pr_template.md").write_text("a\nb\nc\nD\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.3.0")
    assert upgrade(repo).installed == ["docs/pr.md"]
    assert mapped.read_text(encoding="utf-8") == "a\nb\nc\nD\n"
    assert unmapped.read_text(encoding="utf-8") == "a\nb\nc\nd\n"


def test_a_named_template_the_method_lacks_stops_the_upgrade(repo):
    repo = name_templates(repo, '"idea_gauntlt.md" = "AGENTS.md"\n')
    with pytest.raises(GuidesError, match=r"idea_gauntlt.md"):
        upgrade(repo, adopt=True)
    assert read_lock(repo.root) is None and not any(repo.guides_dir.iterdir())


def test_the_kits_own_repository_is_never_upgraded(kit_checkout):
    for adopt in (False, True):
        with pytest.raises(GuidesError, match="canonical"):
            upgrade(kit_checkout, adopt=adopt)
    assert read_lock(kit_checkout.root) is None
    canonical = kit_checkout.root / "method" / "task_review.md"
    assert canonical.read_text(encoding="utf-8") == "# Task review, canonical\n"
