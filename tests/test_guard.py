from lifecycle import guard

PUSH = "refs/heads/develop abc refs/heads/{} def\n"


def test_a_push_to_the_protected_branch_is_refused(monkeypatch, capsys):
    monkeypatch.delenv("PRE_COMMIT_REMOTE_BRANCH", raising=False)
    assert guard.push("master", [PUSH.format("master")]) == 1
    assert "refused a push to master" in capsys.readouterr().err


def test_a_push_elsewhere_passes(monkeypatch):
    monkeypatch.delenv("PRE_COMMIT_REMOTE_BRANCH", raising=False)
    assert guard.push("master", [PUSH.format("develop")]) == 0


def test_pre_commit_names_the_ref(monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_REMOTE_BRANCH", "refs/heads/master")
    assert guard.push("master", []) == 1


def test_one_protected_ref_among_several_is_refused(monkeypatch):
    monkeypatch.delenv("PRE_COMMIT_REMOTE_BRANCH", raising=False)
    lines = [PUSH.format("develop"), PUSH.format("master")]
    assert guard.push("master", lines) == 1


def _pr(sha, base="master", merged="2026-11-20"):
    return {"number": 5, "merged_at": merged, "merge_commit_sha": sha, "base": {"ref": base}}


def test_a_merge_commit_deploys(monkeypatch):
    monkeypatch.setattr(guard, "_recent_merges", lambda repo, base: [_pr("abc")])
    assert guard.deploy("master", "o/r", "abc", wait=0) == 0


def test_a_head_no_pr_merged_is_refused(monkeypatch, capsys):
    monkeypatch.setattr(
        guard, "_recent_merges", lambda repo, base: [_pr("other"), _pr("abc", merged=None)]
    )
    assert guard.deploy("master", "o/r", "abc", wait=0) == 1
    assert "not the merge commit" in capsys.readouterr().err


def test_a_merge_into_another_base_does_not_count():
    assert guard.merged_as([_pr("abc", base="develop")], "abc", "master") is None
