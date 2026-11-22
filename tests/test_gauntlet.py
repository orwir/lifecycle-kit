"""The idea gauntlet reads for a game without asking more of a software or hardware idea:
a game's readings are `[game]` lines that continue an item, a rule or a gate, so every phase
of the template keeps the items it asks of every idea."""

import re
from pathlib import Path

GUIDE = Path(__file__).resolve().parents[1] / "method" / "idea_gauntlet.md"
#: The checklist items each phase of the template asks of every idea.
ITEMS = {0: 4, 1: 11, 2: 10, 3: 3, 4: 5}
REASONS = ("Solved by X", "Adapt X", "Blocked by Y", "Not worth it", "Disproved")


def guide():
    return GUIDE.read_text(encoding="utf-8")


def template():
    """The body of the fenced template an idea's IDEA.md is copied from."""
    return guide().split("## Template", 1)[1].split("```\n", 2)[1]


def phases():
    parts = re.split(r"^## Phase (\d) .*$", template(), flags=re.M)
    return {int(n): body for n, body in zip(parts[1::2], parts[2::2], strict=True)}


def rule(n):
    rules = guide().split("## The rules", 1)[1].split("\n## ", 1)[0]
    return re.split(r"^\d+\. ", rules, flags=re.M)[n]


def test_a_game_reading_adds_no_item():
    found = phases()
    assert sorted(found) == sorted(ITEMS)
    for n, body in found.items():
        assert len(re.findall(r"^- \[ \] ", body, re.M)) == ITEMS[n], f"Phase {n}"
        assert "[game]" in body, f"Phase {n} has no game reading"
    lines = template().splitlines()
    for i, line in enumerate(lines):
        if "[game]" in line:
            assert not line.startswith("- [ ]"), line
            assert lines[i - 1].strip(), f"stands alone: {line}"


def test_each_exit_and_gate_reads_for_a_game():
    """Phase 1's early exit and both gates are where an idea's path turns: a game's
    reading continues each one's paragraph."""
    paragraphs = re.split(r"\n\s*\n", template())
    turns = [p for p in paragraphs if re.match(r"(EARLY EXIT|GATE)\b", p)]
    assert len(turns) == 3
    for turn in turns:
        assert "\n[game] " in turn, turn.splitlines()[0]


def test_type_names_game_beside_the_build():
    assert re.search(r"^- Type: software \| hardware \| mixed\[, game\]$", template(), re.M)
    first = re.search(r"^- \[ \] (.+)$", phases()[0], re.M).group(1)
    assert first.startswith("Type and appetite")


def test_the_rules_read_for_a_game():
    for n in (3, 4, 5):
        assert "[game]" in rule(n), f"rule {n}"
    reading = rule(3).split("[game]", 1)[1]
    for reason in REASONS:
        assert f"**{reason}" in reading, reason
