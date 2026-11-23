"""The kit's CI runs where its commits land: tasks on the integration branch, releases on
``main``, which the marketplace serves, and a hotfix on its own branch, so the release that
ships it reads its CI."""

from __future__ import annotations

import pytest
from lifecycle import KIT_ROOT, ci
from lifecycle.config import load


@pytest.mark.parametrize("branch", ["main", load(KIT_ROOT).integration, "hotfix/a-fix"])
def test_ci_runs_on_a_push_where_the_kit_lands_or_ships(branch):
    assert ci.runs_on(KIT_ROOT, "push", branch)


def test_ci_runs_on_no_other_push():
    assert not ci.runs_on(KIT_ROOT, "push", "probe/1.2.3")
