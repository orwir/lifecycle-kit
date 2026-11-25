"""The two briefs in task_review.md, the Clarify brief and the hand-back brief, share a shape:
the status on the first line, *For you* as the last block, no bullet kept only to say
`nothing`, no term of the method the maintainer cannot act on, and one *Taken alone* block —
a row per choice taken alone, per issue filed, per gap no issue could be filed for, and per
`Watch:` line, a risk nothing has met yet that the maintainer files by naming it. A copy that
loses or reorders a row, or puts a line that carries no news back, is caught here."""

import re
from pathlib import Path

import pytest

TASK_REVIEW = Path(__file__).resolve().parents[1] / "method" / "task_review.md"
LEAD = "**Taken alone** (veto by naming one)"
ROWS = ("- <what> — <why>.", "- Filed [", "- Not filed: <", "- Watch: <")
STATUS = "· <<n> decision(s) | ready"
TERMS = ("no shape", "(no guard)", "micro-task")
WATCH = "Watch: <the risk: what breaks, and how it shows> — "


def section(text, name):
    """The text under a `## <name>` heading, to the next one."""
    return text.split(f"\n## {name}\n", 1)[1].split("\n## ", 1)[0]


def template(text, name):
    """The first fenced block under a `## <name>` heading."""
    return section(text, name).split("```\n", 2)[1]


def blocks(block):
    """A brief's blocks, as the blank lines between them part them."""
    return [part for part in block.strip().split("\n\n") if part.strip()]


def rows(block, lead):
    """The rows of a brief's block, from its lead to the next blank line."""
    lines = block.splitlines()
    if lead not in lines:
        return []
    found = []
    for line in lines[lines.index(lead) + 1 :]:
        if not line.strip():
            break
        found.append(line)
    return found


def taken_alone(block):
    """The rows of a brief's *Taken alone* block."""
    return rows(block, LEAD)


def problems(found):
    """What keeps a *Taken alone* block from the rows both briefs share, in their order."""
    if len(found) != len(ROWS):
        return [f"{len(found)} rows, not {len(ROWS)}"]
    return [
        f"row {i + 1} does not open `{lead}`"
        for i, (row, lead) in enumerate(zip(found, ROWS, strict=True))
        if not row.startswith(lead)
    ]


def shape_problems(block):
    """What keeps a brief's template from the shape both share: the status on its first
    line, *For you* last, no bullet that offers `nothing`, no term of the method."""
    parts = blocks(block)
    found = []
    if STATUS not in parts[0].splitlines()[0]:
        found.append("the first line carries no status")
    if not parts[-1].startswith("**For you:**"):
        found.append("*For you* is not the last block")
    found += [
        f"`{line.split(':')[0]}` offers nothing"
        for line in block.splitlines()
        if line.startswith("- ") and re.search(r"\|\s*nothing>", line)
    ]
    return found + [f"prints `{term}`" for term in TERMS if term in block]


def brief(name):
    return template(TASK_REVIEW.read_text(encoding="utf-8"), name)


@pytest.mark.parametrize("name", ["Clarify brief", "Hand-back brief"])
def test_each_brief_carries_the_same_taken_alone_rows_a_watch_line_among_them(name):
    assert problems(taken_alone(brief(name))) == []


def test_a_brief_that_lost_its_watch_row_or_reordered_its_rows_is_caught():
    lost = f"{LEAD}\n- <what> — <why>.\n- Filed [x]\n- Not filed: <x>\n\n**Reviewed:** x\n"
    assert problems(taken_alone(lost)) == ["3 rows, not 4"]
    swapped = f"{LEAD}\n- <what> — <why>.\n- Filed [x]\n- Watch: <x>\n- Not filed: <x>\n"
    assert problems(taken_alone(swapped)) == [
        "row 3 does not open `- Not filed: <`",
        "row 4 does not open `- Watch: <`",
    ]


@pytest.mark.parametrize("name", ["Clarify brief", "Hand-back brief"])
def test_each_brief_opens_with_its_status_ends_with_for_you_and_carries_no_empty_line(name):
    assert shape_problems(brief(name)) == []


def test_a_brief_with_its_ask_up_top_an_empty_bullet_or_a_method_term_is_caught():
    old = (
        "**Plan [#1](u)** · x\n\n<goal>\n\n**For you:** say go.\n\n**What we plan**\n"
        "- You see: <what | nothing>\n- Under it: <how>\n\n**Reviewed:** skipped, no shape\n"
    )
    assert shape_problems(old) == [
        "the first line carries no status",
        "*For you* is not the last block",
        "`- You see` offers nothing",
        "prints `no shape`",
    ]


def test_the_clarify_brief_says_today_against_after_and_the_plans_file_count():
    assert rows(brief("Clarify brief"), "**What we plan**")[1].endswith("; <n> file(s)")
    assert blocks(brief("Clarify brief"))[1] == (
        "Today <what is so now>. After this, <what will be so>."
    )


def test_a_skipped_review_names_every_shape_the_round_is_for():
    text = TASK_REVIEW.read_text(encoding="utf-8")
    shapes = next(line for line in text.splitlines() if line.startswith("- **The four shapes,**"))
    skipped = brief("Clarify brief").split("| skipped: ", 1)[1].splitlines()[0]
    for terms in ("persisted, billed, auth or safety state", "wait, retry or failure"):
        assert terms in shapes and terms in skipped


def test_going_ahead_waits_for_no_go_only_after_a_skipped_review():
    clarify = brief("Clarify brief")
    assert "| going ahead>" in clarify.splitlines()[0]
    assert (
        "nothing to answer after a skipped review, and no drawing: going ahead"
        in (blocks(clarify)[-1])
    )


def test_the_hand_back_says_what_changed_its_size_and_a_landing_risk():
    changed = rows(brief("Hand-back brief"), "**What changed**")
    assert [row.split(":")[0] for row in changed] == [
        "- You see",
        "- Under it",
        "- Removed",
        "- Size",
        "- Risk",
    ]
    assert changed[1].startswith("- Under it: <as planned | the departures from the accepted plan")
    assert changed[4] == ("- Risk: <what landing does that a revert does not undo>; undo: <how>")


def test_a_green_gate_says_only_how_many_tests_fail_without_the_change():
    verified = next(
        line for line in brief("Hand-back brief").splitlines() if line.startswith("**Verified:**")
    )
    assert verified.startswith("**Verified:** gate green · <<n> test(s) fail without the change")
    assert not re.search(r"passed|coverage|lint", verified)


@pytest.mark.parametrize("name", ["Clarify brief", "Hand-back brief"])
def test_a_watch_row_names_the_risk_as_the_plans_watch_line_does(name):
    assert taken_alone(brief(name))[3].startswith(f"- {WATCH}")
    rules = section(TASK_REVIEW.read_text(encoding="utf-8"), "Developer rules")
    assert f"`{WATCH}<its trigger>`" in rules


def test_no_word_count_caps_a_brief_and_two_questions_shape_it():
    rules = section(TASK_REVIEW.read_text(encoding="utf-8"), "Brief rules")
    assert not re.search(r"\b\d+ words\b", rules)
    assert "can the maintainer tell from the brief alone what the change is about" in rules
    assert "make an informed decision?" in rules
    assert "something that decision needs and the maintainer does not already know?" in rules
