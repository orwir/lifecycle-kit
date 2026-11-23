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
        "removes them and their branches"
    )
    assert tree.exists(), "listing removes nothing"
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"{tree.as_posix()}: removed, its branch task-1 deleted" in report.lines
    assert report.lines[-1] == "1 of 1 other landed worktree(s) removed with their branches"
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
    assert report.lines[-1] == "0 of 0 other landed worktree(s) removed with their branches"
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


def test_a_detached_worktree_stays(clone):
    tree = clone.worktree("scratch", "--detach")
    report = tidy.tidy(clone.primary, "next", remove=True)
    assert f"kept {tree.as_posix()}: a detached HEAD" in report.lines
    assert tree.exists()


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
    assert report.lines[-1] == "0 of 1 other landed worktree(s) removed with their branches"
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
    assert out[-1] == "no other landed worktree to remove"


def _section(text, number):
    return re.search(rf"^## {number}\..*?(?=^## )", text, re.M | re.S).group(0)


def test_complete_runs_tidy_after_both_landings_and_removes_only_on_the_maintainers_word():
    skill = (KIT / "skills" / "complete" / "SKILL.md").read_text(encoding="utf-8")
    land = _section(skill, 4)
    follows = re.search(r"^\*\*The primary checkout follows\.\*\*.*$", land, re.M).group(0)
    assert "the direct push accepted, or the PR merged and then `git fetch origin`" in follows
    assert follows.index("`git fetch origin`") < follows.index("`lifecycle tidy`")
    assert "`lifecycle tidy --remove` runs only on the maintainer's word" in follows
    assert "a refusal it prints (exit 1) is that line, and the batch goes on" in follows
    merged = land.index("`gh pr merge <PR> --squash --delete-branch`")
    assert merged < land.index(follows) < land.index("**The push's CI:**")
    assert "Then *The primary checkout follows*, and the push's CI" in land
    assert "Then *The primary checkout follows*, below." in land[merged:]
    branches = _section(skill, 7)
    assert "`lifecycle tidy --remove` on the maintainer's word" in branches
    assert "A squash merge leaves the branch's commits off the integration branch" in branches
    assert "`lifecycle tidy`'s first and last lines" in skill.split("## 8.")[1]


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
