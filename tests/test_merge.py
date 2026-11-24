"""``lifecycle merge``: the merge read from the pull request's state, and each branch
deleted only where nothing would be lost, in every layout a landing runs from. GitHub is a
fake gh for the pull request and its API, and a bare origin for its branch."""

import json
import os
import subprocess
from urllib.parse import unquote

import pytest
from conftest import commit, git
from lifecycle import cli, merge, ship

PR = 7
REFS = "/git/refs/heads/"
API_FAILED = "gh api repos/o/r/git/refs/heads/feat failed: HTTP 422: "


def tip(where, branch):
    """``branch``'s commit in ``where``, or "" where it has none."""
    return subprocess.run(
        ["git", "-C", str(where), "for-each-ref", "--format=%(objectname)", f"refs/heads/{branch}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def on(where):
    return git(where, "rev-parse", "--abbrev-ref", "HEAD")


def pushed(where, branch="feat"):
    """A commit on ``branch`` in ``where``, pushed to origin: the pull request's head."""
    made = commit(where, f"{branch}-work")
    git(where, "push", "-q", "origin", branch)
    return made


def fake_gh(monkeypatch, clone, head, state="OPEN", merging=None, deleting=None, fork=False):
    """GitHub's side of the pull request: ``merging`` runs as ``gh pr merge`` does, by
    default marking it merged; ``deleting`` as the API's ref deletion does, by default
    deleting the branch on the bare origin, or answering 422 where it has none."""
    pr = {
        "state": state,
        "headRefName": "feat",
        "headRefOid": head,
        "baseRefName": "next",
        "isCrossRepository": fork,
    }
    calls = []

    def merged(pr):
        pr["state"] = "MERGED"
        return ""

    def deleted(branch):
        if not tip(clone.origin, branch):
            raise ship.Refused(API_FAILED + "Reference does not exist")
        git(clone.origin, "update-ref", "-d", f"refs/heads/{branch}")
        return ""

    def gh(*args):
        calls.append(args)
        if args[:2] == ("pr", "view"):
            return json.dumps(pr)
        if args[:2] == ("pr", "merge"):
            return (merging or merged)(pr)
        if args[0] == "api" and REFS in args[1] and args[2:] == ("-X", "DELETE"):
            return (deleting or deleted)(unquote(args[1].split(REFS, 1)[1]))
        raise AssertionError(f"unexpected gh {args}")

    monkeypatch.setattr(ship, "gh", gh)
    monkeypatch.setattr(ship, "POLL_SECONDS", 0)
    return calls


def merges(calls):
    return [call for call in calls if call[:2] == ("pr", "merge")]


# --- Where it lands from --------------------------------------------------------------------


def test_a_linked_worktree_lands_with_the_integration_branch_in_the_primary_checkout(
    clone, monkeypatch
):
    """The issue's run: gh's own cleanup could not switch this worktree to next."""
    tree = clone.task("feat")
    head = pushed(tree)
    calls = fake_gh(monkeypatch, clone, head)
    assert on(clone.primary) == "next"
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert merges(calls) == [("pr", "merge", str(PR), "--squash")]
    assert lines[0] == f"PR #{PR} merged by squash into next"
    assert lines[1] == "branch feat on origin: deleted"
    assert tip(clone.origin, "feat") == ""
    assert on(tree) == "feat" and tip(tree, "feat") == head
    path = tree.resolve().as_posix()
    assert lines[-1] == (
        f"local branch feat: left with its worktree {path}, which tidy keeps after a squash "
        f"merge: both go by git worktree remove {path} and git branch -D feat, on the "
        "maintainer's word"
    )


def test_a_linked_worktree_keeps_its_branch_with_the_integration_branch_in_no_checkout(
    clone, monkeypatch
):
    """gh would have moved this worktree onto next and deleted its branch."""
    git(clone.primary, "switch", "-q", "-c", "other")
    tree = clone.task("feat")
    head = pushed(tree)
    fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert on(tree) == "feat" and tip(tree, "feat") == head
    assert on(clone.primary) == "other"
    assert tip(clone.origin, "feat") == ""
    assert "left with its worktree" in lines[-1] and "git worktree remove" in lines[-1]


def test_the_primary_checkout_switches_to_the_base_and_deletes_its_branch(clone, monkeypatch):
    git(clone.primary, "switch", "-q", "-c", "feat")
    head = pushed(clone.primary)
    fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert on(clone.primary) == "next"
    assert tip(clone.primary, "feat") == ""
    assert tip(clone.origin, "feat") == ""
    assert lines[-1] == (
        f"switched {clone.primary.as_posix()} to next, then local branch feat: deleted"
    )


def test_a_tip_past_the_prs_head_leaves_the_checkout_where_it_was(clone, monkeypatch):
    git(clone.primary, "switch", "-q", "-c", "feat")
    head = pushed(clone.primary)
    later = commit(clone.primary, "after-the-push")
    fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert on(clone.primary) == "feat" and tip(clone.primary, "feat") == later
    assert lines[-1] == (
        f"local branch feat is at {later[:8]}, not the PR's head {head[:8]}: left, checked "
        f"out in {clone.primary.resolve().as_posix()}"
    )


def test_a_refused_switch_leaves_the_branch_and_the_checkout(clone, monkeypatch, tmp_path):
    git(clone.primary, "switch", "-q", "-c", "feat")
    head = pushed(clone.primary)
    git(clone.primary, "worktree", "add", "-q", str(tmp_path / "integration"), "next")
    fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert on(clone.primary) == "feat" and tip(clone.primary, "feat") == head
    assert tip(clone.origin, "feat") == ""
    assert "could not switch to next" in lines[-1] and "left" in lines[-1]


def test_a_head_branch_no_checkout_holds_is_deleted_at_the_prs_head(clone, monkeypatch):
    """A re-run after a batch cut off past the primary checkout's switch."""
    git(clone.primary, "switch", "-q", "-c", "feat")
    head = pushed(clone.primary)
    git(clone.primary, "switch", "-q", "next")
    fake_gh(monkeypatch, clone, head, state="MERGED")
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert tip(clone.primary, "feat") == ""
    assert on(clone.primary) == "next"
    assert lines[-1] == "local branch feat: deleted"


def test_a_head_branch_no_checkout_holds_past_the_prs_head_is_kept(clone, monkeypatch):
    git(clone.primary, "switch", "-q", "-c", "feat")
    head = pushed(clone.primary)
    later = commit(clone.primary, "after-the-push")
    git(clone.primary, "switch", "-q", "next")
    fake_gh(monkeypatch, clone, head, state="MERGED")
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert tip(clone.primary, "feat") == later
    assert lines[-1] == f"local branch feat is at {later[:8]}, not the PR's head {head[:8]}: left"


def test_a_branch_another_checkout_holds_is_left_there(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)
    fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert on(tree) == "feat" and tip(tree, "feat") == head
    assert lines[-1] == f"local branch feat: left, checked out in {tree.resolve().as_posix()}"


def test_a_local_delete_git_refuses_is_named(clone, monkeypatch):
    """A ref lock another git process holds refuses the delete."""
    git(clone.primary, "switch", "-q", "-c", "feat")
    head = pushed(clone.primary)
    git(clone.primary, "switch", "-q", "next")
    (clone.primary / ".git" / "refs" / "heads" / "feat.lock").write_text("", encoding="utf-8")
    fake_gh(monkeypatch, clone, head, state="MERGED")
    code, lines = merge.merge(clone.primary, PR)
    assert code == merge.MERGED
    assert tip(clone.primary, "feat") == head
    assert lines[-1].startswith("local branch feat: its deletion failed: ")


def test_a_git_call_with_no_answer_reads_as_a_failure(monkeypatch, tmp_path):
    def hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(merge.subprocess, "run", hang)
    ran = merge._git(tmp_path, "ls-remote", "origin", timeout=60)
    assert ran.returncode != 0
    assert ran.stderr == "fatal: git ls-remote gave no answer in 60 s"


# --- The branch on GitHub -------------------------------------------------------------------


def test_the_delete_runs_no_pre_push_hook(clone, monkeypatch):
    """A push would run the repository's gate: the delete goes through GitHub's API."""
    tree = clone.task("feat")
    head = pushed(tree)
    hooks = clone.tmp / "hooks"
    hooks.mkdir()
    (hooks / "pre-push").write_text("#!/bin/sh\necho 'the gate' >&2\nexit 1\n", newline="\n")
    os.chmod(hooks / "pre-push", 0o755)
    git(clone.primary, "config", "core.hooksPath", str(hooks))
    calls = fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert lines[1] == "branch feat on origin: deleted"
    assert tip(clone.origin, "feat") == ""
    assert ("api", "repos/{owner}/{repo}/git/refs/heads/feat", "-X", "DELETE") in calls


def test_a_branch_on_origin_at_another_commit_stays(clone, monkeypatch, tmp_path):
    tree = clone.task("feat")
    head = pushed(tree)
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", "-b", "feat", str(clone.origin), str(other))
    later = commit(other, "pushed-after-the-merge")
    git(other, "push", "-q", "origin", "feat")
    calls = fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert tip(clone.origin, "feat") == later
    assert lines[1] == (
        f"branch feat on origin is at {later[:8]}, not the PR's head {head[:8]}: left for "
        "the maintainer"
    )
    assert not [call for call in calls if call[:1] == ("api",)]


def test_a_refused_delete_carries_githubs_reason(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)

    def protect(branch):
        raise ship.Refused(API_FAILED + "Cannot delete this protected branch")

    fake_gh(monkeypatch, clone, head, deleting=protect)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert tip(clone.origin, "feat") == head
    assert lines[1] == (
        "branch feat on origin: GitHub refused its deletion, so it is left: gh api "
        "repos/o/r/git/refs/heads/feat failed: HTTP 422: Cannot delete this protected branch"
    )


def test_a_delete_with_no_answer_says_the_branch_may_be_left(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)

    def silent(branch):
        raise ship.ReleaseError("gh api repos/o/r/git/refs/heads/feat gave no answer in 60 s")

    fake_gh(monkeypatch, clone, head, deleting=silent)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert tip(clone.origin, "feat") == head
    assert lines[1] == (
        "branch feat on origin: its deletion failed, so it may be left: gh api "
        f"repos/o/r/git/refs/heads/feat gave no answer in 60 s; lifecycle merge {PR} reads it "
        "again"
    )


def test_a_failed_delete_of_a_branch_gone_since_reads_as_gone(clone, monkeypatch):
    """The repository deleted the head branch on merge, between the read and the delete."""
    tree = clone.task("feat")
    head = pushed(tree)

    def raced(branch):
        git(clone.origin, "update-ref", "-d", f"refs/heads/{branch}")
        raise ship.Refused(API_FAILED + "Reference does not exist")

    fake_gh(monkeypatch, clone, head, deleting=raced)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert lines[1].startswith("branch feat on origin: gone, though its delete reported an error")


def test_a_branch_already_gone_sends_no_delete(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)
    git(tree, "push", "-q", "origin", "--delete", "feat")
    calls = fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert lines[1] == "branch feat on origin: gone already, no delete sent"
    assert not [call for call in calls if call[:1] == ("api",)]


def test_an_unreachable_origin_leaves_the_branch_and_names_the_stale_fetch(
    clone, monkeypatch, tmp_path
):
    tree = clone.task("feat")
    head = pushed(tree)
    git(tree, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    fake_gh(monkeypatch, clone, head)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert tip(clone.origin, "feat") == head
    assert lines[1].startswith("branch feat on origin could not be read, so it is left (")
    assert lines[1].endswith(f"lifecycle merge {PR} reads it again")
    assert lines[2].startswith("git fetch --prune origin failed (")
    assert lines[2].endswith("until a fetch succeeds, tidy reads origin as last fetched")


def test_a_forks_branch_is_left_on_the_fork(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)
    fake_gh(monkeypatch, clone, head, fork=True)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert tip(clone.origin, "feat") == head
    assert lines[1] == "branch feat is on the fork the PR came from: left there"


# --- The merge's outcome --------------------------------------------------------------------


def test_a_refused_merge_deletes_nothing_and_says_why(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)

    def refuse(pr):
        raise ship.Refused("gh pr merge failed: the base branch policy prohibits the merge")

    fake_gh(monkeypatch, clone, head, merging=refuse)
    code, lines = merge.merge(tree, PR)
    assert code == merge.NOT_MERGED
    assert lines == [
        f"PR #{PR} not merged, open: gh pr merge failed: the base branch policy prohibits "
        "the merge; nothing deleted"
    ]
    assert tip(clone.origin, "feat") == head and tip(tree, "feat") == head


def test_a_failed_call_on_a_merged_pr_counts_as_merged(clone, monkeypatch):
    """gh's exit 1 after a merge it made: the state, not the exit code, decides."""
    tree = clone.task("feat")
    head = pushed(tree)

    def merge_then_fail(pr):
        pr["state"] = "MERGED"
        raise ship.ReleaseError("gh pr merge failed: fatal: 'next' is already used by worktree")

    fake_gh(monkeypatch, clone, head, merging=merge_then_fail)
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert lines[0].startswith(f"PR #{PR} merged by squash into next, though the call reported")
    assert tip(clone.origin, "feat") == ""


def test_a_pr_merged_already_is_not_merged_again(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)
    calls = fake_gh(monkeypatch, clone, head, state="MERGED")
    code, lines = merge.merge(tree, PR)
    assert code == merge.MERGED
    assert merges(calls) == []
    assert lines[0] == f"PR #{PR} was merged already into next"
    assert tip(clone.origin, "feat") == ""


def test_a_closed_pr_is_not_merged(clone, monkeypatch):
    tree = clone.task("feat")
    head = pushed(tree)
    calls = fake_gh(monkeypatch, clone, head, state="CLOSED")
    assert merge.merge(tree, PR) == (
        merge.NOT_MERGED,
        [f"PR #{PR} is closed, not merged: nothing deleted"],
    )
    assert merges(calls) == [] and tip(clone.origin, "feat") == head


@pytest.mark.parametrize("readable", [0, 1])
def test_an_unread_state_deletes_nothing_and_is_never_refused(clone, monkeypatch, capsys, readable):
    """Unreadable from the start, or only after the merge was asked for."""
    tree = clone.task("feat")
    head = pushed(tree)
    calls = fake_gh(monkeypatch, clone, head)
    answer = ship.gh
    reads = []

    def gh(*args):
        if args[:2] == ("pr", "view"):
            reads.append(args)
            if len(reads) > readable:
                raise ship.ReleaseError("gh pr view gave no answer in 60 s")
        return answer(*args)

    monkeypatch.setattr(ship, "gh", gh)
    monkeypatch.chdir(tree)
    assert cli.main(["merge", str(PR)]) == 1
    err = capsys.readouterr().err.splitlines()
    assert len(err) == 1 and err[0].startswith(f"lifecycle: PR #{PR}'s state could not be read ")
    if readable:
        assert "after the merge was asked for" in err[0]
        assert err[0].endswith(
            f"nothing deleted; lifecycle merge {PR} reads it again, and merges it only if it "
            "still reads open"
        )
    else:
        assert err[0].endswith(
            f"nothing merged or deleted; lifecycle merge {PR} reads it again, and merges it "
            "if it reads open"
        )
    assert len(merges(calls)) == readable
    assert tip(clone.origin, "feat") == head and tip(tree, "feat") == head


# --- The command ----------------------------------------------------------------------------


def test_the_command_prints_each_line_and_exits_by_the_outcome(clone, monkeypatch, capsys):
    tree = clone.task("feat")
    head = pushed(tree)
    fake_gh(monkeypatch, clone, head)
    monkeypatch.chdir(tree)
    assert cli.main(["merge", str(PR)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == f"PR #{PR} merged by squash into next"
    assert out[1] == "branch feat on origin: deleted"
    assert "left with its worktree" in out[-1]
