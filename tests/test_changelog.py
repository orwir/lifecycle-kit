"""The kit's CHANGELOG held to the style its header states, and UPGRADING.md beside it.

Every release is read, not only the newest: the kit has no ``[Unreleased]`` section, since
each task's diff is its release, and doctor shows released entries to every repository.
"""

from __future__ import annotations

import json
import re

import pytest
from lifecycle import KIT_ROOT, changelog
from lifecycle.changelog import CAP

CHANGELOG = KIT_ROOT / "CHANGELOG.md"
UPGRADING = KIT_ROOT / "UPGRADING.md"
REPOSITORIES = "- Repositories: "


def releases(path) -> dict[str, list[str]]:
    """Each heading line of ``path`` with the lines below it, up to the next."""
    found: dict[str, list[str]] = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line
            found[current] = []
        elif current is not None:
            found[current].append(line)
    return found


def test_every_release_heading_is_dated():
    old = [h for h in releases(CHANGELOG) if not re.match(r"^## \[[\d.]+\] — \d{4}-", h)]

    assert old == []


def test_every_release_is_one_claim_per_entry_within_the_cap():
    found = [
        f"{h}: {v}" for h, body in releases(CHANGELOG).items() for v in changelog.violations(body)
    ]

    assert found == []


def test_a_release_with_repositories_entries_has_its_steps_in_upgrading():
    asking = {
        h
        for h, body in releases(CHANGELOG).items()
        if any(line.startswith(REPOSITORIES) for line in body)
    }

    assert asking and asking == set(releases(UPGRADING))


def test_every_upgrade_step_names_the_file_it_changes():
    steps = [
        line for body in releases(UPGRADING).values() for line in body if line.startswith("- ")
    ]
    named = re.compile(r"`[^`\s]*[./][^`\s]*`")

    assert steps and [step for step in steps if not named.search(step)] == []


def test_every_upgrade_step_sits_on_one_line():
    """The reader takes only ``- `` lines, so a step wrapped onto a second line reaches an
    upgrade cut off."""
    wrapped = [
        line
        for body in releases(UPGRADING).values()
        for line in body
        if line and not line.startswith("- ")
    ]

    assert wrapped == []


def test_the_cap_the_push_line_is_told_is_the_cap_the_push_holds():
    for path in (KIT_ROOT / "skills" / "complete" / "SKILL.md", KIT_ROOT / "docs" / "guide.md"):
        assert f"{CAP} characters" in path.read_text(encoding="utf-8"), path


def test_an_entry_outside_every_group_is_named():
    assert changelog.violations(["", "- loose (#1)", "### Added", "- grouped (#2)"]) == [
        "in no group: loose (#1)"
    ]


def test_the_newest_release_is_the_plugins_version():
    manifest = json.loads((KIT_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    newest = next(iter(releases(CHANGELOG)))

    assert changelog.release_of(newest) == manifest["version"]


def test_an_older_kits_heading_is_read_but_named():
    assert changelog.release_of("## v1.2.3") == "1.2.3"
    assert changelog.release_of("## [1.2.3] — 2026-11-21") == "1.2.3"
    assert changelog.release_of("## v1.2.3 — dated") is None


@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        ("- " + "x" * (CAP + 1) + " (#1)", f"{CAP + 1} characters, over the cap of {CAP}"),
        ("- Replies are shorter; progress counts messages (#1)", "welded"),
        ("- Replies are shorter — progress counts messages (#1)", "welded"),
        ("- Replies are shorter - progress counts messages (#1)", "welded"),
    ],
)
def test_each_breach_of_the_style_is_named(entry, reason):
    (found,) = changelog.violations(["### Changed", entry])

    assert reason in found


def test_an_aside_between_two_dashes_is_one_claim():
    entry = "- A tier names routes — a model and its provider — instead of models (#656)"

    assert changelog.violations(["### Changed", entry]) == []


def test_the_cap_counts_the_claim_and_not_its_references():
    assert changelog.violations(["### Fixed", "- " + "x" * CAP + " (#1, #22)"]) == []
    assert changelog.violations(["### Added", "- " + "x" * CAP]) == []


def test_a_group_appears_once_and_only_the_four_are_used():
    section = ["### Added", "- a (#1)", "### Added", "- b (#2)", "### Security", "- c (#3)"]

    assert changelog.violations(section) == [
        "Added: a second block, where one per release collects them",
        "Security: not one of Added, Changed, Fixed, Removed",
    ]


def test_a_kit_issue_is_named_with_the_kits_repository():
    entry = "a fix (#9, #12), after #3, not `a/b#4` or x#5"

    assert (
        changelog.qualify(entry, "o/kit")
        == "a fix (o/kit#9, o/kit#12), after o/kit#3, not `a/b#4` or x#5"
    )
