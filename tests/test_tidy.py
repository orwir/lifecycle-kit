"""`lifecycle tidy` is what a task that lands from a linked worktree leaves in order: the
primary checkout's integration branch fast-forwarded to origin's, and, on the maintainer's
word, each linked worktree whose own work landed removed with its branch, never one that
holds work, a fresh session's or one in use."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import commit, git
from lifecycle import cli, tidy

KIT = Path(__file__).resolve().parents[1]


def branches(cwd):
    return git(cwd, "branch", "--format=%(refname:short)").splitlines()


def listed(cwd):
    return [Path(tree.path) for tree in tidy.worktrees(Path(cwd))]


def head(cwd):
    return git(cwd, "rev-parse", "HEAD")


def test_a_push_from_a_worktree_fast_forwards_the_primary_checkout(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    report = tidy.tidy(tree, "next")
    assert head(clone.primary) == git(clone.primary, "rev-parse", "origin/next")
    forwarded = r"^primary checkout .*: fast-forwarded next by 1 commit\(s\) to "
    assert re.search(forwarded, report.lines[0])
    assert not report.refused
    assert tidy.tidy(tree, "next").lines[0].endswith("next level with origin/next")


def test_a_merge_on_github_is_followed_once_fetched(clone):
    """A PR merge moves origin's branch on GitHub alone: nothing here has it until a fetch,
    so the complete skill fetches before it runs tidy."""
    tree = clone.task("task-1")
    before = head(clone.primary)
    clone.elsewhere("merged")
    assert tidy.tidy(tree, "next").lines[0].endswith("next level with origin/next")
    assert head(clone.primary) == before
    git(tree, "fetch", "-q", "origin")
    assert "fast-forwarded next by 1 commit(s)" in tidy.tidy(tree, "next").lines[0]
    assert head(clone.primary) != before


def test_edits_the_fast_forward_leaves_alone_stay_in_place(clone):
    (clone.primary / "shared.txt").write_text("a long-lived local edit", encoding="utf-8")
    tree = clone.task("task-1")
    clone.land(tree)
    report = tidy.tidy(tree, "next")
    assert report.lines[0].endswith("its edits left in place: shared.txt")
    assert head(clone.primary) == git(clone.primary, "rev-parse", "origin/next")
    assert (clone.primary / "shared.txt").read_text(encoding="utf-8") == "a long-lived local edit"


def test_many_edits_are_named_up_to_a_cap_and_counted(clone):
    for n in range(7):
        commit(clone.primary, f"local-{n}")
    git(clone.primary, "reset", "-q", "--soft", "origin/next")
    tree = clone.task("task-1")
    clone.land(tree)
    line = tidy.tidy(tree, "next").lines[0]
    assert line.endswith(
        "its edits left in place: local-0.txt, local-1.txt, local-2.txt, local-3.txt, "
        "local-4.txt and 2 more"
    )


def test_a_clashing_edit_refuses_the_fast_forward_and_changes_nothing(clone):
    (clone.primary / "shared.txt").write_text("mine", encoding="utf-8")
    before = head(clone.primary)
    tree = clone.task("task-1")
    commit(tree, "shared", "theirs")
    git(tree, "push", "-q", "origin", "HEAD:next")
    report = tidy.tidy(tree, "next")
    assert report.refused
    assert report.lines[0].endswith(
        "the fast-forward of next to origin/next was refused, nothing changed: error: Your "
        "local changes to the following files would be overwritten by merge: shared.txt"
    )
    assert head(clone.primary) == before
    assert (clone.primary / "shared.txt").read_text(encoding="utf-8") == "mine"


@pytest.mark.parametrize(
    ("make", "says"),
    [
        (
            lambda primary: commit(primary, "own"),
            "next has 1 commit(s) of its own and is 1 behind origin/next: left for you",
        ),
        (
            lambda primary: git(primary, "switch", "-q", "-c", "mine"),
            "mine checked out, not next: left as it is",
        ),
    ],
    ids=["diverged", "another-branch"],
)
def test_a_diverged_primary_or_one_on_another_branch_is_left(clone, make, says):
    make(clone.primary)
    before = head(clone.primary)
    tree = clone.task("task-1")
    clone.land(tree)
    report = tidy.tidy(tree, "next")
    assert report.lines[0].endswith(says)
    assert not report.refused
    assert head(clone.primary) == before


def test_a_primary_checkout_ahead_of_origin_has_nothing_to_fast_forward(clone):
    commit(clone.primary, "unpushed")
    before = head(clone.primary)
    report = tidy.tidy(clone.primary, "next")
    assert report.lines[0].endswith(
        "next 1 commit(s) ahead of origin/next, nothing to fast-forward"
    )
    assert head(clone.primary) == before and not report.refused


def test_a_bare_first_entry_is_named_and_nothing_is_fast_forwarded(clone):
    tree = clone.tmp / "on-bare"
    git(clone.origin, "worktree", "add", "-q", "-b", "on-bare", str(tree), "next")
    report = tidy.tidy(tree, "next")
    assert report.lines[0].endswith("a bare repository, nothing to fast-forward")


def test_no_origin_branch_does_nothing_and_says_why(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    git(clone.primary, "update-ref", "-d", "refs/remotes/origin/next")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.lines == (
        f"primary checkout {clone.primary.as_posix()}: no origin/next in this clone to follow, "
        "nothing fast-forwarded",
    )
    assert tree.exists() and "task-1" in branches(clone.primary)


def test_remove_takes_a_landed_worktree_and_its_branch(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    listing = tidy.tidy(clone.primary, "next")
    assert f"landed {tree.as_posix()}, branch task-1" in listing.lines
    assert listing.lines[-1] == (
        "1 other landed worktree(s): on the maintainer's word, `lifecycle tidy --remove` "
        "removes them"
    )
    assert tree.exists(), "listing removes nothing"
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: removed, its branch task-1 deleted" in report.lines
    assert report.lines[-1] == "1 of 1 other landed worktree(s) removed"
    assert not report.refused
    assert not tree.exists()
    assert "task-1" not in branches(clone.primary)
    assert tree not in listed(clone.primary)


def test_a_commit_rebased_before_it_landed_counts_as_landed(clone):
    """A push refused because the branch moved rebases first: the commit made on the branch
    is not on origin's, but its rebase, a patch-equivalent, is."""
    tree = clone.task("task-1")
    made = commit(tree, "task-1")
    clone.elsewhere("meanwhile")
    git(tree, "fetch", "-q", "origin")
    git(tree, "rebase", "-q", "origin/next")
    git(tree, "push", "-q", "origin", "HEAD:next")
    assert subprocess.run(
        ["git", "-C", str(tree), "merge-base", "--is-ancestor", made, "origin/next"]
    ).returncode
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: removed, its branch task-1 deleted" in report.lines


def test_an_amended_commit_counts_by_its_amend(clone):
    """The commit an amend replaced never lands, and is no patch-equivalent of the amend
    when the amend changed what it holds: only the amend is the branch's own work."""
    tree = clone.task("task-1")
    commit(tree, "task-1", "first draft")
    (tree / "task-1.txt").write_text("amended", encoding="utf-8")
    git(tree, "commit", "-q", "-a", "--amend", "--no-edit")
    git(tree, "push", "-q", "origin", "HEAD:next")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: removed, its branch task-1 deleted" in report.lines


def _edited(clone, tree):
    clone.land(tree)
    (tree / "task.txt").write_text("edited", encoding="utf-8")


def _untracked(clone, tree):
    clone.land(tree)
    (tree / "new.txt").write_text("new", encoding="utf-8")


def _reset_away(clone, tree):
    commit(tree, "never-pushed")
    git(tree, "reset", "-q", "--hard", "origin/next")


def _unlanded(clone, tree):
    commit(tree, "never-pushed")


def _picked_away(clone, tree):
    """A landed commit beside a cherry-picked one that was reset away."""
    clone.land(tree)
    git(tree, "switch", "-q", "-c", "side")
    picked = commit(tree, "picked")
    git(tree, "switch", "-q", "task")
    git(tree, "cherry-pick", picked)
    git(tree, "reset", "-q", "--hard", "origin/next")


def _fresh(clone, tree):
    pass


def _locked(clone, tree):
    clone.land(tree)
    git(clone.primary, "worktree", "lock", str(tree))


AWAY = "reset away, not pushed, or squash-merged"
KEPT = [
    (_edited, "edits or untracked files"),
    (_untracked, "edits or untracked files"),
    (_reset_away, f"a commit of its own not on next ({AWAY})"),
    (_unlanded, f"a commit of its own not on next ({AWAY})"),
    (_picked_away, f"a commit of its own not on next ({AWAY})"),
    (_fresh, "no commit of its own (a fresh session's)"),
    (_locked, "locked"),
]


@pytest.mark.parametrize(("make", "why"), KEPT, ids=[make.__name__[1:] for make, _ in KEPT])
def test_a_worktree_with_work_of_its_own_or_none_stays_named_with_why(clone, make, why):
    tree = clone.task("task")
    make(clone, tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: {why}" in report.lines
    assert report.lines[-1] == "no other landed worktree or branch to remove"
    assert tree.exists() and "task" in branches(clone.primary)


def test_the_default_branch_checked_out_in_a_linked_worktree_stays(clone):
    """``origin/HEAD`` names the default branch, which here is not the integration one."""
    git(clone.origin, "branch", "main", "next")
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    tree = clone.tmp / "on-main"
    git(clone.primary, "worktree", "add", "-q", "-b", "main", str(tree), "origin/next")
    clone.land(tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: main checked out here, the default branch" in report.lines
    assert tree.exists() and "main" in branches(clone.primary)


def test_the_integration_branch_checked_out_in_a_linked_worktree_stays(clone):
    git(clone.primary, "switch", "-q", "-c", "mine")
    tree = clone.tmp / "on-next"
    git(clone.primary, "worktree", "add", "-q", str(tree), "next")
    clone.land(tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: next checked out here, the integration branch" in (
        report.lines
    )
    assert tree.exists() and "next" in branches(clone.primary)


def park(tree):
    """Detach ``tree`` as an assistant's archive parks it for reuse: an empty reflog entry,
    naming no branch."""
    at = head(tree)
    git(tree, "update-ref", "--no-deref", "HEAD", at, at)


def admin(tree):
    return Path(git(tree, "rev-parse", "--absolute-git-dir"))


DETACHED = "a detached HEAD with no branch to delete"


def test_an_archived_worktree_goes_and_the_branch_it_left_with_it(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    park(tree)
    listing = tidy.tidy(clone.primary, "next")
    assert f"landed {tree.as_posix()}, a detached HEAD" in listing.lines
    assert "landed branch task-1, checked out nowhere" in listing.lines
    assert listing.lines[-1] == (
        "1 other landed worktree(s) and 1 landed branch(es) checked out nowhere: on the "
        "maintainer's word, `lifecycle tidy --remove` removes them"
    )
    assert tree.exists() and "task-1" in branches(clone.primary), "listing removes nothing"
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: removed, {DETACHED}" in report.lines
    assert "branch task-1: deleted, checked out nowhere" in report.lines
    assert report.lines[-1] == (
        "1 of 1 other landed worktree(s) removed, 1 of 1 landed branch(es) checked out "
        "nowhere deleted"
    )
    assert not report.refused
    assert not tree.exists() and "task-1" not in branches(clone.primary)


def test_a_scratch_worktree_left_clean_at_a_landed_commit_goes(clone):
    tree = clone.worktree("scratch", "--detach")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: removed, {DETACHED}" in report.lines
    assert report.lines[-1] == "1 of 1 other landed worktree(s) removed"
    assert not tree.exists()


def _scratch_edited(tree):
    (tree / "new.txt").write_text("new", encoding="utf-8")


def _scratch_elsewhere(tree):
    """HEAD moved to a commit made elsewhere: nothing made on it, but not landed."""
    made = git(tree, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "elsewhere")
    git(tree, "checkout", "-q", "--detach", made)


def _scratch_left_behind(tree):
    """A commit made on the detached HEAD, then HEAD moved back: only its reflog has it."""
    commit(tree, "left")
    git(tree, "checkout", "-q", "--detach", "origin/next")


DETACHED_KEPT = [
    (_scratch_edited, "edits or untracked files"),
    (_scratch_elsewhere, "its HEAD not on next"),
    (_scratch_left_behind, f"a commit of its own not on next ({AWAY})"),
]


@pytest.mark.parametrize(
    ("make", "why"), DETACHED_KEPT, ids=[make.__name__[9:] for make, _ in DETACHED_KEPT]
)
def test_a_detached_worktree_with_work_of_its_own_stays_named_with_why(clone, make, why):
    tree = clone.worktree("scratch", "--detach")
    make(tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: {why}" in report.lines
    assert report.lines[-1] == "no other landed worktree or branch to remove"
    assert tree.exists()


#: What git leaves in a checkout's git folder for each operation under way.
UNDER_WAY = [
    ("rebase-merge", "a rebase"),
    ("rebase-apply", "a rebase or `git am`"),
    ("MERGE_HEAD", "a merge"),
    ("CHERRY_PICK_HEAD", "a cherry-pick"),
    ("REVERT_HEAD", "a revert"),
    ("BISECT_LOG", "a bisect"),
]


@pytest.mark.parametrize(("state", "what"), UNDER_WAY, ids=[state for state, _ in UNDER_WAY])
def test_an_operation_under_way_keeps_a_clean_landed_worktree(clone, state, what):
    tree = clone.worktree("scratch", "--detach")
    at = admin(tree) / state
    if state.startswith("rebase-"):
        at.mkdir()
    else:
        at.write_text(head(tree), encoding="utf-8")
    assert git(tree, "status", "--porcelain") == ""
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: {what} in progress" in report.lines
    assert tree.exists()


def _stopped_rebase(cwd):
    """A rebase stopped by a failing step after replaying a landed commit as it was: the
    checkout lists as detached and clean, its HEAD on the integration branch."""
    subprocess.run(
        ["git", "-C", str(cwd), "rebase", "--exec", "exit 1", "origin/next~1"],
        capture_output=True,
        check=False,
    )
    assert (admin(cwd) / "rebase-merge").exists(), "the rebase stopped"


def test_a_worktree_mid_rebase_stays_and_so_does_the_branch_it_rewrites(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    _stopped_rebase(tree)
    assert tidy.worktrees(clone.primary)[-1].branch is None, "git lists it as detached"
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a rebase in progress" in report.lines
    assert not any("branch task-1" in line for line in report.lines)
    assert not report.refused
    assert tree.exists() and "task-1" in branches(clone.primary)


def test_a_bisect_left_in_a_worktree_on_its_branch_keeps_it(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    git(tree, "bisect", "start")
    git(tree, "bisect", "bad")
    git(tree, "bisect", "good", "HEAD~1")
    assert tidy.worktrees(clone.primary)[-1].branch == "task-1", "the bisect ended on it"
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a bisect in progress" in report.lines
    assert tree.exists() and "task-1" in branches(clone.primary)


def test_a_branch_the_primary_checkout_is_rebasing_stays(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "switch", "-q", "-c", "own", "origin/next")
    _stopped_rebase(clone.primary)
    report = tidy.tidy(tree, "next", remove=True)
    assert not any("branch own" in line for line in report.lines)
    assert not report.refused
    assert "own" in branches(clone.primary)


def test_a_detached_worktree_whose_git_folder_is_not_found_stays(clone, monkeypatch):
    tree = clone.worktree("scratch", "--detach")
    monkeypatch.setattr(tidy, "_admin", lambda root, tree: None)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert (
        f"kept {tree.as_posix()}: a detached HEAD whose git folder in the clone was not found"
        in report.lines
    )
    assert tree.exists()


def _unreadable(real, ref):
    """``tidy._run`` with the read of ``ref``'s reflog failing."""

    def run(root, *args):
        if args[:2] == ("reflog", "show") and any(arg.endswith(ref) for arg in args):
            return subprocess.CompletedProcess(args, 128, "", "fatal: cannot read")
        return real(root, *args)

    return run


def test_a_detached_worktree_whose_reflog_cannot_be_read_stays(clone, monkeypatch):
    tree = clone.worktree("scratch", "--detach")
    monkeypatch.setattr(tidy, "_run", _unreadable(tidy._run, "/HEAD"))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a detached HEAD whose reflog could not be read" in (
        report.lines
    )
    assert tree.exists()


def test_tidy_run_in_a_detached_worktree_keeps_it(clone):
    tree = clone.worktree("scratch", "--detach")
    report = tidy.tidy(tree, "next", remove=True)
    assert f"kept {tree.as_posix()}: the checkout this runs in" in report.lines
    assert tree.exists()


@pytest.mark.parametrize("extra", [(), ("--relative-paths",)], ids=["absolute", "relative"])
def test_a_detached_worktree_whose_folder_is_gone_goes_by_its_entry(clone, extra):
    tree = clone.worktree("scratch", "--detach", *extra)
    shutil.rmtree(tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: folder gone, its entry removed, {DETACHED}" in report.lines
    assert tree not in listed(clone.primary)


def test_a_gone_detached_worktree_with_a_commit_left_behind_stays(clone):
    tree = clone.worktree("scratch", "--detach")
    _scratch_left_behind(tree)
    shutil.rmtree(tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a commit of its own not on next ({AWAY})" in report.lines
    assert tree in listed(clone.primary)


@pytest.mark.parametrize(
    ("meanwhile", "why"),
    [
        (
            lambda tree: git(tree, "switch", "-q", "-c", "fresh"),
            "no commit of its own (a fresh session's)",
        ),
        (lambda tree: commit(tree, "late"), f"a commit of its own not on next ({AWAY})"),
    ],
    ids=["given-to-a-session", "a-commit-made"],
)
def test_a_detached_worktree_changed_before_its_removal_stays(clone, monkeypatch, meanwhile, why):
    tree = clone.worktree("scratch", "--detach")

    def probe(path):
        if path == tree:
            meanwhile(tree)
        return False

    monkeypatch.setattr(tidy, "probe", probe)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: {why}" in report.lines
    assert report.lines[-1] == "0 of 1 other landed worktree(s) removed"
    assert not report.refused
    assert tree.exists()


def test_a_landed_branch_no_checkout_holds_goes_whatever_left_it(clone):
    """A worktree removed by hand leaves its branch; one nothing was made on goes once its
    head has landed, as no session works on it."""
    tree = clone.task("task-1")
    clone.land(tree)
    git(clone.primary, "worktree", "remove", str(tree))
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "branch", "idle", "origin/next")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert "branch task-1: deleted, checked out nowhere" in report.lines
    assert "branch idle: deleted, checked out nowhere" in report.lines
    assert report.lines[-1] == "2 of 2 landed branch(es) checked out nowhere deleted"
    assert not {"task-1", "idle"} & set(branches(clone.primary))


def test_a_branch_no_checkout_holds_with_work_not_landed_stays(clone):
    tree = clone.task("task-1")
    commit(tree, "never-pushed")
    git(clone.primary, "worktree", "remove", str(tree))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept branch task-1: a commit of its own not on next ({AWAY})" in report.lines
    assert report.lines[-1] == "no other landed worktree or branch to remove"
    assert "task-1" in branches(clone.primary)


def test_a_branch_whose_reflog_cannot_be_read_stays(clone, monkeypatch):
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "branch", "idle", "origin/next")
    monkeypatch.setattr(tidy, "_run", _unreadable(tidy._run, "refs/heads/idle"))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert "kept branch idle: its reflog could not be read" in report.lines
    assert "idle" in branches(clone.primary)


def test_the_integration_and_default_branches_are_never_swept(clone):
    git(clone.origin, "branch", "main", "next")
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git(clone.primary, "branch", "main", "origin/main")
    git(clone.primary, "switch", "-q", "-c", "mine")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert not any("branch next" in line or "branch main" in line for line in report.lines)
    assert {"next", "main"} <= set(branches(clone.primary))


def test_a_bisect_that_detached_a_worktree_holds_its_branch(clone):
    tree = clone.task("task-1")
    for step in range(3):
        clone.land(tree, f"step-{step}")
    git(tree, "bisect", "start")
    git(tree, "bisect", "bad")
    git(tree, "bisect", "good", "HEAD~3")
    assert tidy.worktrees(clone.primary)[-1].branch is None, "the bisect detached it"
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a bisect in progress" in report.lines
    assert not any("branch task-1" in line for line in report.lines)
    assert not report.refused
    assert "task-1" in branches(clone.primary)


def test_a_rebase_by_patches_holds_the_branch_it_names(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    park(tree)
    state = admin(tree) / "rebase-apply"
    state.mkdir()
    (state / "head-name").write_text("refs/heads/task-1\n", encoding="utf-8")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a rebase or `git am` in progress" in report.lines
    assert not any("branch task-1" in line for line in report.lines)
    assert "task-1" in branches(clone.primary)


def test_a_branch_made_during_the_run_is_not_judged(clone, monkeypatch):
    """The branches are read before the checkouts: one a session makes and checks out in
    between is in neither, so nothing judges it held by none."""
    git(clone.primary, "fetch", "-q", "origin")
    real = tidy._branches

    def read(root):
        names = real(root)
        git(clone.primary, "branch", "late", "origin/next")
        return names

    monkeypatch.setattr(tidy, "_branches", read)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert not any("branch late" in line for line in report.lines)
    assert "late" in branches(clone.primary)


def test_a_branch_checked_out_since_the_listing_stays(clone, monkeypatch):
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "branch", "idle", "origin/next")
    took = clone.tmp / "took"
    real, judged = tidy._loose, []

    def loose(root, branch, integration):
        judged.append(branch)
        if len(judged) == 2:
            git(clone.primary, "worktree", "add", "-q", str(took), "idle")
        return real(root, branch, integration)

    monkeypatch.setattr(tidy, "_loose", loose)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert "kept branch idle: checked out since the listing" in report.lines
    assert not report.refused
    assert "idle" in branches(clone.primary)


def test_a_branch_that_fails_its_check_again_before_its_deletion_stays(clone, monkeypatch):
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "branch", "idle", "origin/next")
    checks = iter([None, "its head not on next"])
    monkeypatch.setattr(tidy, "_loose", lambda *args: next(checks))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert "kept branch idle: its head not on next" in report.lines
    assert not report.refused
    assert "idle" in branches(clone.primary)


def test_a_refused_deletion_of_a_branch_no_checkout_holds_is_said(clone, monkeypatch):
    git(clone.primary, "fetch", "-q", "origin")
    git(clone.primary, "branch", "idle", "origin/next")
    real = tidy._run

    def run(root, *args):
        if args[:2] == ("branch", "-D"):
            return subprocess.CompletedProcess(args, 1, "", "error: cannot delete branch")
        return real(root, *args)

    monkeypatch.setattr(tidy, "_run", run)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert "branch idle: its deletion was refused: error: cannot delete branch" in report.lines
    assert "idle" in branches(clone.primary)


def test_a_worktree_whose_branch_reflog_cannot_be_read_stays(clone, monkeypatch):
    tree = clone.task("task-1")
    clone.land(tree)
    monkeypatch.setattr(tidy, "_run", _unreadable(tidy._run, "refs/heads/task-1"))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: the reflog of its branch task-1 could not be read" in (
        report.lines
    )
    assert tree.exists()


def test_a_detached_worktree_gone_from_gits_list_before_its_removal_is_said(clone, monkeypatch):
    tree = clone.worktree("scratch", "--detach")

    def probe(path):
        if path == tree:
            git(clone.primary, "worktree", "remove", str(tree))
        return False

    monkeypatch.setattr(tidy, "probe", probe)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: gone from git's list before its removal, nothing done" in (
        report.lines
    )
    assert report.lines[-1] == "0 of 1 other landed worktree(s) removed"
    assert not report.refused


def test_a_refused_removal_of_a_detached_worktree_keeps_it(clone, monkeypatch):
    tree = clone.worktree("scratch", "--detach")
    monkeypatch.setattr(tidy, "_run", _failing_remove(tidy._run, partway=False))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert any(
        line.startswith(f"{tree.as_posix()}: removal refused, kept: error: failed")
        for line in report.lines
    )
    assert tree in listed(clone.primary)


def test_a_detached_removal_that_fails_partway_names_the_folder(clone, monkeypatch):
    tree = clone.worktree("scratch", "--detach")
    monkeypatch.setattr(tidy, "_run", _failing_remove(tidy._run, partway=True))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert any(
        line.startswith(f"{tree.as_posix()}: removal failed partway (error: failed to delete")
        and line.endswith(
            f"git dropped the worktree, {DETACHED}; the folder is left behind for you"
        )
        for line in report.lines
    )
    assert tree not in listed(clone.primary) and tree.exists()


def test_the_checkout_tidy_runs_in_stays_though_it_landed(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    other = clone.task("task-2")
    clone.land(other)
    report = tidy.tidy(tree, "next", remove=True)
    assert f"kept {tree.as_posix()}: the checkout this runs in" in report.lines
    assert f"{other.as_posix()}: removed, its branch task-2 deleted" in report.lines
    assert tree.exists() and "task-1" in branches(clone.primary)


def test_a_landed_worktree_whose_folder_is_gone_goes_alone_with_its_branch(clone):
    tree = clone.task("task-1")
    clone.land(tree)
    kept = clone.task("task-2")
    commit(kept, "never-pushed")
    shutil.rmtree(tree)
    shutil.rmtree(kept)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: folder gone, its entry removed, its branch task-1 deleted" in (
        report.lines
    )
    assert tree not in listed(clone.primary)
    assert "task-1" not in branches(clone.primary)
    assert kept in listed(clone.primary), "a kept worktree's entry is not pruned with it"
    assert "task-2" in branches(clone.primary)


def test_a_worktree_in_use_stays_whole(clone, monkeypatch):
    tree = clone.task("task-1")
    clone.land(tree)
    monkeypatch.setattr(tidy, "probe", lambda path: path == tree)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: in use" in report.lines
    assert report.lines[-1] == "0 of 1 other landed worktree(s) removed"
    assert not report.refused
    assert tree.exists() and "task-1" in branches(clone.primary)


def test_the_probe_sees_a_process_in_the_folder_only_on_windows(clone):
    """On Windows a folder a process has as its working directory cannot be renamed;
    elsewhere it can, so the probe tells nothing there and says so by False."""
    tree = clone.task("task-1")
    held = subprocess.Popen(
        [sys.executable, "-c", "print('ready', flush=True); import sys; sys.stdin.read()"],
        cwd=tree,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert held.stdout.readline().strip() == "ready", "the child runs in the folder"
    try:
        assert tidy.probe(tree) is (os.name == "nt")
    finally:
        held.communicate("")
    assert tidy.probe(tree) is False
    assert tree.exists() and not tree.with_name(f"{tree.name}.tidy-probe").exists()


def test_a_probe_that_cannot_move_a_folder_back_refuses_that_one_and_reports_the_rest(
    clone, monkeypatch, capsys
):
    tree = clone.task("task-1")
    clone.land(tree)
    moved = tree.with_name("task-1.tidy-probe")
    real = Path.rename

    def rename(self, target):
        if Path(self) == moved:
            raise OSError("access denied")
        return real(self, target)

    monkeypatch.setattr(tidy, "PROBES", True)
    monkeypatch.setattr(Path, "rename", rename)
    monkeypatch.chdir(clone.primary)
    assert cli.main(["tidy", "--remove"]) == 1
    out = capsys.readouterr().out.splitlines()
    assert "fast-forwarded next by 1 commit(s)" in out[0], "what ran before it is reported"
    assert (
        f"{tree.as_posix()}: the probe moved it to {moved.as_posix()} and could not move it "
        "back (access denied): rename it back; nothing in it was touched"
    ) in out
    assert moved.exists() and "task-1" in branches(clone.primary)


def test_a_branch_that_fails_its_check_again_after_removal_stays(clone, monkeypatch):
    tree = clone.task("task-1")
    clone.land(tree)
    checks = iter([None, "a commit of its own not on next"])
    monkeypatch.setattr(tidy, "_unlanded", lambda *args: next(checks))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert (
        f"{tree.as_posix()}: removed, its branch task-1 kept: a commit of its own not on next"
        in report.lines
    )
    assert not tree.exists() and "task-1" in branches(clone.primary)


def test_a_refused_branch_deletion_is_said(clone, monkeypatch):
    tree = clone.task("task-1")
    clone.land(tree)
    real = tidy._run

    def run(root, *args):
        if args[:2] == ("branch", "-D"):
            return subprocess.CompletedProcess(args, 1, "", "error: cannot delete branch")
        return real(root, *args)

    monkeypatch.setattr(tidy, "_run", run)
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert (
        f"{tree.as_posix()}: removed, its branch task-1 kept: error: cannot delete branch"
        in report.lines
    )


def _failing_remove(real, partway, deletes=True):
    """``tidy._run`` with ``git worktree remove`` failing: before it touched anything, or,
    as git does when it cannot delete the folder, after it dropped the worktree's entry;
    without ``deletes``, ``git branch -D`` fails too."""

    def run(root, *args):
        if args[:2] == ("branch", "-D") and not deletes:
            return subprocess.CompletedProcess(args, 1, "", "error: cannot delete branch")
        if args[:2] != ("worktree", "remove"):
            return real(root, *args)
        if partway:
            real(root, *args)
            Path(args[2]).mkdir()
            (Path(args[2]) / "held.txt").write_text("a file in use", encoding="utf-8")
        return subprocess.CompletedProcess(args, 255, "", f"error: failed to delete '{args[2]}'")

    return run


def test_a_refused_removal_keeps_the_worktree_and_its_branch(clone, monkeypatch, capsys):
    tree = clone.task("task-1")
    clone.land(tree)
    monkeypatch.setattr(tidy, "_run", _failing_remove(tidy._run, partway=False))
    monkeypatch.chdir(clone.primary)
    assert cli.main(["tidy", "--remove"]) == 1
    out = capsys.readouterr().out
    assert f"{tree.as_posix()}: removal refused, kept with its branch: error: failed" in out
    assert tree in listed(clone.primary) and "task-1" in branches(clone.primary)


def test_a_removal_that_fails_partway_deletes_the_branch_git_left_and_names_the_folder(
    clone, monkeypatch
):
    tree = clone.task("task-1")
    clone.land(tree)
    monkeypatch.setattr(tidy, "_run", _failing_remove(tidy._run, partway=True))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert any(
        line.startswith(f"{tree.as_posix()}: removal failed partway (error: failed to delete")
        and line.endswith("so its branch task-1 is deleted; the folder is left behind for you")
        for line in report.lines
    )
    assert tree not in listed(clone.primary) and "task-1" not in branches(clone.primary)
    assert tree.exists(), "git left the folder"


def test_a_partway_removal_whose_branch_cannot_go_says_it_stays(clone, monkeypatch):
    tree = clone.task("task-1")
    clone.land(tree)
    monkeypatch.setattr(tidy, "_run", _failing_remove(tidy._run, partway=True, deletes=False))
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert report.refused
    assert any(
        line.endswith(
            "git dropped the worktree, and its branch task-1 stays: error: cannot delete "
            "branch; the folder is left behind for you"
        )
        for line in report.lines
    )
    assert tree not in listed(clone.primary) and "task-1" in branches(clone.primary)


def test_the_command_lists_and_exits_zero_with_nothing_refused(clone, capsys, monkeypatch):
    tree = clone.task("task-1")
    clone.land(tree)
    monkeypatch.chdir(tree)
    assert cli.main(["tidy"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert "fast-forwarded next by 1 commit(s)" in out[0]
    assert out[-1] == "no other landed worktree or branch to remove"


def _section(text, number):
    return re.search(rf"^## {number}\..*?(?=^## )", text, re.M | re.S).group(0)


def test_complete_runs_tidy_after_both_landings_and_removes_only_on_the_maintainers_word():
    skill = (KIT / "skills" / "complete" / "SKILL.md").read_text(encoding="utf-8")
    land = _section(skill, 4)
    follows = re.search(r"^\*\*The primary checkout follows\.\*\*.*$", land, re.M).group(0)
    assert "the direct push accepted, or the PR merged, which `lifecycle merge` fetched" in follows
    assert follows.index("`lifecycle merge`") < follows.index("`lifecycle tidy`")
    assert "`lifecycle tidy --remove` runs only on the maintainer's word" in follows
    assert "a refusal it prints (exit 1) is that line, and the batch goes on" in follows
    merged = land.index("`lifecycle merge <PR>`")
    assert merged < land.index(follows) < land.index("**The push's CI:**")
    assert "Then *The primary checkout follows*, and the push's CI" in land
    assert "Then *The primary checkout follows*, below" in land[merged:]
    branches = _section(skill, 7)
    assert "`lifecycle tidy --remove` on the maintainer's word" in branches
    assert "A squash merge leaves the branch's commits off the integration branch" in branches
    assert "`lifecycle tidy`'s first and last lines" in skill.split("## 8.")[1]


def test_complete_merges_by_the_prs_state_and_leaves_a_linked_worktrees_branch():
    """gh's --delete-branch exits 1 on a merged PR in a linked worktree: the skill reads the
    merge from `lifecycle merge`, which leaves that worktree's branch, squash-merged, for
    git worktree remove and git branch -D, since tidy keeps it."""
    skill = (KIT / "skills" / "complete" / "SKILL.md").read_text(encoding="utf-8")
    assert "--delete-branch" not in skill and "gh pr merge" not in skill
    land = _section(skill, 4)
    step = land[land.index("4. `lifecycle merge <PR>`") : land.index("**The primary checkout")]
    assert "never from gh's exit code" in step
    assert "1 with a line saying the PR is not merged" in step
    assert "stop for the maintainer, the PR left as it is" in step
    unread = re.search(r"^ +- 1 with a `lifecycle:` line.*$", step, re.M).group(0)
    assert "or no line at all (the shell cut it off)" in unread
    assert "reads the state first and merges only a PR still open" in unread
    assert "Still unread, the batch stops before § 5" in unread
    follows = re.search(r"^\*\*The primary checkout follows\.\*\*.*$", land, re.M).group(0)
    assert "where it printed that its fetch failed, `git fetch origin` first" in follows
    branches = _section(skill, 7)
    assert "gh leaves" not in branches and "`--delete-branch`" not in branches
    squash = branches[branches.index("A squash merge leaves") :]
    assert "`lifecycle merge` leaves its branch" in squash
    assert "`git worktree remove <path>` and `git branch -D <branch>`" in squash
    assert "`lifecycle merge`'s lines" in skill.split("## 8.")[1]


@pytest.mark.parametrize("name", ["clarify", "review"])
def test_the_rounds_run_tidy_on_doctors_note(name):
    skill = (KIT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    zero = _section(skill, 0)
    bullet = re.search(r"^   - a `note` whose fix is `tidy`: run `lifecycle tidy`.*$", zero, re.M)
    assert bullet, "§ 0 runs tidy on doctor's note"
    assert "never its `--remove`, which is the maintainer's word" in bullet.group(0)
    assert "a refusal it prints (exit 1) is no failure of the command" in bullet.group(0)
    assert "in the primary checkout, read AGENTS.md again" in bullet.group(0)
    assert zero.index("fix is `tidy`") < zero.index("anything else: carry on")
