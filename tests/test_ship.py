import json
import subprocess

import pytest
from lifecycle import METHOD, cli, ship

URL = "https://github.com/o/r/actions/runs/{}"


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(ship, "POLL_SECONDS", 0)


def fake_gh(monkeypatch, printed="", listings=([1],), views=(), fail=()):
    """``ship.gh`` answering ``workflow run`` with ``printed`` (or failing with it, where it
    is an exception), each ``run list`` with the next of ``listings`` (run ids), each ``run
    view`` with the next of ``views``, and failing the calls whose first two words are in
    ``fail``, the ones a ``None`` in ``fail`` stands for failing only once."""
    calls, listings, views, fail = [], list(listings), list(views), list(fail)

    def gh(*args):
        calls.append(args)
        if args[:2] in fail:
            raise ship.ReleaseError(f"gh {' '.join(args[:2])} failed: down")
        if fail and fail[0] is None:
            fail.pop(0)
            raise ship.ReleaseError("gh: a passing failure")
        if args[:2] == ("workflow", "run"):
            if isinstance(printed, Exception):
                raise printed
            return printed
        if args[:2] == ("run", "list"):
            ids = listings.pop(0) if len(listings) > 1 else listings[0]
            return json.dumps([{"databaseId": run} for run in ids])
        return json.dumps(views.pop(0) if len(views) > 1 else views[0])

    monkeypatch.setattr(ship, "gh", gh)
    return calls


def run(conclusion="success", failed=None, status="completed"):
    steps = [{"name": "Set up job", "conclusion": "success"}]
    if failed:
        steps.append({"name": failed, "conclusion": "failure"})
    jobs = [{"name": "refuse", "steps": steps}]
    return {"status": status, "conclusion": conclusion, "url": URL.format(7), "jobs": jobs}


def test_a_release_dispatches_on_the_ref_and_the_reviewed_commit(monkeypatch):
    calls = fake_gh(monkeypatch, printed=URL.format(7) + "\n", views=[run()])
    assert ship.release("release.yml", "main", "abc12345ff")[0] == ship.SHIPPED
    assert ("workflow", "run", "release.yml", "--ref", "main", "-f", "commit=abc12345ff") in calls
    assert ("run", "view", "7", "--json", "status,conclusion,url,jobs") in calls


def test_the_run_is_the_url_gh_printed():
    assert ship.find(URL.format(42) + "\n", "release.yml", "main", {1}) == "42"


def test_without_a_printed_url_the_run_is_the_new_one(monkeypatch):
    fake_gh(monkeypatch, listings=[[1], [1, 2]])
    assert ship.find("", "release.yml", "main", {1}) == "2"


def test_two_new_runs_at_once_are_not_guessed_between(monkeypatch):
    fake_gh(monkeypatch, listings=[[1, 2, 3]])
    with pytest.raises(ship.ReleaseError, match="2 runs"):
        ship.find("", "release.yml", "main", {1})


def test_a_run_that_never_appears_is_said(monkeypatch):
    fake_gh(monkeypatch, listings=[[1]])
    with pytest.raises(ship.ReleaseError, match="never appeared"):
        ship.find("", "release.yml", "main", {1})


def test_watch_waits_for_the_run_to_complete(monkeypatch):
    fake_gh(monkeypatch, views=[run(status="queued"), run(status="in_progress"), run()])
    assert ship.watch("7")["conclusion"] == "success"


def test_a_passing_failure_of_a_read_is_retried(monkeypatch):
    fake_gh(monkeypatch, views=[run()], fail=[None])
    assert ship.watch("7")["conclusion"] == "success"


def test_a_successful_run_shipped():
    assert ship.outcome(run(), "main", "abc12345ff")[0] == ship.SHIPPED


def test_a_moved_branch_sends_the_release_back_to_review():
    code, line = ship.outcome(run("failure", ship.MOVED), "main", "abc12345ff")
    assert code == ship.MOVED_SINCE_REVIEW and "main moved since the review" in line


def test_no_outcome_takes_the_code_argparse_exits_with_on_a_usage_error():
    assert 2 not in {ship.SHIPPED, ship.FAILED, ship.MOVED_SINCE_REVIEW, ship.IN_FLIGHT}


def test_a_tagged_version_is_refused():
    code, line = ship.outcome(run("failure", ship.TAGGED), "main", "abc12345ff")
    assert code == ship.FAILED and "tagged already, or its tags could not be read" in line


def test_a_wrong_ref_is_refused():
    code, line = ship.outcome(run("failure", ship.WRONG_REF), "feat/x", "abc12345ff")
    assert code == ship.FAILED and "feat/x is not the integration branch" in line


def test_any_other_failure_names_its_job_and_step():
    code, line = ship.outcome(run("failure", "Deploy"), "main", "abc12345ff")
    assert code == ship.FAILED and "failed at refuse > Deploy" in line


def test_a_cancelled_run_is_not_a_release():
    code, line = ship.outcome(run("cancelled"), "main", "abc12345ff")
    assert code == ship.FAILED and "ended cancelled" in line


def test_a_run_still_going_at_the_timeout_is_in_flight(monkeypatch):
    fake_gh(monkeypatch, printed=URL.format(7), views=[run(status="in_progress")])
    monkeypatch.setattr(ship, "TIMEOUT_SECONDS", 0)
    code, line = ship.release("release.yml", "main", "abc12345ff")
    assert code == ship.IN_FLIGHT and "still in_progress" in line and "dispatch nothing" in line


def test_a_run_lost_after_the_dispatch_is_in_flight(monkeypatch):
    fake_gh(monkeypatch, printed=URL.format(7), fail=[("run", "view")])
    code, line = ship.release("release.yml", "main", "abc12345ff")
    assert code == ship.IN_FLIGHT and "may still ship" in line


def test_a_run_never_found_after_the_dispatch_is_in_flight(monkeypatch):
    fake_gh(monkeypatch, listings=[[1]])
    assert ship.release("release.yml", "main", "abc12345ff")[0] == ship.IN_FLIGHT


def test_a_dispatch_github_refused_started_nothing(monkeypatch):
    fake_gh(monkeypatch, printed=ship.Refused("gh workflow run failed: HTTP 422"))
    with pytest.raises(ship.Refused, match="HTTP 422"):
        ship.release("release.yml", "main", "abc12345ff")


def test_a_dispatch_that_failed_any_other_way_is_looked_for(monkeypatch):
    lost = ship.ReleaseError("gh workflow run failed: HTTP 502")
    fake_gh(monkeypatch, printed=lost, listings=[[1], [1, 2]], views=[run()])
    assert ship.release("release.yml", "main", "abc12345ff")[0] == ship.SHIPPED


@pytest.mark.parametrize(
    ("stderr", "refused"), [("HTTP 422: Unexpected inputs", True), ("HTTP 502: Bad Gateway", False)]
)
def test_only_a_4xx_is_github_refusing(monkeypatch, stderr, refused):
    failed = subprocess.CompletedProcess([], 1, stdout="", stderr=stderr)
    monkeypatch.setattr(ship.subprocess, "run", lambda *a, **k: failed)
    with pytest.raises(ship.ReleaseError) as raised:
        ship.gh("workflow", "run")
    assert isinstance(raised.value, ship.Refused) is refused


def test_a_gh_that_never_answers_is_no_refusal(monkeypatch):
    def hung(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(ship.subprocess, "run", hung)
    with pytest.raises(ship.ReleaseError, match="no answer") as raised:
        ship.gh("workflow", "run")
    assert not isinstance(raised.value, ship.Refused)


def test_a_dispatch_with_no_answer_is_looked_for(monkeypatch):
    silent = ship.ReleaseError(f"gh workflow run gave no answer in {ship.CALL_SECONDS} s")
    fake_gh(monkeypatch, printed=silent, listings=[[1], [1, 2]], views=[run()])
    assert ship.release("release.yml", "main", "abc12345ff")[0] == ship.SHIPPED


def test_the_recipe_names_each_refusal_step_as_the_tool_reads_it():
    recipe = (METHOD / "project_kickstart.md").read_text(encoding="utf-8")
    assert all(f"- name: {step}\n" in recipe for step in ship.REFUSALS)


def committed(config, monkeypatch, settings):
    (config.root / ".lifecycle.toml").write_text(settings, encoding="utf-8")
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "t")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t@t")
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "x"]):
        subprocess.run(["git", "-C", str(config.root), *args], check=True)
    head = ["git", "-C", str(config.root), "rev-parse", "HEAD"]
    return subprocess.run(head, capture_output=True, text=True, check=True).stdout.strip()


def shipped_by(monkeypatch):
    shipped = []

    def released(workflow, ref, commit):
        shipped.append((workflow, ref, commit))
        return ship.MOVED_SINCE_REVIEW, "refused: moved"

    monkeypatch.setattr(ship, "release", released)
    return shipped


def test_release_needs_the_workflow_named(monkeypatch, capsys, repo):
    monkeypatch.chdir(repo.root)
    assert cli.main(["release", "HEAD"]) == 1
    assert "names no [release] workflow" in capsys.readouterr().err


def test_release_ships_the_full_commit_from_the_integration_branch(monkeypatch, capsys, repo):
    settings = '[branches]\nintegration = "trunk"\n\n[release]\nworkflow = "release.yml"\n'
    head = committed(repo, monkeypatch, settings)
    shipped = shipped_by(monkeypatch)
    monkeypatch.chdir(repo.root)
    assert cli.main(["release", head[:8]]) == ship.MOVED_SINCE_REVIEW
    assert shipped == [("release.yml", "trunk", head)]
    assert cli.main(["release", "nope"]) == 1
    assert "nope is not a commit" in capsys.readouterr().err


def test_release_ships_a_hotfix_from_its_branch(monkeypatch, repo):
    head = committed(repo, monkeypatch, '[release]\nworkflow = "release.yml"\n')
    shipped = shipped_by(monkeypatch)
    monkeypatch.chdir(repo.root)
    cli.main(["release", head, "--ref", "hotfix/x"])
    assert shipped == [("release.yml", "hotfix/x", head)]
