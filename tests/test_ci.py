"""The kit's CI runs where its commits land: tasks on the integration branch, releases on
``main``, which the marketplace serves."""

from __future__ import annotations

import re

from lifecycle import KIT_ROOT
from lifecycle.config import load

CI = KIT_ROOT / ".github" / "workflows" / "ci.yml"


def push_branches(workflow: str) -> set[str]:
    """The branches under ``on: push:``, written as the flow list ``[a, b]``."""
    found = re.search(r"^  push:\n    branches: \[([^\]]*)\]", workflow, re.MULTILINE)
    return {name.strip() for name in found.group(1).split(",")} if found else set()


def test_ci_runs_on_a_push_to_main_and_to_the_integration_branch():
    integration = load(KIT_ROOT).integration

    assert {"main", integration} <= push_branches(CI.read_text(encoding="utf-8"))


def test_a_push_trigger_in_another_shape_names_no_branch():
    assert push_branches("on:\n  push:\n    branches:\n      - main\n") == set()
    assert push_branches("on:\n  push:\n    branches: [main, next]\n") == {"main", "next"}
