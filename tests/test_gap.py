import ast
import json
import re
import subprocess

import pytest
from lifecycle import cli, gap
from test_section_refs import ROOT, sources, text_of

KIT = "o/kit"


class FakeGh:
    """``gap.gh`` answering from ``replies``, keyed by a call's first two words; a reply that
    is an exception is raised. Each call is kept with whether it was the filing."""

    def __init__(self, **replies):
        self.replies = replies
        self.calls = []

    def __call__(self, *args, cwd, filing=False):
        self.calls.append((args, filing))
        reply = self.replies.get("_".join(args[:2]).replace("-", "_").split("/")[0], "")
        if isinstance(reply, Exception):
            raise reply
        return reply

    def made(self, *words):
        return [args for args, _ in self.calls if args[: len(words)] == words]


@pytest.fixture
def body(tmp_path):
    path = tmp_path / "gap.md"
    path.write_text("What the guide says, what the task met, the gap.\n", encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def kit(monkeypatch):
    monkeypatch.setattr(gap, "kit_repository", lambda: KIT)
    monkeypatch.setattr(cli, "kit_repository", lambda: KIT)


def install(monkeypatch, **replies):
    fake = FakeGh(**replies)
    monkeypatch.setattr(gap, "gh", fake)
    return fake


def test_one_who_can_push_files_on_the_kit_unlabelled(monkeypatch, repo, body):
    fake = install(
        monkeypatch, api_repos="true\n", issue_create=f"https://github.com/{KIT}/issues/41\n"
    )
    filed = gap.file(repo, "A gap", body)
    assert filed.reference == f"{KIT}#41" and filed.label is None
    assert not fake.made("repo") and not fake.made("label")
    (create,) = fake.made("issue", "create")
    assert create[create.index("--repo") + 1] == KIT and "--label" not in create
    assert fake.calls[-1][1] is True  # the filing, with no time limit


def test_one_who_cannot_push_files_here_labelled_with_the_label_created(monkeypatch, repo, body):
    fake = install(
        monkeypatch,
        api_repos="false\n",
        repo_view="me/app\n",
        label_list="",  # gh prints nothing where no label matches the search
        issue_create="https://github.com/me/app/issues/7\n",
    )
    filed = gap.file(repo, "A gap", body)
    assert filed.reference == "#7" and filed.label == gap.LABEL
    (created,) = fake.made("label", "create", gap.LABEL)
    assert created[created.index("--repo") + 1] == "me/app"
    (create,) = fake.made("issue", "create")
    assert create[create.index("--repo") + 1] == "me/app"
    assert create[create.index("--label") + 1] == gap.LABEL


def test_a_label_present_among_many_is_found_by_its_name_and_not_created(monkeypatch, repo, body):
    listed = [{"name": "kit-gaps"}, {"name": "Kit-Gap"}]
    fake = install(
        monkeypatch,
        api_repos="false\n",
        repo_view="me/app\n",
        label_list=json.dumps(listed),
        issue_create="https://github.com/me/app/issues/8\n",
    )
    gap.file(repo, "A gap", body)
    (searched,) = fake.made("label", "list")
    assert searched[searched.index("--search") + 1] == gap.LABEL
    assert not fake.made("label", "create")


def test_a_label_only_named_like_it_is_not_taken_for_it(monkeypatch, repo, body):
    fake = install(
        monkeypatch,
        api_repos="false\n",
        repo_view="me/app\n",
        label_list=json.dumps([{"name": "kit-gaps"}]),
        issue_create="https://github.com/me/app/issues/9\n",
    )
    gap.file(repo, "A gap", body)
    assert fake.made("label", "create", gap.LABEL)


@pytest.mark.parametrize(
    "replies",
    [
        {"api_repos": gap.GapError("no issue filed: gh api failed: HTTP 401")},
        {"api_repos": "false\n", "repo_view": gap.GapError("no issue filed: no repository")},
        {
            "api_repos": "false\n",
            "repo_view": "me/app\n",
            "label_list": "[]",
            "label_create": gap.GapError("no issue filed: HTTP 403"),
        },
    ],
    ids=["the check fails", "no github repository", "the label is refused"],
)
def test_a_failure_before_the_filing_files_nothing(monkeypatch, repo, body, replies):
    fake = install(monkeypatch, **replies)
    with pytest.raises(gap.GapError, match=r"^no issue filed: "):
        gap.file(repo, "A gap", body)
    assert not fake.made("issue", "create")


def test_a_missing_body_files_nothing(monkeypatch, repo, tmp_path):
    fake = install(monkeypatch, api_repos="true\n")
    with pytest.raises(gap.GapError, match=r"^no issue filed: .* is not a file"):
        gap.file(repo, "A gap", tmp_path / "absent.md")
    assert not fake.calls


def test_a_checkout_of_the_kit_names_its_own_issue_bare(monkeypatch, kit_checkout, body):
    install(monkeypatch, api_repos="true\n", issue_create=f"https://github.com/{KIT}/issues/5\n")
    assert gap.file(kit_checkout, "A gap", body).reference == "#5"


def test_a_failed_gh_call_is_no_issue_filed(monkeypatch, tmp_path):
    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "HTTP 401: Bad credentials\n")

    monkeypatch.setattr(gap.subprocess, "run", run)
    with pytest.raises(gap.GapError, match=r"^no issue filed: gh api repos/o/kit failed: HTTP 401"):
        gap.can_push(KIT, tmp_path)


def test_a_read_that_stalls_is_no_issue_filed(monkeypatch, tmp_path):
    limits = []

    def run(command, **kwargs):
        limits.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(gap.subprocess, "run", run)
    with pytest.raises(
        gap.GapError, match=f"^no issue filed: .* no answer in {gap.CALL_SECONDS} s"
    ):
        gap.can_push(KIT, tmp_path)
    assert limits == [gap.CALL_SECONDS]


TRANSIT = (
    "GraphQL: Something went wrong while executing your query. This may be the result of a "
    "timeout, or it could be a GitHub bug.\n"
)


def answering(filing):
    """``subprocess.run`` for ``gh``: every read answers that the user can push, and the
    filing ends as ``filing`` (an exit code and its stderr)."""

    def run(command, **kwargs):
        if command[1:3] == ["issue", "create"]:
            assert kwargs["timeout"] is None
            return subprocess.CompletedProcess(command, filing[0], "", filing[1])
        return subprocess.CompletedProcess(command, 0, "true\n", "")

    return run


def test_a_filing_that_fails_in_transit_is_not_reported_unfiled(monkeypatch, repo, body):
    monkeypatch.setattr(gap.subprocess, "run", answering((1, TRANSIT)))
    with pytest.raises(gap.GapError) as failed:
        gap.file(repo, "A gap", body)
    assert not str(failed.value).startswith("no issue filed")
    assert str(failed.value).endswith(
        f"the issue may be filed anyway: read {KIT}'s issues before filing again"
    )


def test_a_filing_github_refuses_is_no_issue_filed(monkeypatch, repo, body):
    refused = "HTTP 403: Resource not accessible by integration\n"
    monkeypatch.setattr(gap.subprocess, "run", answering((1, refused)))
    with pytest.raises(gap.GapError, match=r"^no issue filed: gh issue create failed: HTTP 403"):
        gap.file(repo, "A gap", body)


def test_a_filing_with_no_issue_link_is_not_reported_unfiled(monkeypatch, repo, body):
    install(monkeypatch, api_repos="true\n", issue_create="\n")
    with pytest.raises(gap.GapError) as failed:
        gap.file(repo, "A gap", body)
    assert str(failed.value).startswith("gh issue create printed no issue link (nothing)")
    assert f"read {KIT}'s issues before filing again" in str(failed.value)


def test_gh_not_installed_is_no_issue_filed(monkeypatch, tmp_path):
    def run(command, **kwargs):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(gap.subprocess, "run", run)
    with pytest.raises(gap.GapError, match=r"^no issue filed: gh is not installed$"):
        gap.can_push(KIT, tmp_path)


def test_lifecycle_gap_prints_where_it_filed(monkeypatch, capsys, repo, body):
    install(
        monkeypatch,
        api_repos="false\n",
        repo_view="me/app\n",
        label_list="[]",
        issue_create="https://github.com/me/app/issues/7\n",
    )
    monkeypatch.chdir(repo.root)
    code = cli.main(["gap", "--title", "A gap", "--body-file", str(body)])
    out = capsys.readouterr().out
    assert code == 0
    assert out == (
        "filed #7 https://github.com/me/app/issues/7, labelled kit-gap: "
        f"the signed-in gh account cannot push to {KIT}\n"
    )


def test_lifecycle_gap_exits_1_when_nothing_is_filed(monkeypatch, capsys, repo, body):
    install(monkeypatch, api_repos=gap.GapError("no issue filed: gh api failed: offline"))
    monkeypatch.chdir(repo.root)
    code = cli.main(["gap", "--title", "A gap", "--body-file", str(body)])
    assert (
        code == 1
        and capsys.readouterr().err == "lifecycle: no issue filed: gh api failed: offline\n"
    )


#: A gap or a reusable pattern sent to the kit by name, which a person who cannot write to the
#: kit is refused at: every such text sends it where `lifecycle gap` files it instead.
TO_THE_KIT = re.compile(
    r"\b(?:file[ds]?|filing|issues?)\s+on\s+the\s+(?:lifecycle\s+)?kit\b|\bgoes\s+to\s+the\s+kit\b",
    re.I,
)
NEWLINE = "\n"


def prose():
    """Each text a person or an agent reads, as its path, its first line and the text: the
    kit's prose files (the released sections of the CHANGELOG and UPGRADING.md being
    history), and the strings of the tools, adjacent literals joined."""
    for path in sources():
        text = text_of(path)
        if path.name == "UPGRADING.md":
            text = text.split("\n## ")[0]
        yield path.relative_to(ROOT).as_posix(), 1, text
    for path in sorted((ROOT / "tools" / "lifecycle").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield path.relative_to(ROOT).as_posix(), node.lineno, node.value


def test_no_text_sends_a_gap_to_the_kit_by_name():
    found = [
        f"{where}:{line + text[: hit.start()].count(NEWLINE)}: {' '.join(hit.group(0).split())}"
        for where, line, text in prose()
        for hit in TO_THE_KIT.finditer(text)
    ]
    assert not found, "send it where `lifecycle gap` files it:\n" + "\n".join(found)
