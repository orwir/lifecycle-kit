"""The protected branch's two guards: refuse a push to it, and a deploy of a head no PR merged.

The protected branch takes only release-PR merges, which GitHub makes, so no push
from a checkout ever targets it. A private repository on GitHub's free plan cannot
have branch protection, so these hold the rule instead: the push guard runs as the
pre-push hook, and the deploy guard runs in the deploy workflow before anything is
built, the one check that holds however the branch moved.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Iterable

ATTEMPTS = 3
WAIT_SECONDS = 10


def pushed_refs(lines: Iterable[str]) -> list[str]:
    """The remote refs of a pre-push hook's stdin: ``<local ref> <sha> <remote ref> <sha>``."""
    return [parts[2] for parts in (line.split() for line in lines) if len(parts) == 4]


def push(protected: str, lines: Iterable[str] | None = None) -> int:
    target = f"refs/heads/{protected}"
    from_pre_commit = os.environ.get("PRE_COMMIT_REMOTE_BRANCH")
    refs = [from_pre_commit] if from_pre_commit else pushed_refs(lines or [])
    if target not in refs:
        return 0
    print(
        f"push-guard: refused a push to {protected}. It takes only release-PR merges; "
        "push the integration branch or a feature branch instead.",
        file=sys.stderr,
    )
    return 1


def merged_as(pulls: list[dict], sha: str, base: str) -> dict | None:
    """The pull request into ``base`` whose merge made ``sha``, if one did."""
    for pr in pulls:
        if pr.get("merged_at") and pr.get("merge_commit_sha") == sha and pr["base"]["ref"] == base:
            return pr
    return None


def _recent_merges(repo: str, base: str) -> list[dict]:
    endpoint = (
        f"repos/{repo}/pulls?state=closed&base={base}&sort=updated&direction=desc&per_page=30"
    )
    out = subprocess.run(["gh", "api", endpoint], check=True, capture_output=True, encoding="utf-8")
    return json.loads(out.stdout)


def deploy(protected: str, repo: str, sha: str, wait: float = WAIT_SECONDS) -> int:
    """Fails closed: a failed read fails the step. The retry covers a PR that reads as
    merged a moment after its push event fires."""
    for attempt in range(ATTEMPTS):
        pr = merged_as(_recent_merges(repo, protected), sha, protected)
        if pr is not None:
            print(f"deploy-guard: {sha[:8]} is the merge of #{pr['number']} into {protected}.")
            return 0
        if attempt < ATTEMPTS - 1:
            time.sleep(wait)
    print(
        f"deploy-guard: refused. {sha[:8]} is not the merge commit of a pull request into "
        f"{protected}, so it reached {protected} some other way. Put {protected} back on the "
        "last release's merge commit, then ship through a release PR.",
        file=sys.stderr,
    )
    return 1
