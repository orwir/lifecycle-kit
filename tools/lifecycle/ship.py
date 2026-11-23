"""Ship a reviewed commit: dispatch the release workflow on it and watch the run to its end.

The workflow is the repository's own (``[release] workflow``), built on the kickstart's
recipe. Before it builds, it refuses a ref other than the integration branch or a hotfix
branch, a head other than the commit the review read, and a version released already, each
in a step named in ``REFUSALS``; then it builds, ships and tags. A tag pushed from a checkout
ships nothing, so this dispatch is the one way a release starts. Once GitHub has taken the
dispatch, an outcome this command did not see is reported as in flight, never as failed: the
run may still ship.
"""

from __future__ import annotations

import json
import re
import subprocess
import time

#: The recipe's refusal steps, by the name each carries in the workflow.
WRONG_REF = "Refuse a ref other than the integration or a hotfix branch"
MOVED = "Refuse a head the review did not read"
TAGGED = "Refuse a version released already"
REFUSALS = (WRONG_REF, MOVED, TAGGED)

#: Exit codes: argparse takes 2 for a usage error, so no outcome here uses it.
SHIPPED, FAILED, MOVED_SINCE_REVIEW, IN_FLIGHT = 0, 1, 3, 4
POLL_SECONDS = 15
CALL_SECONDS = 60
READ_ATTEMPTS = 3
FIND_ATTEMPTS = 8
TIMEOUT_SECONDS = 3 * 60 * 60
_RUN_URL = re.compile(r"https://\S+/actions/runs/(\d+)")


class ReleaseError(Exception):
    pass


class Refused(ReleaseError):
    """GitHub answered the request with a 4xx: it did nothing."""


_REFUSED = re.compile(r"HTTP 4\d\d")


def gh(*args: str) -> str:
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=CALL_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise ReleaseError(f"gh {' '.join(args[:2])} gave no answer in {CALL_SECONDS} s") from error
    if result.returncode != 0:
        failed = Refused if _REFUSED.search(result.stderr) else ReleaseError
        raise failed(f"gh {' '.join(args[:2])} failed: {result.stderr.strip()}")
    return result.stdout


def read(*args: str, none: str = "") -> str | None:
    """A read, safe to repeat, so a passing failure of ``gh`` is retried a bounded number
    of times. The dispatch is never retried: a second one would start a second run. A failure
    whose message holds ``none`` is gh's way of answering "nothing": ``None``, not retried."""
    for attempt in range(READ_ATTEMPTS):
        try:
            return gh(*args)
        except ReleaseError as error:
            if none and none in str(error):
                return None
            if attempt == READ_ATTEMPTS - 1:
                raise
            time.sleep(POLL_SECONDS)
    raise AssertionError("unreachable")


def _runs(workflow: str, ref: str) -> set[int]:
    listed = read(
        "run", "list", "--workflow", workflow, "--branch", ref, "--event", "workflow_dispatch",
        "--limit", "20", "--json", "databaseId",
    )  # fmt: skip
    return {run["databaseId"] for run in json.loads(listed)}


def find(printed: str, workflow: str, ref: str, before: set[int]) -> str:
    """The id of the run a dispatch started: from the URL gh printed, or, where it printed
    none, the one run on ``ref`` that was not there before the dispatch."""
    found = _RUN_URL.search(printed)
    if found:
        return found.group(1)
    for attempt in range(FIND_ATTEMPTS):
        new = sorted(_runs(workflow, ref) - before)
        if len(new) > 1:
            raise ReleaseError(f"{len(new)} runs of {workflow} started on {ref} at once")
        if new:
            return str(new[0])
        if attempt < FIND_ATTEMPTS - 1:
            time.sleep(POLL_SECONDS)
    raise ReleaseError(f"the run of {workflow} on {ref} never appeared")


def watch(run_id: str) -> dict:
    """The run once it has completed; a run still going at the timeout is the caller's."""
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while True:
        run = json.loads(read("run", "view", run_id, "--json", "status,conclusion,url,jobs"))
        if run["status"] == "completed":
            return run
        if time.monotonic() >= deadline:
            raise ReleaseError(f"run {run_id} is still {run['status']} at {run['url']}")
        time.sleep(POLL_SECONDS)


def outcome(run: dict, ref: str, commit: str) -> tuple[int, str]:
    """The exit code and the line that say how a completed run ended."""
    url = run["url"]
    if run["conclusion"] == "success":
        return SHIPPED, f"shipped {commit[:8]} from {ref}: {url}"
    failed = [
        (job["name"], step["name"])
        for job in run.get("jobs", [])
        for step in job.get("steps", [])
        if step.get("conclusion") == "failure"
    ]
    for _, step in failed:
        if step == MOVED:
            return MOVED_SINCE_REVIEW, (
                f"refused: {ref} moved since the review, so its head is not {commit[:8]}. "
                "Check the release's version and changelog against the new head, and its "
                f"milestone where the checklist does, review it, then ship that: {url}"
            )
        if step == TAGGED:
            return (
                FAILED,
                f"refused: this version is tagged already, or its tags could not be read: {url}",
            )
        if step == WRONG_REF:
            return FAILED, f"refused: {ref} is not the integration branch or a hotfix branch: {url}"
    if failed:
        job, step = failed[0]
        return FAILED, f"failed at {job} > {step}: {url}"
    return FAILED, f"the run ended {run['conclusion']}: {url}"


def release(workflow: str, ref: str, commit: str) -> tuple[int, str]:
    before = _runs(workflow, ref)
    try:
        printed = gh("workflow", "run", workflow, "--ref", ref, "-f", f"commit={commit}")
    except Refused:
        raise
    except ReleaseError:
        printed = ""  # no answer, or one lost after the request went out: look for the run
    try:
        run_id = find(printed, workflow, ref, before)
        print(f"release: dispatched {workflow} on {ref} for {commit[:8]}, run {run_id}", flush=True)
        return outcome(watch(run_id), ref, commit)
    except ReleaseError as error:
        return IN_FLIGHT, (
            f"in flight: {workflow} was dispatched on {ref}, but its end was not seen ({error}). "
            "It may still ship and tag: find it in the repository's Actions, and dispatch "
            "nothing again until it has ended."
        )
