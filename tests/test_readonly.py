import pytest
from lifecycle.readonly import (
    HEREDOC,
    OPTION_AFTER_ALLOWED,
    SUBSTITUTION,
    UNKNOWN,
    WRITE_REDIRECT,
    check,
)

ALLOW = ("pre-commit run ruff-all --hook-stage pre-push --all-files",)


@pytest.mark.parametrize(
    "command",
    [
        "git diff",
        "git -C ../wt diff --stat HEAD~1",
        "git --no-pager log --oneline -5",
        "git show HEAD:path/to/file.py",
        "git worktree list",
        "git stash list",
        "gh issue view 12 --json body -q .body",
        "gh pr diff 7",
        "cat a.py | grep -n foo | head -3",
        "grep -rn 'x$' apps/ 2>/dev/null",
        "git log 2>&1 | tail -5",
        "find tests -name '*.py'",
        "sed -n 10,40p file.py",
        "ls docs && wc -l AGENTS.md",
        "PYTHONUTF8=1 git log",
        "pre-commit run ruff-all --hook-stage pre-push --all-files",
        "echo 'cost: $5'",
        "wc -l < AGENTS.md",
        "git log --format='%h {x}'",
        "git log >/dev/null 2>&1",
        "lifecycle config",
        "sort -r notes.txt",
        "git log --oneline --output-indicator-new=+",
        "git grep --or -e a -e b",
        "lifecycle guides check",
        "lifecycle upgraded --json",
    ],
)
def test_reads_pass(command):
    assert check(command, ALLOW) is None


@pytest.mark.parametrize(
    ("command", "reason"),
    [
        ("git stash", UNKNOWN),
        ("lifecycle upgrade", UNKNOWN),
        ("lifecycle guides push -m x", UNKNOWN),
        ("git checkout -- a.py", UNKNOWN),
        ("git -c alias.x=!rm diff", UNKNOWN),
        ("git diff --output=patch.txt", UNKNOWN),
        ("git branch new", UNKNOWN),
        ("gh issue edit 3 --body x", UNKNOWN),
        ("gh api graphql -f query=x", UNKNOWN),
        ("pytest tests/", UNKNOWN),
        ('python -c \'open("x","w")\'', UNKNOWN),
        ("pre-commit run --all-files", UNKNOWN),
        ("find . -name x -delete", UNKNOWN),
        ("sed -i s/a/b/ f", UNKNOWN),
        ("sort -o out in", UNKNOWN),
        ("uniq in out", UNKNOWN),
        ("GIT_DIR=x git log", UNKNOWN),
        ("find . -name x {-delete,}", SUBSTITUTION),
        ("git diff {--output=p,}", SUBSTITUTION),
        ("sort {-o,out} in", SUBSTITUTION),
        ("git grep -O vim foo", UNKNOWN),
        ("git grep -nOless foo", UNKNOWN),
        ("git grep --open-files-in-pager=vim foo", UNKNOWN),
        ("rg --pre ./run foo", UNKNOWN),
        ("rg --pre-glob '*.x' foo", UNKNOWN),
        ("tree -o out.txt", UNKNOWN),
        ("git grep --op=touch x", UNKNOWN),
        ("git grep --open=touch x", UNKNOWN),
        ("git diff --outp=patch.txt", UNKNOWN),
        ("sort -ro out in", UNKNOWN),
        ("sort --ou=out in", UNKNOWN),
        ("sort --compress-program=sh in", UNKNOWN),
        ("sort --co=sh in", UNKNOWN),
        ("git log > nul", WRITE_REDIRECT),
        ("git log 2>/dev/null.x", WRITE_REDIRECT),
        ("git log >&1out", WRITE_REDIRECT),
        ("cat a > b", WRITE_REDIRECT),
        ("cat a>b", WRITE_REDIRECT),
        ("git log >> notes", WRITE_REDIRECT),
        ("cat $HOME/x", SUBSTITUTION),
        ('echo "$(rm -rf x)"', SUBSTITUTION),
        ("echo `id`", SUBSTITUTION),
        ("diff <(git show a:x) x", SUBSTITUTION),
        ("cat <<EOF\nx\nEOF", HEREDOC),
        ("git diff; rm x", UNKNOWN),
        ("git log && touch x", UNKNOWN),
        ("git diff \\\n--output=patch.txt", UNKNOWN),
        ("git diff \\\r\n--output=patch.txt", UNKNOWN),
        ("pre-commit run ruff-all --hook-stage pre-push --all-files && rm x", UNKNOWN),
    ],
)
def test_writes_and_unknowns_are_refused(command, reason):
    assert check(command, ALLOW) == reason


def test_an_unclosed_quote_is_refused():
    assert "quote" in check("grep 'x")


@pytest.mark.parametrize(
    "command",
    [
        "ruff check tools tests --fix",
        "ruff check tools tests --output-file=report.txt",
        "ruff check tools tests extra '--fix'",
        "ruff check tools tests -o report.txt",
        "ruff check tools tests \\--fix",
        "ruff check tools tests \\\n--fix",
        "ruff check tools tests \\  --fix",
    ],
)
def test_an_option_appended_to_an_allow_entry_is_refused(command):
    assert check(command, ("ruff check tools tests",)) == OPTION_AFTER_ALLOWED


def test_a_path_appended_to_an_allow_entry_passes():
    assert check("ruff check tools tests bin/", ("ruff check tools tests",)) is None


def test_a_longer_entry_is_read_past_a_shorter_one():
    allow = ("ruff format", "ruff format --check tools tests")
    assert check("ruff format --check tools tests", allow) is None


def test_an_allow_entry_never_refuses_a_read_the_guard_knows():
    assert check("git diff --check --cached", ("git diff --check",)) is None


def test_a_continued_line_reads_as_one_command():
    assert check("git log \\\n--oneline -5") is None
