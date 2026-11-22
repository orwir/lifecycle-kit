"""The two reviewer returns in task_review.md, the plan return and the return packet, are two
copies of one format: the required count where a verdict stood, then each finding as a block
whose evidence is marked `seen` or `inferred`. A copy that drifts back to a verdict or a table
row, or loses a line of the block, is caught here."""

import re
from pathlib import Path

import pytest

TASK_REVIEW = Path(__file__).resolve().parents[1] / "method" / "task_review.md"
HEADER = re.compile(r"^[A-Z]\d+ · <severity> · <[^>]+>$")
BLOCK = ("Claim: <", "Evidence: <seen | inferred> — <", "Action: <")


def template(text, section):
    """The first fenced block under a `## <section>` heading."""
    body = text.split(f"\n## {section}\n", 1)[1].split("\n## ", 1)[0]
    return body.split("```\n", 2)[1]


def problems(block):
    """What keeps a return template from the required line and the finding block."""
    lines = block.splitlines()
    found = []
    if not lines or not lines[0].startswith("Required: "):
        found.append("the first line is not `Required:`")
    if any(line.startswith("Verdict:") for line in lines):
        found.append("a verdict")
    if any(line.startswith("|") for line in lines):
        found.append("a table row")
    headers = [i for i, line in enumerate(lines) if HEADER.match(line)]
    if not headers:
        found.append("no finding header")
    for i in headers:
        following = lines[i + 1 : i + 1 + len(BLOCK)]
        if len(following) < len(BLOCK) or not all(
            line.startswith(lead) for line, lead in zip(following, BLOCK, strict=True)
        ):
            found.append(f"the block under line {i + 1} lacks claim, evidence and action")
    return found


@pytest.mark.parametrize("section", ["Plan return", "Return packet"])
def test_each_return_opens_with_the_required_count_and_holds_findings_as_blocks(section):
    assert problems(template(TASK_REVIEW.read_text(encoding="utf-8"), section)) == []


def test_a_verdict_a_table_row_or_a_block_missing_its_evidence_is_caught():
    old = (
        "Verdict: approve | corrections\n\nFindings:\n| id | location | severity |\n"
        "| R1 | <path:line> | Real bug |\n"
    )
    assert problems(old) == [
        "the first line is not `Required:`",
        "a verdict",
        "a table row",
        "no finding header",
    ]
    unmarked = (
        "Required: none\n\nR1 · <severity> · <path:line>\nClaim: <x>\nEvidence: <x>\nAction: <x>\n"
    )
    assert problems(unmarked) == ["the block under line 3 lacks claim, evidence and action"]
