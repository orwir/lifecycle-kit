"""A `<file>.md § <heading>` the kit writes points at a heading that exists, so a renamed
section cannot leave the guides, the skills, the reviewer, the upgrade steps or a repository's
ported contract pointing at nothing. A bare `§ <heading>` in a skill or the reviewer definition
means a section of task_review.md, as they say; a bare `§ <number>` is a skill's own step.

What a match checks: a reference's words open with a heading's name (its numbering, emphasis
and the gloss after a dash dropped) for at least the name's first two words, or all the
reference has; a dotted number (`§ Phase 5.7`) must open some heading. So a heading reworded
after its second word keeps old references passing, and a rename is caught when its first two
words change."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
METHOD = ROOT / "method"
_REFTEXT = r"(\*[^*\n]+\*|(?:[^,.;:()`*\[\]\n|§]|(?<=\d)\.(?=\d)|:(?=\s+[A-Z]))+)"
REF = re.compile(r"([\w./-]+\.md)`?\]?(?:\([^)]*\))?\s*§\s*" + _REFTEXT)
BARE = re.compile(r"§\s*" + _REFTEXT)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)
FENCE = re.compile(r"^(```+|~~~+).*?^\1\s*$", re.M | re.S)
#: Files a reference may name that are a repository's own, not the kit's.
REPOSITORY_FILES = {"vision.md"}


def sources():
    yield from METHOD.glob("*.md")
    yield from ROOT.glob("skills/*/SKILL.md")
    yield from ROOT.glob("agents/*.md")
    yield from (ROOT / "docs" / "guide.md", ROOT / "README.md", ROOT / "AGENTS.md")
    yield from (ROOT / "UPGRADING.md", ROOT / "CHANGELOG.md")


def text_of(path):
    text = path.read_text(encoding="utf-8")
    # The changelog's released entries are history; only its header is read.
    return text.split("\n---\n")[0] if path.name == "CHANGELOG.md" else text


def words(text):
    """Lower-case words, a possessive's `'s` or `'` dropped."""
    return re.findall(r"[\w-]+", re.sub(r"'s?\b", "", text.lower()))


def name(heading):
    """A heading's name: without its numbering, emphasis or the gloss after a dash."""
    heading = re.sub(r"^\d+\.\s+", "", heading.replace("*", ""))
    return re.split(r"\s+—\s+", heading)[0]


def headings(path, body_of_template=False):
    """The headings outside fenced blocks; a template's body is read from inside its fence."""
    text = path.read_text(encoding="utf-8")
    if body_of_template:
        text = text.split("````\n")[1]
    return [name(h) for h in HEADING.findall(FENCE.sub("", text))]


def targets():
    """The heading sets each file name must resolve in. `AGENTS.md` is both a repository's,
    ported from the AGENTS template, and the kit's own, which runs the same skills."""
    named = {p.name: [headings(p)] for p in METHOD.glob("*.md")}
    named["guide.md"] = [headings(ROOT / "docs" / "guide.md")]
    named["AGENTS.md"] = [
        headings(METHOD / "agents_template.md", body_of_template=True),
        headings(ROOT / "AGENTS.md"),
    ]
    named["CONTRIBUTING.md"] = [headings(METHOD / "contributing_template.md")]
    return named


def resolves(ref, heads):
    number = re.search(r"\d+\.\d+", ref)
    if number:
        return any(words(h)[:2] == words(number.group()) for h in heads)
    said = words(ref)
    for head in map(words, heads):
        common = next(
            (i for i, (a, b) in enumerate(zip(said, head, strict=False)) if a != b),
            min(len(said), len(head)),
        )
        if head and common >= min(2, len(head), len(said)):
            return True
    return False


def refs(paths):
    for source in paths:
        text = text_of(source)
        qualified = []
        for match in REF.finditer(text):
            qualified.append((match.start(), match.start(2)))
            yield source, match.group(1).split("/")[-1], match.group(2)
        if source.name != "SKILL.md" and source.parent.name != "agents":
            continue
        for match in BARE.finditer(text):
            inside = any(start <= match.start() < end for start, end in qualified)
            ref = match.group(1).strip()
            if not inside and ref and not ref[0].isdigit():
                yield source, "task_review.md", ref


def where(path):
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name


def broken(paths):
    named = targets()
    for source, target, ref in refs(paths):
        if target in REPOSITORY_FILES:
            continue
        sets = named.get(target)
        if sets is None or not all(resolves(ref, heads) for heads in sets):
            yield f"{where(source)}: {target} § {ref.strip()}"


def test_every_section_reference_names_a_heading_that_exists():
    found = list(broken(sources()))
    assert not found, "\n".join(found)


def test_the_tree_holds_the_references_it_is_meant_to_read():
    assert len(list(refs(sources()))) >= 120


@pytest.mark.parametrize(
    "text, ok",
    [
        ("see `task_review.md` § The plan round awaits none", True),
        ("see task_review.md § A section that is gone", False),
        ("see task_review.md § The planning round", False),
        ("[task_review.md](https://x/task_review.md) § Developer rules", True),
        ("`design_workflow.md` § *Round*", True),
        ("`codebase_review.md` § Phase 5.7", True),
        ("`codebase_review.md` § Phase 5.99", False),
    ],
)
def test_a_reference_resolves_only_to_a_heading_that_exists(text, ok):
    (match,) = REF.finditer(text)
    target = match.group(1).split("/")[-1]
    assert all(resolves(match.group(2), heads) for heads in targets()[target]) is ok


def test_each_reference_in_a_clause_is_read_and_a_bare_one_too(tmp_path):
    skill = tmp_path / "skills" / "x" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("By § Plan packet and § Gone rules; see § 3.\n", encoding="utf-8")
    assert [ref.strip() for _, _, ref in refs([skill])] == ["Plan packet and", "Gone rules"]
    assert list(broken([skill])) == ["SKILL.md: task_review.md § Gone rules"]


def test_a_guide_the_kit_does_not_hold_is_reported_and_a_repository_file_skipped(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(
        "See `removed_guide.md` § Anything, and `vision.md` § CUJs.\n", encoding="utf-8"
    )
    assert list(broken([page])) == ["page.md: removed_guide.md § Anything"]


def test_a_heading_inside_a_fence_is_no_heading(tmp_path):
    page = tmp_path / "guide.md"
    page.write_text("# Real\n\n```\n## Fenced\n```\n", encoding="utf-8")
    assert headings(page) == ["Real"]
