"""Wait on the CI a push started, or on a pull request's checks, and say how it ended.

A push's CI is the runs that push started (``gh run list --commit --event push --branch``);
a pull request's is every check ``gh pr checks`` lists, third-party ones included. Whether
CI is expected at all is read from the repository's workflows: their ``on:`` triggers and
branch and tag filters, never their ``paths``, so a push a ``paths`` filter skipped reads as
missing, not as passed. Nothing unread is ever reported as passed.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import ship

#: Exit codes: argparse takes 2 for a usage error, and a failed read is ``lifecycle:``'s 1.
PASSED, FAILED, MISSING, RUNNING, SUPERSEDED = 0, 1, 3, 4, 5
#: A run's conclusions, and a pull request check's buckets, that are not a failure.
PASSING = frozenset({"success", "skipped", "neutral", "pass", "skipping"})
POLL_SECONDS = 15
FIND_READS = 5
FIND_SECONDS = 60
TIMEOUT_SECONDS = 60 * 60
NO_CHECKS = "no checks reported"


@dataclass(frozen=True)
class Check:
    key: str
    name: str
    workflow: str
    done: bool
    conclusion: str
    url: str

    @property
    def passed(self) -> bool:
        return self.conclusion in PASSING


# --- Whether a workflow runs on an event for a branch ---------------------------------------

_ON = re.compile(r"""^(?:on|"on"|'on')\s*:(.*)$""")
_COMMENT = re.compile(r"(?:^|\s)#.*$")
_FILTERS = ("branches", "branches-ignore", "tags", "tags-ignore")


def _lines(text: str) -> list[tuple[int, str]]:
    """Each line that holds anything, its comment cut, as (indent, content)."""
    found = []
    for raw in text.splitlines():
        line = _COMMENT.sub("", raw).rstrip()
        if line.strip():
            found.append((len(line) - len(line.lstrip(" ")), line.strip()))
    return found


def _under(lines: list[tuple[int, str]], at: int) -> list[tuple[int, str]]:
    """The lines that belong to the key on line ``at``: deeper ones, and a sequence's items
    at the key's own indent, which YAML allows."""
    indent = lines[at][0]
    body = []
    for line in lines[at + 1 :]:
        if line[0] > indent or (line[0] == indent and line[1].startswith("- ")):
            body.append(line)
        else:
            break
    return body


def _scalar(raw: str) -> str | None:
    """A plain or quoted scalar; ``None`` for what this reader does not follow: an alias, an
    anchor, a tag, a block scalar, a flow collection."""
    raw = raw.strip()
    if len(raw) > 1 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    if not raw or raw[0] in "*&!|>[]{}":
        return None
    return raw


def _flow(value: str) -> list[str] | None:
    """``[a, 'b']`` closed on its own line, or a lone scalar, as a list; ``None`` otherwise."""
    if value.startswith("["):
        if not value.endswith("]"):
            return None
        items = [_scalar(item) for item in value[1:-1].split(",") if item.strip()]
    else:
        items = [_scalar(value)]
    return None if None in items else items


def _items(lines: list[tuple[int, str]]) -> list[str] | None:
    """A block sequence's items; ``None`` where a line is not one."""
    if not lines or not all(content.startswith("- ") for _, content in lines):
        return None
    return _flow(",".join(content[2:] for _, content in lines).join("[]"))


def _filters(lines: list[tuple[int, str]]) -> dict[str, list[str]] | None:
    """An event's branch and tag filters; ``None`` where one could not be read."""
    found: dict[str, list[str]] = {}
    if not lines:
        return found
    child = lines[0][0]
    for at, (indent, content) in enumerate(lines):
        key, _, value = content.partition(":")
        if indent != child or _scalar(key) not in _FILTERS:
            continue
        listed = _flow(value.strip()) if value.strip() else _items(_under(lines, at))
        if listed is None:
            return None
        found[_scalar(key)] = listed
    return found


def triggers(text: str) -> dict[str, dict[str, list[str]] | None] | None:
    """A workflow's events, each with its branch and tag filters (``None`` where they could
    not be read); ``None`` for a workflow whose ``on:`` could not be read at all."""
    lines = _lines(text)
    at = next((i for i, (indent, c) in enumerate(lines) if indent == 0 and _ON.match(c)), None)
    if at is None:
        return None
    rest = _ON.match(lines[at][1]).group(1).strip()
    if rest:
        listed = _flow(rest)
        return None if listed is None else {event: {} for event in listed}
    body = _under(lines, at)
    if not body:
        return None
    if body[0][1].startswith("- "):
        listed = _items([line for line in body if line[0] == body[0][0]])
        return None if listed is None else {event: {} for event in listed}
    child = body[0][0]
    events: dict[str, dict[str, list[str]] | None] = {}
    for i, (indent, content) in enumerate(body):
        if indent != child:
            continue
        key, colon, value = content.partition(":")
        if not colon or _scalar(key) is None:
            return None
        value = value.strip()
        if not value or value in ("null", "~", "{}"):
            events[_scalar(key)] = _filters(_under(body, i))
        else:
            events[_scalar(key)] = None
    return events


def _glob(pattern: str) -> re.Pattern[str]:
    """GitHub's filter pattern: ``*`` stops at ``/``, ``**`` does not; ``?``, ``+`` and a
    ``[…]`` class mean what they mean in a regular expression; anything else is literal."""
    parts = re.split(r"(\*\*|\*|\?|\+|\[[^\]]*\])", pattern)
    special = {"**": ".*", "*": "[^/]*", "?": "?", "+": "+"}
    return re.compile(
        "".join(
            special.get(part, part) if i % 2 else re.escape(part) for i, part in enumerate(parts)
        )
    )


def _included(patterns: list[str], branch: str) -> bool:
    """In order, as GitHub reads them: a ``!`` pattern takes back what an earlier one let in."""
    hit = False
    for pattern in patterns:
        negated = pattern.startswith("!")
        if _glob(pattern[1:] if negated else pattern).fullmatch(branch):
            hit = not negated
    return hit


def _on_branch(filters: dict[str, list[str]], branch: str) -> bool:
    if "branches" in filters:
        return _included(filters["branches"], branch)
    if "branches-ignore" in filters:
        return not _included(filters["branches-ignore"], branch)
    # Tags filtered and branches not: GitHub runs it on no branch at all.
    return not ("tags" in filters or "tags-ignore" in filters)


def expecting(root: Path, event: str, branch: str) -> list[str]:
    """The workflows under ``.github/workflows/`` that run on ``event`` for ``branch`` (the
    pushed branch for a push, the base for a pull request), each a path, and where it was
    counted only because it could not be read, why: never a false "no CI"."""
    names = (event, f"{event}_target") if event == "pull_request" else (event,)
    folder = root / ".github" / "workflows"
    found = []
    for path in sorted(folder.glob("*.y*ml")) if folder.is_dir() else []:
        where = path.relative_to(root).as_posix()
        try:
            events = triggers(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            events = None
        if events is None:
            found.append(f"{where} (its on: could not be read)")
            continue
        for name in (name for name in names if name in events):
            filters = events[name]
            try:
                runs = filters is None or _on_branch(filters, branch)
            except re.error:
                filters = None
                runs = True
            if runs:
                found.append(
                    where
                    if filters is not None
                    else f"{where} (its {name} filters could not be read)"
                )
                break
    return found


def runs_on(root: Path, event: str, branch: str) -> bool:
    return bool(expecting(root, event, branch))


# --- The wait -------------------------------------------------------------------------------


def settle(read: Callable[[], list[Check]], expected: bool, what: str) -> tuple[str, list[Check]]:
    """("settled" | "missing" | "running", the checks last read). Settled is two reads in a
    row listing the same checks, all done: each workflow registers on its own, so a first
    read can miss one. With nothing expected, one read: what it finds is still waited on."""
    deadline = time.monotonic() + TIMEOUT_SECONDS
    reads = FIND_READS if expected else 1
    for attempt in range(reads):
        checks = read()
        if checks:
            break
        if attempt < reads - 1:
            time.sleep(FIND_SECONDS)
    else:
        return "missing", []
    print(f"ci: waiting on {len(checks)} {what}", flush=True)
    previous: set[str] | None = None
    while True:
        keys = {check.key for check in checks}
        if checks and all(check.done for check in checks):
            if keys == previous:
                return "settled", checks
            previous = keys
        else:
            previous = None
        if time.monotonic() >= deadline:
            return "running", checks
        time.sleep(POLL_SECONDS)
        checks = read()


def _running(checks: list[Check]) -> str:
    """Every check of the last read with its state: one that ended may not have settled."""
    last = ", ".join(f"{c.name} ({c.conclusion}) {c.url}" for c in checks) or "nothing listed"
    return (
        f"running: not settled after {TIMEOUT_SECONDS // 60} min, the last read: {last}; "
        "nothing is read as passed: read it again with the same command"
    )


def _missing(found: str, where: str, expected: list[str]) -> str:
    return (
        f"missing: no {found} appeared on {where} after {FIND_READS} reads a minute apart, "
        f"though CI is expected from {', '.join(expected)}: read it again with the same command, "
        "and where it stays missing, check that workflow's paths filter"
    )


def _links(checks: list[Check]) -> str:
    return ", ".join(f"{c.name} {c.url}" for c in checks)


# --- A push ---------------------------------------------------------------------------------


def _push_runs(commit: str, ref: str) -> list[Check]:
    listed = ship.read(
        "run", "list", "--commit", commit, "--event", "push", "--branch", ref, "--limit", "50",
        "--json", "databaseId,workflowName,workflowDatabaseId,status,conclusion,url",
    )  # fmt: skip
    return [
        Check(
            key=str(run["databaseId"]),
            name=run["workflowName"],
            workflow=str(run["workflowDatabaseId"]),
            done=run["status"] == "completed",
            conclusion=run["conclusion"] or run["status"],
            url=run["url"],
        )
        for run in json.loads(listed)
    ]


def _why(run: Check) -> str:
    """A failed run, its failed jobs and steps named."""
    view = json.loads(ship.read("run", "view", run.key, "--json", "jobs"))
    where = []
    for job in view.get("jobs", []):
        if job.get("conclusion") in PASSING:
            continue
        steps = [s["name"] for s in job.get("steps", []) if s.get("conclusion") == "failure"]
        where += [f"{job['name']} > {step}" for step in steps] or [
            f"{job['name']} ({job.get('conclusion')})"
        ]
    at = f" at {'; '.join(where)}" if where else ""
    return f"{run.name} ended {run.conclusion}{at}: {run.url}"


def _newest(run: Check, ref: str) -> dict | None:
    listed = ship.read(
        "run", "list", "--workflow", run.workflow, "--branch", ref, "--event", "push",
        "--limit", "1", "--json", "headSha,url",
    )  # fmt: skip
    found = json.loads(listed)
    return found[0] if found else None


def push(root: Path, commit: str, ref: str) -> tuple[int, str]:
    """The CI a push of ``commit`` to ``ref`` started, waited on to its end."""
    short = commit[:8]
    expected = expecting(root, "push", ref)
    state, runs = settle(
        lambda: _push_runs(commit, ref), bool(expected), f"run(s) on {short} ({ref})"
    )
    if state == "missing" and not expected:
        return PASSED, f"no CI: no workflow under .github/workflows runs on a push to {ref}"
    if state == "missing":
        return MISSING, _missing("run", f"{short} ({ref})", expected)
    if state == "running":
        return RUNNING, _running(runs)
    failed, superseded = [], []
    for run in (run for run in runs if not run.passed):
        newest = _newest(run, ref) if run.conclusion == "cancelled" else None
        if newest and newest["headSha"] != commit:
            superseded.append(
                f"{ref} moved on to {newest['headSha'][:8]}, whose push cancelled "
                f"{run.name} {run.url}: read that commit's CI, {newest['url']}"
            )
        else:
            failed.append(_why(run))
    if failed:
        return FAILED, f"failed on {short} ({ref}): " + "; ".join(failed)
    if superseded:
        return SUPERSEDED, "superseded: " + "; ".join(superseded)
    return PASSED, f"passed on {short} ({ref}): {_links(runs)}"


# --- A pull request -------------------------------------------------------------------------


def _pr_checks(pr: int) -> list[Check]:
    fields = "name,bucket,link,workflow"
    listed = ship.read("pr", "checks", str(pr), "--json", fields, none=NO_CHECKS)
    return [
        Check(
            key=f"{check['workflow']}/{check['name']}",
            name=" / ".join(part for part in (check["workflow"], check["name"]) if part),
            workflow=check["workflow"],
            done=check["bucket"] != "pending",
            conclusion=check["bucket"],
            url=check["link"],
        )
        for check in json.loads(listed or "[]")
    ]


def pull_request(root: Path, pr: int) -> tuple[int, str]:
    """A pull request's checks, waited on to their end."""
    base = json.loads(ship.read("pr", "view", str(pr), "--json", "baseRefName"))["baseRefName"]
    expected = expecting(root, "pull_request", base)
    state, checks = settle(lambda: _pr_checks(pr), bool(expected), f"check(s) on PR #{pr}")
    if state == "missing" and not expected:
        return PASSED, (
            f"no PR CI: no workflow under .github/workflows runs on a pull request into {base}"
        )
    if state == "missing":
        return MISSING, _missing("check", f"PR #{pr}", expected)
    if state == "running":
        return RUNNING, _running(checks)
    failed = [check for check in checks if not check.passed]
    if failed:
        listed = "; ".join(f"{c.name} ({c.conclusion}): {c.url}" for c in failed)
        return FAILED, f"failed on PR #{pr}: {listed}"
    return PASSED, f"passed on PR #{pr}: {len(checks)} check(s)"
