import json

import pytest
from lifecycle import METHOD, board

FIELDS = [{"name": "Status", "id": "F", "options": [{"name": "Done", "id": "D"}]}]

REPO = {
    "id": "R",
    "nameWithOwner": "o/r",
    "name": "r",
    "owner": {"login": "o"},
    "visibility": "PRIVATE",
    "url": "https://github.com/o/r",
}


def choice(id_, name, color="GRAY", description=""):
    return {"id": id_, "name": name, "color": color, "description": description}


# What `gh project create` leaves: three options, Todo first.
FRESH = [
    choice("t", "Todo", "GREEN", "This item hasn't been started"),
    choice("p", "In Progress", "YELLOW", "This is actively being worked on"),
    choice("d", "Done", "PURPLE", "This has been completed"),
]
FOUR = [
    choice("b", "Backlog"),
    choice("r", "Ready"),
    choice("p", "In Progress"),
    choice("d", "Done"),
]


def issue(number, repo="o/r"):
    return f"https://github.com/{repo}/issues/{number}"


def open_issue(number, *labels):
    """An open issue as `gh issue list --json id,url,number,labels` gives it."""
    return {
        "id": f"I{number}",
        "url": issue(number),
        "number": number,
        "labels": [{"name": label} for label in labels],
    }


def card(id_, number, status=None, kind="Issue", repo="o/r", archived=False):
    """A card as the board's items query returns it."""
    content = {
        "__typename": kind,
        "number": number,
        "url": issue(number, repo),
        "repository": {"nameWithOwner": repo},
    }
    value = {"name": status} if status else None
    return {"id": id_, "isArchived": archived, "fieldValueByName": value, "content": content}


class FakeGh:
    """`gh` as setup and move call it, answering from a board held in memory."""

    def __init__(
        self,
        options,
        items=(),
        issues=(),
        workflows=(),
        linked=("o/r",),
        public=False,
        fail=None,
        archived=None,
    ):
        """``archived`` maps an issue's number to the Status its archived card holds."""
        self.options, self.items, self.issues = options, list(items), list(issues)
        self.archived = archived or {}
        self.workflows, self.linked, self.public, self.fail = workflows, linked, public, fail
        self.calls = []

    def __call__(self, *args, stdin=None):
        sent = json.loads(stdin) if stdin else None
        self.calls.append((args, sent))
        if self.fail and (self.fail in args or (sent and self.fail in sent["query"])):
            raise board.BoardError(f"gh {' '.join(args[:2])} failed: boom")
        if args[:2] == ("project", "create"):
            return json.dumps({"number": 7, "url": "https://github.com/users/o/projects/7"})
        if args[:2] == ("issue", "list"):
            return json.dumps(self.issues)
        query = sent["query"]
        if "addProjectV2ItemById" in query:
            number = int(sent["variables"]["c"].removeprefix("I"))
            had = self.archived.get(number)
            item = {"id": f"ADDED-{number}", "fieldValueByName": {"name": had} if had else None}
            return json.dumps({"data": {"addProjectV2ItemById": {"item": item}}})
        if "items(first:100" in query:
            start = int(sent["variables"]["after"] or 0)
            more = start + 100 < len(self.items)
            page = {
                "pageInfo": {"hasNextPage": more, "endCursor": str(start + 100)},
                "nodes": self.items[start : start + 100],
            }
            return json.dumps({"data": {"repositoryOwner": {"projectV2": {"items": page}}}})
        if "repositoryOwner" in query:
            project = {
                "id": "P",
                "url": "https://github.com/users/o/projects/9",
                "public": self.public,
                "field": {"id": "F", "options": self.options},
                "repositories": {"nodes": [{"nameWithOwner": name} for name in self.linked]},
                "workflows": {"nodes": list(self.workflows)},
            }
            return json.dumps({"data": {"repositoryOwner": {"projectV2": project}}})
        if "updateProjectV2Field(" in query:
            options = [
                {"id": sent_option.get("id") or "new-" + sent_option["name"], **sent_option}
                for sent_option in sent["variables"]["o"]
            ]
            reply = {"updateProjectV2Field": {"projectV2Field": {"options": options}}}
            return json.dumps({"data": reply})
        return json.dumps({"data": {}})

    def mutations(self, needle):
        return [sent for _, sent in self.calls if sent and needle in sent["query"]]

    def commands(self, *head):
        return [args for args, _ in self.calls if args[: len(head)] == head]


def run_setup(monkeypatch, fake, owner="o", number=9):
    monkeypatch.setattr(board, "gh", fake)
    lines = []
    return board.setup(REPO, owner, number, lines.append), lines


def test_option_finds_the_column():
    assert board.option(FIELDS, "Done") == ("F", "D")


def test_a_missing_column_is_named():
    with pytest.raises(board.BoardError, match="'Ready'"):
        board.option(FIELDS, "Ready")


def test_move_ends_at_the_top_of_the_column_brought_back_from_the_archive(monkeypatch):
    calls = []
    replies = {
        "issue": "https://github.com/o/r/issues/4\n",
        "item-add": json.dumps({"id": "ITEM"}),
        "view": json.dumps({"id": "PROJ"}),
        "field-list": json.dumps({"fields": FIELDS}),
    }

    def gh(*args):
        calls.append(args)
        key = args[0] if args[0] == "issue" else args[1] if args[0] == "project" else ""
        return replies.get(key, "")

    monkeypatch.setattr(board, "gh", gh)
    assert board.move(4, "Done", "o", 9) == "ITEM"
    assert calls[-1][:2] == ("api", "graphql") and "i=ITEM" in calls[-1]
    assert "unarchiveProjectV2Item" in calls[-1][3]
    assert calls[-2][-2:] == ("--single-select-option-id", "D")


def test_a_fresh_board_keeps_every_id_and_takes_the_four_in_order(monkeypatch):
    fake = FakeGh(FRESH)
    done, lines = run_setup(monkeypatch, fake, owner=None, number=None)
    assert fake.commands("project", "create")[0][-4:] == ("--title", "r", "--format", "json")
    assert lines[0].startswith("created board o/7: ") and "--number 7" in lines[0]
    (sent,) = fake.mutations("updateProjectV2Field(")
    todo, progress, done_ = FRESH
    assert sent["variables"]["o"] == [
        {**todo, "name": "Backlog"},
        {"name": "Ready", "color": "BLUE", "description": ""},
        progress,
        done_,
    ]
    assert done.created and done.number == 7
    assert done.options == ["Backlog (was Todo)", "Ready (added)"]


def test_a_named_board_with_todo_and_no_backlog_takes_the_same_mapping(monkeypatch):
    fake = FakeGh(FRESH)
    done, _ = run_setup(monkeypatch, fake)
    assert not fake.commands("project", "create") and not done.created
    (sent,) = fake.mutations("updateProjectV2Field(")
    assert [o.get("id") for o in sent["variables"]["o"]] == ["t", None, "p", "d"]


def test_an_extra_option_goes_back_after_done_with_its_id(monkeypatch):
    fake = FakeGh([choice("b", "Backlog"), choice("x", "In Review", "PINK"), choice("d", "Done")])
    done, lines = run_setup(monkeypatch, fake)
    assert lines == ["Status: Ready (added), In Progress (added); kept after Done: In Review"]
    (sent,) = fake.mutations("updateProjectV2Field(")
    assert [(o.get("id"), o["name"]) for o in sent["variables"]["o"]] == [
        ("b", "Backlog"),
        (None, "Ready"),
        (None, "In Progress"),
        ("d", "Done"),
        ("x", "In Review"),
    ]
    assert done.extras == ["In Review"]


def test_a_board_with_the_four_and_an_extra_gets_no_field_write(monkeypatch):
    fake = FakeGh([FOUR[0], choice("t", "Todo"), *FOUR[1:]])
    done, lines = run_setup(monkeypatch, fake)
    assert not fake.mutations("updateProjectV2Field(") and done.extras == ["Todo"]
    assert lines == ["Status keeps options beyond the four, where they are: Todo"]


def test_a_board_set_up_already_is_written_to_nowhere(monkeypatch):
    items = [card("A", 1, "Ready"), card("B", 2, "Done")]
    fake = FakeGh(FOUR, items=items, issues=[open_issue(1)])
    done, lines = run_setup(monkeypatch, fake)
    mutations = [sent for _, sent in fake.calls if sent and sent["query"].startswith("mutation")]
    assert mutations == [] and not fake.commands("project", "item-add")
    assert (done.written, done.linked, done.options, lines) == (0, False, [], [])


def test_an_unlinked_repository_is_linked(monkeypatch):
    fake = FakeGh(FOUR, linked=())
    done, lines = run_setup(monkeypatch, fake)
    (sent,) = fake.mutations("linkProjectV2ToRepository")
    assert sent["variables"] == {"p": "P", "r": "R"} and done.linked
    assert lines == ["linked to o/r"]


def test_each_card_takes_the_column_its_issue_state_gives(monkeypatch):
    items = [
        card("A", 1),  # open, no Status
        card("B", 2),  # closed, no Status
        card("C", 6, kind="PullRequest"),
        card("D", 7, repo="o/other"),
        card("E", 3, "Ready"),
        card("G", 5),  # open, labelled kit-gap, no Status
        card("K", 9, archived=True),  # closed, archived and still listed: left there
    ]
    issues = [
        open_issue(1),
        open_issue(3),
        open_issue(4, "bug"),  # no card yet
        open_issue(5, "kit-gap"),
        open_issue(8),  # reopened: its card was archived in Done
        open_issue(10, "kit-gap"),  # gets no card
        open_issue(11),  # its card was archived by hand from Ready
    ]
    fake = FakeGh(FOUR, items=items, issues=issues, archived={8: "Done", 11: "Ready"})
    done, lines = run_setup(monkeypatch, fake)
    added = [sent["variables"]["c"] for sent in fake.mutations("addProjectV2ItemById")]
    assert added == ["I4", "I8", "I11"]
    sets = [(sent["variables"]["i"], sent["variables"]["v"]) for sent in fake.mutations("Value(")]
    assert sets == [("ADDED-4", "b"), ("ADDED-8", "b"), ("A", "b"), ("B", "d")]
    assert lines == [
        "cards to write: 5",
        "#4: Backlog, added",
        "#8: Backlog, brought back from the archive",
        "#11: Ready, brought back from the archive",
        "#1: Backlog",
        "#2: Done",
    ]
    assert (done.written, done.left) == (5, 3)


def test_the_board_and_the_issues_are_each_read_once_whatever_their_size(monkeypatch):
    items = [card(f"I{n}", n, "Done") for n in range(1, 885)]
    issues = [open_issue(n) for n in range(781, 885)]
    fake = FakeGh(FOUR, items=items, issues=issues)
    run_setup(monkeypatch, fake)
    pages = fake.mutations("items(first:100")
    assert [sent["variables"]["after"] for sent in pages] == [None, *map(str, range(100, 900, 100))]
    (listed,) = fake.commands("issue", "list")
    assert listed[listed.index("--limit") + 1] == board.LIMIT and len(fake.calls) == 11


def test_each_workflow_is_turned_on_or_confirmed_with_its_value(monkeypatch):
    workflows = [
        {"name": "Item closed", "enabled": False},
        {"name": "Auto-add to project", "enabled": True},
    ]
    done, _ = run_setup(monkeypatch, FakeGh(FOUR, workflows=workflows))
    assert done.workflows == [
        'turn on "Item closed" with Status: Done',
        'turn on "Item added to project" with Status: Backlog',
        'confirm "Auto-add to project" is set to repository o/r and filter '
        "is:issue is:open -label:kit-gap",
        'turn on "Auto-archive items" with is:closed updated:<@today-14d',
    ]


def test_the_kickstart_names_each_workflow_setup_prints_with_its_value():
    guide = (METHOD / "project_kickstart.md").read_text(encoding="utf-8")
    for name, value in board.WORKFLOWS:
        named = (
            f"{name} → {value.removeprefix('Status: ')}" if value.startswith("Status: ") else name
        )
        assert named in guide and (value.startswith("Status: ") or f"`{value}`" in guide)


def test_a_failure_after_the_create_names_the_board_and_the_run_again(monkeypatch):
    with pytest.raises(board.BoardError) as failed:
        run_setup(monkeypatch, FakeGh(FRESH, fail="list"), owner=None, number=None)
    message = str(failed.value)
    assert "gh issue list failed: boom" in message
    assert "board o/7 is created: run lifecycle board setup --number 7 again" in message


def test_a_failure_on_a_named_board_creates_nothing_to_name(monkeypatch):
    with pytest.raises(board.BoardError) as failed:
        run_setup(monkeypatch, FakeGh(FOUR, fail="list"))
    assert "is created" not in str(failed.value)


def test_a_failed_graphql_step_is_named_after_what_it_already_wrote(monkeypatch):
    monkeypatch.setattr(board, "gh", FakeGh(FRESH, linked=(), fail="linkProjectV2"))
    lines = []
    with pytest.raises(board.BoardError) as failed:
        board.setup(REPO, "o", 9, lines.append)
    assert str(failed.value) == "linking the repository: gh api graphql failed: boom"
    assert lines == ["Status: Backlog (was Todo), Ready (added)"]


def test_a_board_the_login_cannot_read_is_named(monkeypatch):
    def gh(*args, stdin=None):
        return json.dumps({"data": {"repositoryOwner": {"projectV2": None}}})

    monkeypatch.setattr(board, "gh", gh)
    with pytest.raises(board.BoardError, match="no board o/9"):
        board.setup(REPO, "o", 9, lambda line: None)
