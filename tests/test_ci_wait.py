import json

import pytest
from lifecycle import ci, cli, ship
from test_ship import committed

URL = "https://github.com/o/r/actions/runs/{}"
COMMIT = "abc12345" + "0" * 32
NEWER = "def67890" + "0" * 32


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    for module, name in ((ci, "POLL_SECONDS"), (ci, "FIND_SECONDS"), (ship, "POLL_SECONDS")):
        monkeypatch.setattr(module, name, 0)


def workflows(root, text="on:\n  push:\n    branches: [main]\n  pull_request:\n"):
    folder = root / ".github" / "workflows"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "ci.yml").write_text(text, encoding="utf-8")
    return root


def run(number=1, conclusion="success", status="completed"):
    return {
        "databaseId": number,
        "workflowName": f"ci{number}",
        "workflowDatabaseId": 10 + number,
        "status": status,
        "conclusion": conclusion if status == "completed" else "",
        "url": URL.format(number),
    }


def check(name="test", bucket="pass", workflow="ci"):
    return {"name": name, "bucket": bucket, "link": f"https://x/{name}", "workflow": workflow}


def fake_gh(monkeypatch, pushes=((),), jobs=None, newest=None, checks=((),), down=0):
    """``ship.gh`` answering each push's ``run list`` with the next of ``pushes``, the
    newest-run ``run list`` with ``newest``, ``run view`` with ``jobs`` by run id, and each ``pr
    checks`` with the next of ``checks`` (``None`` being gh's "no checks reported"); its first
    ``down`` calls fail."""
    calls, pushes, checks, failing = [], list(pushes), list(checks), [down]

    def next_of(queue):
        return queue.pop(0) if len(queue) > 1 else queue[0]

    def gh(*args):
        calls.append(args)
        if failing[0]:
            failing[0] -= 1
            raise ship.ReleaseError(f"gh {' '.join(args[:2])} failed: down")
        if args[:2] == ("run", "list"):
            if "--commit" in args:
                return json.dumps(list(next_of(pushes)))
            return json.dumps([newest] if newest else [])
        if args[:2] == ("run", "view"):
            return json.dumps({"jobs": (jobs or {}).get(args[2], [])})
        if args[:2] == ("pr", "view"):
            return json.dumps({"baseRefName": "main"})
        answer = next_of(checks)
        if answer is None:
            raise ship.ReleaseError("gh pr checks failed: no checks reported on the 'x' branch")
        return json.dumps(list(answer))

    monkeypatch.setattr(ship, "gh", gh)
    return calls


def commit_reads(calls):
    return sum(1 for call in calls if call[:2] == ("run", "list") and "--commit" in call)


# --- A push ---------------------------------------------------------------------------------


def test_a_push_reads_the_runs_that_push_started(monkeypatch, tmp_path):
    calls = fake_gh(monkeypatch, pushes=[[run()]])
    assert ci.push(workflows(tmp_path), COMMIT, "main")[0] == ci.PASSED
    assert calls[0][:9] == (
        "run", "list", "--commit", COMMIT, "--event", "push", "--branch", "main", "--limit",
    )  # fmt: skip


def test_a_failed_run_names_its_failed_job_and_step(monkeypatch, tmp_path):
    jobs = {
        "1": [
            {"name": "lint", "conclusion": "success", "steps": []},
            {
                "name": "test (ubuntu-latest, 3.11)",
                "conclusion": "failure",
                "steps": [
                    {"name": "Set up job", "conclusion": "success"},
                    {"name": "Run pytest", "conclusion": "failure"},
                ],
            },
        ]
    }
    fake_gh(monkeypatch, pushes=[[run(1, "failure"), run(2)]], jobs=jobs)
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.FAILED
    assert line == (
        f"failed on abc12345 (main): ci1 ended failure at test (ubuntu-latest, 3.11) > "
        f"Run pytest: {URL.format(1)}"
    )


def test_a_job_that_did_not_fail_is_named_with_how_it_ended(monkeypatch, tmp_path):
    jobs = {
        "1": [
            {"name": "test (3.11)", "conclusion": "failure", "steps": [
                {"name": "Run pytest", "conclusion": "failure"},
            ]},
            {"name": "test (3.13)", "conclusion": "cancelled", "steps": [
                {"name": "Run pytest", "conclusion": "cancelled"},
            ]},
        ]
    }  # fmt: skip
    fake_gh(monkeypatch, pushes=[[run(1, "failure")]], jobs=jobs)
    line = ci.push(workflows(tmp_path), COMMIT, "main")[1]
    assert "at test (3.11) > Run pytest; test (3.13) (cancelled):" in line


@pytest.mark.parametrize("conclusion", ["startup_failure", "timed_out", "action_required"])
def test_every_conclusion_but_success_skipped_and_neutral_is_a_failure(
    monkeypatch, tmp_path, conclusion
):
    fake_gh(monkeypatch, pushes=[[run(1, conclusion)]])
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.FAILED and f"ci1 ended {conclusion}: {URL.format(1)}" in line


def test_runs_that_succeeded_were_skipped_or_neutral_passed(monkeypatch, tmp_path):
    fake_gh(monkeypatch, pushes=[[run(1), run(2, "skipped"), run(3, "neutral")]])
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.PASSED and line.startswith("passed on abc12345 (main): ci1 ")


def test_a_run_cancelled_on_a_branch_still_at_the_commit_failed(monkeypatch, tmp_path):
    fake_gh(monkeypatch, pushes=[[run(1, "cancelled")]], newest={"headSha": COMMIT, "url": "u"})
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.FAILED and "ci1 ended cancelled" in line


def test_a_run_a_later_push_cancelled_was_superseded(monkeypatch, tmp_path):
    newest = {"headSha": NEWER, "url": URL.format(9)}
    calls = fake_gh(monkeypatch, pushes=[[run(1, "cancelled")]], newest=newest)
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.SUPERSEDED
    assert line == (
        f"superseded: main moved on to def67890, whose push cancelled ci1 {URL.format(1)}: "
        f"read that commit's CI, {URL.format(9)}"
    )
    assert calls[-1][2:6] == ("--workflow", "11", "--branch", "main")


def test_a_superseded_run_beside_a_failed_one_is_a_failure(monkeypatch, tmp_path):
    newest = {"headSha": NEWER, "url": URL.format(9)}
    fake_gh(monkeypatch, pushes=[[run(1, "cancelled"), run(2, "failure")]], newest=newest)
    assert ci.push(workflows(tmp_path), COMMIT, "main")[0] == ci.FAILED


def test_where_no_workflow_runs_on_the_push_one_read_says_no_ci(monkeypatch, tmp_path):
    calls = fake_gh(monkeypatch)
    code, line = ci.push(workflows(tmp_path), COMMIT, "next")
    assert (code, line) == (
        ci.PASSED,
        "no CI: no workflow under .github/workflows runs on a push to next",
    )
    assert commit_reads(calls) == 1


def test_a_run_found_where_none_was_expected_is_still_read(monkeypatch, tmp_path):
    fake_gh(monkeypatch, pushes=[[run(1, "failure")]])
    assert ci.push(workflows(tmp_path), COMMIT, "next")[0] == ci.FAILED


def test_an_expected_run_that_never_appears_is_missing(monkeypatch, tmp_path):
    calls = fake_gh(monkeypatch)
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.MISSING
    assert line.startswith(
        "missing: no run appeared on abc12345 (main) after 5 reads a minute apart, though CI "
        "is expected from .github/workflows/ci.yml: read it again with the same command"
    )
    assert commit_reads(calls) == ci.FIND_READS


def test_a_missing_run_names_a_workflow_counted_only_as_unread(monkeypatch, tmp_path):
    fake_gh(monkeypatch)
    code, line = ci.push(workflows(tmp_path, "on: {push: {}}\n"), COMMIT, "main")
    assert code == ci.MISSING
    assert "expected from .github/workflows/ci.yml (its on: could not be read)" in line


def test_runs_still_going_at_the_timeout_are_running(monkeypatch, tmp_path):
    fake_gh(monkeypatch, pushes=[[run(1), run(2, status="in_progress")]])
    monkeypatch.setattr(ci, "TIMEOUT_SECONDS", 0)
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert (code, line) == (
        ci.RUNNING,
        f"running: not settled after 0 min, the last read: ci1 (success) {URL.format(1)}, "
        f"ci2 (in_progress) {URL.format(2)}; nothing is read as passed: read it again with "
        "the same command",
    )


def test_runs_that_ended_but_had_not_settled_at_the_timeout_are_named(monkeypatch, tmp_path):
    fake_gh(monkeypatch, pushes=[[run(1)]])
    monkeypatch.setattr(ci, "TIMEOUT_SECONDS", 0)
    code, line = ci.push(workflows(tmp_path), COMMIT, "main")
    assert code == ci.RUNNING and f"the last read: ci1 (success) {URL.format(1)};" in line


def test_the_wait_says_what_it_waits_on_in_words_no_outcome_uses(monkeypatch, tmp_path, capsys):
    fake_gh(monkeypatch, pushes=[[run()]])
    ci.push(workflows(tmp_path), COMMIT, "main")
    assert capsys.readouterr().out == "ci: waiting on 1 run(s) on abc12345 (main)\n"


def test_a_run_that_appears_on_the_second_read_is_waited_for(monkeypatch, tmp_path):
    late = [[run(1)], [run(1), run(2, status="queued")], [run(1), run(2, "failure")]]
    fake_gh(monkeypatch, pushes=late)
    assert ci.push(workflows(tmp_path), COMMIT, "main")[0] == ci.FAILED


def test_runs_settle_on_two_equal_reads(monkeypatch, tmp_path):
    calls = fake_gh(monkeypatch, pushes=[[run(1, status="in_progress")], [run(1)]])
    assert ci.push(workflows(tmp_path), COMMIT, "main")[0] == ci.PASSED
    assert commit_reads(calls) == 3


def test_a_passing_failure_of_a_read_is_retried(monkeypatch, tmp_path):
    fake_gh(monkeypatch, pushes=[[run()]], down=1)
    assert ci.push(workflows(tmp_path), COMMIT, "main")[0] == ci.PASSED


# --- A pull request -------------------------------------------------------------------------


@pytest.mark.parametrize("bucket", ["fail", "cancel"])
def test_a_failed_or_cancelled_check_fails_the_pull_request(monkeypatch, tmp_path, bucket):
    fake_gh(monkeypatch, checks=[[check("lint"), check("test", bucket)]])
    code, line = ci.pull_request(workflows(tmp_path), 7)
    assert (code, line) == (ci.FAILED, f"failed on PR #7: ci / test ({bucket}): https://x/test")


def test_passed_and_skipped_checks_pass_the_pull_request(monkeypatch, tmp_path):
    fake_gh(monkeypatch, checks=[[check("lint"), check("test", "skipping")]])
    assert ci.pull_request(workflows(tmp_path), 7) == (ci.PASSED, "passed on PR #7: 2 check(s)")


def test_no_checks_where_a_workflow_runs_on_pull_requests_is_missing(monkeypatch, tmp_path):
    calls = fake_gh(monkeypatch, checks=[None])
    code, line = ci.pull_request(workflows(tmp_path), 7)
    assert code == ci.MISSING and "no check appeared on PR #7 after 5 reads" in line
    assert sum(1 for call in calls if call[:2] == ("pr", "checks")) == ci.FIND_READS


def test_no_checks_where_no_workflow_runs_on_pull_requests_is_no_pr_ci(monkeypatch, tmp_path):
    fake_gh(monkeypatch, checks=[None])
    root = workflows(tmp_path, "on:\n  push:\n")
    assert ci.pull_request(root, 7) == (
        ci.PASSED,
        "no PR CI: no workflow under .github/workflows runs on a pull request into main",
    )


def test_a_check_that_appears_on_the_second_read_is_waited_for(monkeypatch, tmp_path):
    lint = check("lint")
    late = [[lint], [lint, check("test", "pending")], [lint, check("test", "fail")]]
    fake_gh(monkeypatch, checks=late)
    assert ci.pull_request(workflows(tmp_path), 7)[0] == ci.FAILED


def test_no_outcome_takes_the_code_argparse_exits_with_on_a_usage_error():
    assert 2 not in {ci.PASSED, ci.FAILED, ci.MISSING, ci.RUNNING, ci.SUPERSEDED}


# --- Whether a workflow runs ----------------------------------------------------------------

PUSH_TO = "on:\n  push:\n    branches: {}\n"
ALPHA = PUSH_TO.format("['releases/**', '!releases/**-alpha']")


@pytest.mark.parametrize(
    ("text", "event", "branch", "runs"),
    [
        ("on: push\n", "push", "next", True),
        ("on: [push, pull_request]\n", "pull_request", "main", True),
        ("on: [pull_request]\n", "push", "main", False),
        ("on:\n- push\n", "push", "main", True),
        (PUSH_TO.format("[main, 'releases/**']"), "push", "main", True),
        (PUSH_TO.format("[main, 'releases/**']"), "push", "next", False),
        (PUSH_TO.format("[main, 'releases/**']"), "push", "releases/v1/x", True),
        ("on:\n  push:\n    branches:\n      - main\n", "push", "next", False),
        ("on:\n  push:\n    branches:\n    - main\n", "push", "main", True),
        ("on:\n  push:\n    branches:\n    - main\n", "push", "next", False),
        (PUSH_TO.format("['feature/*']"), "push", "feature/a", True),
        (PUSH_TO.format("['feature/*']"), "push", "feature/a/b", False),
        (ALPHA, "push", "releases/1-alpha", False),
        (ALPHA, "push", "releases/1", True),
        ("on:\n  push:\n    branches-ignore: ['dependabot/**']\n", "push", "dependabot/x", False),
        ("on:\n  push:\n    branches-ignore: ['dependabot/**']\n", "push", "next", True),
        ("on:\n  push:\n    tags: ['v*']\n", "push", "main", False),
        ("on:\n  push:\n    tags-ignore:\n      - 'v*'\n", "push", "main", False),
        ("on:\n  push:\n    paths: ['src/**']\n", "push", "main", True),
        ("on:\n  pull_request_target:\n", "pull_request", "main", True),
        ("on:\n  pull_request:\n    branches: [main]\n", "pull_request", "next", False),
        ("on:\n  workflow_call:\n  workflow_dispatch:\n", "push", "main", False),
        ('"on":\n  push:\n', "push", "main", True),
        ("on:  # when\n  push:  # every\n    branches: [main] # only\n", "push", "next", False),
        ("on:\n  push:\n    types: [x]\n  pull_request:\n", "push", "next", True),
        ("on: {push: {branches: [main]}}\n", "push", "next", True),
        ("on:\n  push: {branches: [main]}\n", "push", "next", True),
        ("name: no trigger\n", "push", "next", True),
        ("on:\n  push:\n    branches: [\n      main, next]\n", "push", "feature", True),
        ("on:\n  push:\n    branches:\n      [main, next]\n", "push", "feature", True),
        ("on:\n  [push, pull_request]\n", "push", "main", True),
        ("on:\n  - push\n  - pull_request\n", "push", "main", True),
        ("on:\n  - pull_request\n", "push", "main", False),
        ("on:\n  push:\n    branches: *refs\n", "push", "feature", True),
        ("on:\n  push:\n    branches:\n      - *main\n", "push", "feature", True),
        ("on:\n  push:\n    branches: ['[z-a]']\n", "push", "feature", True),
        ("on:\n  push:\n    branches: ['a[b']\n", "push", "a[b", True),
        ("on:\n  push:\n    branches: ['a[b']\n", "push", "ab", False),
    ],
)
def test_whether_a_workflow_runs_on_an_event_for_a_branch(tmp_path, text, event, branch, runs):
    assert ci.runs_on(workflows(tmp_path, text), event, branch) is runs


def test_a_repository_without_workflows_runs_no_ci(tmp_path):
    assert ci.runs_on(tmp_path, "push", "main") is False


# --- The command ----------------------------------------------------------------------------


def waited_by(monkeypatch):
    waited = []

    def push(root, commit, ref):
        waited.append((commit, ref))
        return ci.SUPERSEDED, "superseded: moved"

    monkeypatch.setattr(ci, "push", push)
    monkeypatch.setattr(ci, "pull_request", lambda root, pr: (ci.PASSED, f"passed on PR #{pr}"))
    return waited


def test_ci_reads_the_full_commit_on_the_integration_branch(monkeypatch, capsys, repo):
    head = committed(repo, monkeypatch, '[branches]\nintegration = "trunk"\n')
    waited = waited_by(monkeypatch)
    monkeypatch.chdir(repo.root)
    assert cli.main(["ci", head[:8]]) == ci.SUPERSEDED
    assert cli.main(["ci", head, "--ref", "hotfix/x"]) == ci.SUPERSEDED
    assert waited == [(head, "trunk"), (head, "hotfix/x")]
    assert capsys.readouterr().err == "ci: superseded: moved\nci: superseded: moved\n"
    assert cli.main(["ci", "--pr", "7"]) == ci.PASSED
    assert capsys.readouterr().out == "ci: passed on PR #7\n"


def test_ci_names_a_commit_that_is_not_one(monkeypatch, capsys, repo):
    committed(repo, monkeypatch, "")
    monkeypatch.chdir(repo.root)
    assert cli.main(["ci", "nope"]) == 1
    assert "nope is not a commit" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv", [["ci"], ["ci", "HEAD", "--pr", "7"], ["ci", "--pr", "7", "--ref", "x"]]
)
def test_ci_takes_a_commit_or_a_pull_request(argv):
    with pytest.raises(SystemExit) as raised:
        cli.main(argv)
    assert raised.value.code == 2


def test_a_read_that_keeps_failing_is_unread_not_red(monkeypatch, capsys, repo):
    head = committed(repo, monkeypatch, "")
    workflows(repo.root)
    fake_gh(monkeypatch, down=99)
    monkeypatch.chdir(repo.root)
    assert cli.main(["ci", head]) == 1
    assert capsys.readouterr().err.startswith("lifecycle: gh run list failed: down")
