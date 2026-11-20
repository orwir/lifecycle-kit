from lifecycle import doctor
from lifecycle.guides import upgrade


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


def test_a_gist_mirror_is_named(repo):
    (repo.guides_dir / ".gist-revision").write_text("abc\n", encoding="utf-8")
    assert "gist" in doctor.check(repo, installed="1.2.0")[0].message
