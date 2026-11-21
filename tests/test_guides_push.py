import json
import subprocess

import pytest
from lifecycle import cli, guides
from lifecycle.guides import GuidesError, local_edits, push, read_lock, upgrade

WHY = "A review asked for it."


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout


def release_in(work, version, message):
    manifest = work / ".claude-plugin" / "plugin.json"
    manifest.write_text(json.dumps({"name": "lifecycle", "version": version}), encoding="utf-8")
    git(work, "commit", "-q", "-am", message)
    git(work, "tag", f"v{version}")


@pytest.fixture
def kit(tmp_path, monkeypatch):
    """A kit remote: v1.2.0 is the fixture's method, v1.2.1 another project's guide edit."""
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    (guides.METHOD / "guide.md").write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
    work = tmp_path / "kit-work"
    (work / "method").mkdir(parents=True)
    (work / ".claude-plugin").mkdir()
    for path in guides.METHOD.iterdir():
        (work / "method" / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (work / "CHANGELOG.md").write_text(
        "# Changelog\n\n---\n\n## [1.2.0] — 2026-11-20\n\n### Added\n- first\n", encoding="utf-8"
    )
    (work / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    git(work, "init", "-q", "-b", "main")
    git(work, "add", "-A")
    release_in(work, "1.2.0", "v1.2.0")
    (work / "method" / "agents_template.md").write_text("# AGENTS, later\n", encoding="utf-8")
    (work / "method" / "guide.md").write_text("A\nb\nc\nd\ne\n", encoding="utf-8")
    release_in(work, "1.2.1", "another project's edits")
    bare = tmp_path / "kit.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True)
    monkeypatch.setenv("LIFECYCLE_KIT_REMOTE", str(bare))
    return bare


def clone(kit, where):
    subprocess.run(["git", "clone", "-q", str(kit), str(where)], check=True)
    return where


def read(path):
    return path.read_text(encoding="utf-8")


def test_an_edit_lands_on_main_as_a_patch_release(repo, kit, tmp_path, monkeypatch):
    monkeypatch.setattr(guides, "_today", lambda: "2026-11-22")
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    assert push(repo, "task_review: say it better", WHY) == (["task_review.md"], "1.2.2")
    check = clone(kit, tmp_path / "check")
    assert read(check / "method" / "task_review.md") == "# Task review, better\n"
    assert read(check / "method" / "agents_template.md") == "# AGENTS, later\n"
    assert json.loads(read(check / ".claude-plugin" / "plugin.json"))["version"] == "1.2.2"
    assert "v1.2.2" in git(check, "tag")
    assert read(check / "CHANGELOG.md") == (
        "# Changelog\n\n---\n\n## [1.2.2] — 2026-11-22\n\n"
        "### Changed\n- task_review: say it better\n\n"
        "## [1.2.0] — 2026-11-20\n\n### Added\n- first\n"
    )
    lock = read_lock(repo.root)
    assert (lock.kit, lock.pushed, local_edits(repo, lock)) == (
        "1.2.0",
        {"task_review.md": "1.2.2"},
        [],
    )


def test_a_second_push_builds_on_the_first(repo, kit, tmp_path):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    push(repo, "first", WHY)
    (repo.guides_dir / "task_review.md").write_text("# Task review, best\n", encoding="utf-8")
    assert push(repo, "second", WHY) == (["task_review.md"], "1.2.3")
    assert read(clone(kit, tmp_path / "check") / "method" / "task_review.md") == (
        "# Task review, best\n"
    )


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        ("task_review: " + "x" * 120, "133 characters, over the cap of 120"),
        ("task_review: say it better; and shorter", "welded"),
        ("task_review: say it better (#12)", r"an issue reference \(#12\)"),
        ("task_review: say it better (orwir/murmur#12)", r"reference \(orwir/murmur#12\)"),
        ("", "no line"),
        ("   ", "no line"),
    ],
)
def test_a_line_that_breaks_the_changelogs_style_is_refused_before_cloning(
    repo, kit, monkeypatch, line, reason
):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    cloned = []
    monkeypatch.setattr(guides, "_git", lambda *args: cloned.append(args))
    with pytest.raises(GuidesError, match=reason):
        push(repo, line, WHY)
    assert cloned == [] and local_edits(repo, read_lock(repo.root)) == ["task_review.md"]


@pytest.mark.parametrize(
    ("why", "reason"),
    [
        ("", "no reason"),
        ("  \n\n ", "no reason"),
        ("A review missed it, see #12.", r"names an issue \(#12\)"),
        ("Closes orwir/murmur#12.", r"names an issue \(orwir/murmur#12\)"),
        ("Closes GH-12.", r"names an issue \(GH-12\)"),
        ("See skills/complete/SKILL.md#2-guides.", r"names an issue \(complete/SKILL\.md#2\)"),
        (
            "Closes https://github.com/orwir/murmur/issues/12.",
            r"\(github\.com/orwir/murmur/issues/12\)",
        ),
    ],
)
def test_a_missing_reason_or_one_naming_an_issue_is_refused_before_cloning(
    repo, kit, monkeypatch, why, reason
):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    cloned = []
    monkeypatch.setattr(guides, "_git", lambda *args: cloned.append(args))
    with pytest.raises(GuidesError, match=reason):
        push(repo, "task_review: say it better", why)
    assert cloned == [] and local_edits(repo, read_lock(repo.root)) == ["task_review.md"]


def test_the_reason_reaches_the_kit_commit_word_for_word(repo, kit, tmp_path, monkeypatch, capsys):
    # The machine strips comment lines from messages, which the push must not inherit.
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "commit.cleanup")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "strip")
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    reason = (
        "A reviewer read `task_review.md#2-guides` and missed the $HOME case, colour #1f2937.\n"
        "# the line above stays\n\n"
        "A second paragraph, `quoted`."
    )
    message = tmp_path / "message.txt"
    body = f"task_review: say it better\n\n{reason}\n".replace("\n", "\r\n")
    message.write_text(body, encoding="utf-8", newline="")
    monkeypatch.chdir(repo.root)
    assert cli.main(["guides", "push", "-F", str(message)]) == 0
    assert "as kit v1.2.2" in capsys.readouterr().out
    check = clone(kit, tmp_path / "check")
    assert git(check, "log", "-1", "--format=%B").rstrip("\n") == (
        f"task_review: say it better\n\n{reason}\n\nReleased as v1.2.2."
    )
    assert "### Changed\n- task_review: say it better\n\n## [1.2.0]" in read(check / "CHANGELOG.md")


@pytest.mark.parametrize("body", ["\n\nA reason.\n", " \n\nA reason.\n"])
def test_a_message_file_with_no_line_is_refused_before_cloning(
    repo, kit, tmp_path, monkeypatch, capsys, body
):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    message = tmp_path / "message.txt"
    message.write_text(body, encoding="utf-8")
    cloned = []
    monkeypatch.setattr(guides, "_git", lambda *args: cloned.append(args))
    monkeypatch.chdir(repo.root)
    assert cli.main(["guides", "push", "-F", str(message)]) == 1
    assert "no line" in capsys.readouterr().err
    assert cloned == [] and local_edits(repo, read_lock(repo.root)) == ["task_review.md"]


def test_a_conflict_stops_the_push(repo, kit):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "agents_template.md").write_text("# AGENTS, mine\n", encoding="utf-8")
    with pytest.raises(GuidesError, match="conflict"):
        push(repo, "agents_template: mine", WHY)
    assert local_edits(repo, read_lock(repo.root)) == ["agents_template.md"]


def test_unreleased_work_on_main_stops_the_push(repo, kit, tmp_path):
    work = clone(kit, tmp_path / "work")
    (work / "NOTES.md").write_text("skill work in progress\n", encoding="utf-8")
    git(work, "add", "NOTES.md")
    git(work, "commit", "-q", "-m", "wip")
    git(work, "push", "-q", "origin", "HEAD:main")
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    with pytest.raises(GuidesError, match="no release carries"):
        push(repo, "x", WHY)


def test_an_upgrade_waits_for_the_release_that_took_the_push(repo, kit, monkeypatch):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    push(repo, "task_review: say it better", WHY)
    monkeypatch.setattr(guides, "kit_version", lambda: "1.2.1")
    with pytest.raises(GuidesError, match="update the installed kit"):
        upgrade(repo)
    (guides.METHOD / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: "1.2.2")
    upgrade(repo)
    lock = read_lock(repo.root)
    assert (lock.kit, lock.pushed) == ("1.2.2", {})
    assert read(repo.guides_dir / "task_review.md") == "# Task review, better\n"


def test_a_deleted_guide_is_not_pushed(repo, kit):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").unlink()
    with pytest.raises(GuidesError, match="Restore"):
        push(repo, "drop it", WHY)


def test_nothing_to_push(repo, kit):
    upgrade(repo, adopt=True)
    assert push(repo, "x", WHY) == ([], "1.2.0")


def test_an_edit_merges_with_another_projects_change_to_the_same_guide(repo, kit, tmp_path):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "guide.md").write_text("a\nb\nc\nd\nE\n", encoding="utf-8")
    assert push(repo, "guide: end better", WHY) == (["guide.md"], "1.2.2")
    assert read(clone(kit, tmp_path / "check") / "method" / "guide.md") == "A\nb\nc\nd\nE\n"
    assert read(repo.guides_dir / "guide.md") == "A\nb\nc\nd\nE\n"
    assert local_edits(repo, read_lock(repo.root)) == []


def test_a_later_push_never_reverts_what_the_first_one_carried(repo, kit, tmp_path):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    push(repo, "first", WHY)
    (repo.guides_dir / "agents_template.md").write_text("# AGENTS, mine\n", encoding="utf-8")
    with pytest.raises(GuidesError, match="conflict"):
        push(repo, "second", WHY)
    assert read(clone(kit, tmp_path / "check") / "method" / "agents_template.md") == (
        "# AGENTS, later\n"
    )


def test_a_gist_mirror_past_the_import_is_refused(tmp_path, monkeypatch):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    gist = tmp_path / "gist"
    gist.mkdir()
    git(gist, "init", "-q", "-b", "main")
    git(gist, "commit", "-q", "--allow-empty", "-m", "imported")
    imported = git(gist, "rev-parse", "HEAD").strip()
    git(gist, "commit", "-q", "--allow-empty", "-m", "pushed after the import")
    later = git(gist, "rev-parse", "HEAD").strip()
    monkeypatch.setattr(guides, "GIST_IMPORTED", imported)
    guides.check_imported(str(gist), imported)
    with pytest.raises(GuidesError, match="does not contain"):
        guides.check_imported(str(gist), later)


def installed_kit(monkeypatch, version, **files):
    for name, body in files.items():
        (guides.METHOD / name).write_text(body, encoding="utf-8")
    monkeypatch.setattr(guides, "kit_version", lambda: version)


def test_an_upgrade_carries_an_unpushed_edit_onto_the_new_release(repo, kit, monkeypatch):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "guide.md").write_text("a\nb\nc\nd\nE\n", encoding="utf-8")
    installed_kit(monkeypatch, "1.3.0", **{"guide.md": "A\nb\nc\nd\ne\n"})
    assert upgrade(repo) == ["guide.md"]
    assert read(repo.guides_dir / "guide.md") == "A\nb\nc\nd\nE\n"
    lock = read_lock(repo.root)
    assert (lock.kit, local_edits(repo, lock)) == ("1.3.0", ["guide.md"])


def test_a_carried_edit_pushes_from_the_new_release(repo, kit, monkeypatch, tmp_path):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").write_text("# Task review, better\n", encoding="utf-8")
    installed_kit(monkeypatch, "1.2.1")
    upgrade(repo)
    assert push(repo, "task_review: say it better", WHY) == (["task_review.md"], "1.2.2")
    assert read(clone(kit, tmp_path / "check") / "method" / "task_review.md") == (
        "# Task review, better\n"
    )


def test_a_carried_edit_that_conflicts_stops_the_upgrade(repo, kit, monkeypatch):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "agents_template.md").write_text("# AGENTS, mine\n", encoding="utf-8")
    installed_kit(monkeypatch, "1.3.0", **{"agents_template.md": "# AGENTS, later\n"})
    with pytest.raises(GuidesError, match="conflict"):
        upgrade(repo)
    assert read_lock(repo.root).kit == "1.2.0"
    assert read(repo.guides_dir / "agents_template.md") == "# AGENTS, mine\n"


def test_a_deleted_guide_stops_the_upgrade(repo, kit, monkeypatch):
    upgrade(repo, adopt=True)
    (repo.guides_dir / "task_review.md").unlink()
    installed_kit(monkeypatch, "1.3.0")
    with pytest.raises(GuidesError, match="Restore"):
        upgrade(repo)


def test_a_template_edit_the_task_carries_is_not_overwritten(repo, kit, monkeypatch):
    upgrade(repo, adopt=True)
    installed = repo.root / ".github" / "pull_request_template.md"
    installed.parent.mkdir(parents=True)
    for path in (installed, repo.guides_dir / "pr_template.md"):
        path.write_text("A\nb\nc\nd\n", encoding="utf-8")
    installed_kit(monkeypatch, "1.3.0", **{"pr_template.md": "a\nb\nc\nD\n"})
    changes = upgrade(repo)
    assert changes.installed == []
    assert read(installed) == "A\nb\nc\nd\n"
    assert read(repo.guides_dir / "pr_template.md") == "A\nb\nc\nD\n"


def test_the_kits_own_repository_pushes_nothing(kit_checkout):
    with pytest.raises(GuidesError, match="canonical"):
        push(kit_checkout, "a guide edit", WHY)
