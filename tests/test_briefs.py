"""The two briefs in task_review.md, the Clarify brief and the hand-back brief, carry one
*Taken alone* block: a row per choice taken alone, per issue filed, per gap no issue could be
filed for, and per `Watch:` line, a trigger nothing has met yet that the maintainer files by
naming it. A copy that loses or reorders a row, the `Watch:` row above all, is caught here."""

from pathlib import Path

import pytest

TASK_REVIEW = Path(__file__).resolve().parents[1] / "method" / "task_review.md"
LEAD = "**Taken alone** (veto by naming one)"
ROWS = ("- <what> — <why>.", "- Filed [", "- Not filed: <", "- Watch: <")


def template(text, section):
    """The first fenced block under a `## <section>` heading."""
    body = text.split(f"\n## {section}\n", 1)[1].split("\n## ", 1)[0]
    return body.split("```\n", 2)[1]


def taken_alone(block):
    """The rows of a brief's *Taken alone* block, from its lead to the next blank line."""
    lines = block.splitlines()
    if LEAD not in lines:
        return []
    rows = []
    for line in lines[lines.index(LEAD) + 1 :]:
        if not line.strip():
            break
        rows.append(line)
    return rows


def problems(rows):
    """What keeps a *Taken alone* block from the rows both briefs share, in their order."""
    if len(rows) != len(ROWS):
        return [f"{len(rows)} rows, not {len(ROWS)}"]
    return [
        f"row {i + 1} does not open `{lead}`"
        for i, (row, lead) in enumerate(zip(rows, ROWS, strict=True))
        if not row.startswith(lead)
    ]


@pytest.mark.parametrize("section", ["Clarify brief", "Hand-back brief"])
def test_each_brief_carries_the_same_taken_alone_rows_a_watch_line_among_them(section):
    assert problems(taken_alone(template(TASK_REVIEW.read_text(encoding="utf-8"), section))) == []


def test_a_brief_that_lost_its_watch_row_or_reordered_its_rows_is_caught():
    lost = f"{LEAD}\n- <what> — <why>.\n- Filed [x]\n- Not filed: <x>\n\n**Reviewed:** x\n"
    assert problems(taken_alone(lost)) == ["3 rows, not 4"]
    swapped = f"{LEAD}\n- <what> — <why>.\n- Filed [x]\n- Watch: <x>\n- Not filed: <x>\n"
    assert problems(taken_alone(swapped)) == [
        "row 3 does not open `- Not filed: <`",
        "row 4 does not open `- Watch: <`",
    ]
