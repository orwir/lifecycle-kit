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


def open_issue(number, *labels, body=""):
    """An open issue as `gh issue list --json id,url,number,labels,body` gives it."""
    return {
        "id": f"I{number}",
        "url": issue(number),
        "number": number,
        "labels": [{"name": label} for label in labels],
        "body": body,
    }


def plan(status):
    """An issue body whose plan's Status line reads ``status``."""
    return (
        f"## Goal\n\nA goal.\n\n## Plan\n\nAdded at Clarify.\n\n**Status:** {status}\n\n"
        "### Behaviour\n"
    )


PLANNED = plan("accepted 2026-11-24")
# A capture made from a template in the web UI: the plan's heading, intro and slot.
CAPTURED = plan("proposed | accepted YYYY-MM-DD")


def view(number, name, layout="BOARD_LAYOUT", columns=("Status",)):
    """A view as the board query returns it; ``columns`` names its column field, if any."""
    fields = {"nodes": [{"name": column} for column in columns]}
    return {"number": number, "name": name, "layout": layout, "verticalGroupByFields": fields}


# What `gh project create` leaves, and a board whose views are set up.
FRESH_VIEWS = [view(1, "View 1", "TABLE_LAYOUT", ())]
SET_UP = [view(1, "Table", "TABLE_LAYOUT", ()), view(2, "Board")]
#: The Status field's id as the REST API names fields.
STATUS_ID = 42


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
        views=SET_UP,
        kind="User",
    ):
        """``archived`` maps an issue's number to the Status its archived card holds."""
        self.options, self.items, self.issues = options, list(items), list(issues)
        self.archived = archived or {}
        self.workflows, self.linked, self.public, self.fail = workflows, linked, public, fail
        self.views, self.kind = list(views), kind
        self.calls = []

    def __call__(self, *args, stdin=None):
        sent = json.loads(stdin) if stdin else None
        self.calls.append((args, sent))
        query = (sent or {}).get("query", "")
        if self.fail and (self.fail in args or self.fail in query):
            raise board.BoardError(f"gh {' '.join(args[:2])} failed: boom")
        if args[:2] == ("project", "create"):
            return json.dumps({"number": 7, "url": "https://github.com/users/o/projects/7"})
        if args[:2] == ("issue", "list"):
            return json.dumps(self.issues)
        if args[0] == "api" and args[1].endswith("/views"):
            number = len(self.views) + 1
            self.views.append(view(number, sent["name"]))
            url = f"https://github.com/users/o/projects/{args[1].split('/')[3]}/views/{number}"
            return json.dumps({"number": number, "name": sent["name"], "html_url": url})
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
                "url": f"https://github.com/users/o/projects/{sent['variables']['n']}",
                "public": self.public,
                "field": {"id": "F", "databaseId": STATUS_ID, "options": self.options},
                "repositories": {"nodes": [{"nameWithOwner": name} for name in self.linked]},
                "workflows": {"nodes": list(self.workflows)},
                "views": {"nodes": list(self.views)},
            }
            owner = {"__typename": self.kind, "projectV2": project}
            return json.dumps({"data": {"repositoryOwner": owner}})
        if "updateProjectV2Field(" in query:
            options = [
                {"id": sent_option.get("id") or "new-" + sent_option["name"], **sent_option}
                for sent_option in sent["variables"]["o"]
            ]
            reply = {"updateProjectV2Field": {"projectV2Field": {"options": options}}}
            return json.dumps({"data": reply})
        return json.dumps({"data": {}})

    def mutations(self, needle):
        return [sent for _, sent in self.calls if sent and needle in sent.get("query", "")]

    def commands(self, *head):
        return [args for args, _ in self.calls if args[: len(head)] == head]

    def made_views(self):
        """Each REST call that makes a view, with the body it sent."""
        return [(args, sent) for args, sent in self.calls if args[1].endswith("/views")]


def run_setup(monkeypatch, fake, owner="o", number=9):
    monkeypatch.setattr(board, "gh", fake)
    lines = []
    return board.setup(REPO, owner, number, lines.append), lines


def test_option_finds_the_column():
    assert board.option(FIELDS, "Done") == ("F", "D")


def test_a_missing_column_is_named():
    with pytest.raises(board.BoardError, match="'Ready'"):
        board.option(FIELDS, "Ready")


def board_card(id_, status, project="P", archived=False):
    """One of an issue's cards as its `projectItems` list it."""
    value = {"name": status} if status else None
    return {
        "id": id_,
        "isArchived": archived,
        "project": {"id": project},
        "fieldValueByName": value,
    }


class MoveGh:
    """`gh` as a move calls it, on board P whose Status options are the four."""

    def __init__(self, cards=None, missing=(), fail=None, options=FOUR):
        """``cards`` maps an issue's number to its cards; ``missing`` names no issue."""
        self.cards, self.missing, self.fail, self.options = cards or {}, set(missing), fail, options
        self.calls = []

    def __call__(self, *args, stdin=None):
        sent = json.loads(stdin) if stdin else None
        self.calls.append((args, sent))
        query = (sent or {}).get("query", "")
        if self.fail and (self.fail in args or self.fail in query):
            raise board.BoardError(f"gh {' '.join(args[:2])} failed: boom")
        if args[:2] == ("issue", "view"):
            if int(args[2]) in self.missing:
                raise board.BoardError("gh issue view failed: no issue")
            return issue(int(args[2])) + "\n"
        if args[:2] == ("project", "item-add"):
            return json.dumps({"id": "ITEM-" + args[args.index("--url") + 1].rsplit("/", 1)[1]})
        if args[:2] == ("project", "view"):
            return json.dumps({"id": "P"})
        if args[:2] == ("project", "field-list"):
            return json.dumps({"fields": [{"name": "Status", "id": "F", "options": self.options}]})
        if "resource(url:" in query:
            number = int(sent["variables"]["u"].rsplit("/", 1)[1])
            nodes = self.cards.get(number, [])
            return json.dumps({"data": {"resource": {"projectItems": {"nodes": nodes}}}})
        return json.dumps({"data": {}})

    def writes(self):
        """Every call that changes the board: a card added, a Status set, a place."""
        return [
            args
            for args, sent in self.calls
            if args[:2] in (("project", "item-add"), ("project", "item-edit"))
            or (sent and sent["query"].startswith("mutation"))
        ]

    def places(self):
        """Each card placed, with the card it was placed after (None for the top)."""
        return [
            (sent["variables"]["i"], sent["variables"]["a"])
            for _, sent in self.calls
            if sent and "updateProjectV2ItemPosition" in sent["query"]
        ]


def run_move(monkeypatch, fake, issues, column, after=None):
    monkeypatch.setattr(board, "gh", fake)
    lines = []
    return board.move(issues, column, "o", 9, after, lines.append), lines


def test_one_card_goes_to_the_top_brought_back_from_the_archive(monkeypatch):
    fake = MoveGh()
    items, lines = run_move(monkeypatch, fake, [4], "Done")
    assert items == ["ITEM-4"] and fake.places() == [("ITEM-4", None)]
    (edit,) = [args for args, _ in fake.calls if args[:2] == ("project", "item-edit")]
    assert edit[-2:] == ("--single-select-option-id", "d")
    (placed,) = [sent for _, sent in fake.calls if sent]
    assert "unarchiveProjectV2Item" in placed["query"]
    assert lines == ["#4: Done, top of the column (ITEM-4)"]


def test_cards_take_ready_in_the_order_given_from_its_top(monkeypatch):
    fake = MoveGh()
    items, lines = run_move(monkeypatch, fake, [12, 7, 9], "Ready")
    assert items == ["ITEM-12", "ITEM-7", "ITEM-9"]
    edits = [args for args, _ in fake.calls if args[:2] == ("project", "item-edit")]
    assert [args[-1] for args in edits] == ["r", "r", "r"]
    assert fake.places() == [("ITEM-12", None), ("ITEM-7", "ITEM-12"), ("ITEM-9", "ITEM-7")]
    assert lines == [
        "#12: Ready, top of the column (ITEM-12)",
        "#7: Ready, after #12 (ITEM-7)",
        "#9: Ready, after #7 (ITEM-9)",
    ]


def test_after_places_the_first_card_right_after_the_one_named(monkeypatch):
    # #4 has a card on another board too, listed first: only this board's counts.
    fake = MoveGh(cards={4: [board_card("Q4", "Backlog", project="Q"), board_card("C4", "Ready")]})
    _, lines = run_move(monkeypatch, fake, [12, 7], "Ready", after=4)
    assert fake.places() == [("ITEM-12", "C4"), ("ITEM-7", "ITEM-12")]
    assert lines == ["#12: Ready, after #4 (ITEM-12)", "#7: Ready, after #12 (ITEM-7)"]


@pytest.mark.parametrize(
    ("cards", "says"),
    [
        ([board_card("C4", "Backlog")], "--after 4: its card is in Backlog, not Ready"),
        ([board_card("C4", None)], "--after 4: its card is in no column, not Ready"),
        (
            [board_card("C4", "Ready", archived=True)],
            "--after 4: its card is archived, not in Ready",
        ),
        ([board_card("Q4", "Ready", project="Q")], "--after 4: #4 has no card on the board"),
        ([], "--after 4: #4 has no card on the board"),
    ],
    ids=["another column", "no column", "archived", "another board only", "no card"],
)
def test_a_card_to_follow_outside_the_column_writes_nothing(monkeypatch, cards, says):
    fake = MoveGh(cards={4: cards})
    with pytest.raises(board.BoardError) as refused:
        run_move(monkeypatch, fake, [12, 7], "Ready", after=4)
    assert str(refused.value) == says and fake.writes() == []


def test_a_number_naming_no_issue_writes_nothing(monkeypatch):
    fake = MoveGh(missing={8})
    with pytest.raises(board.BoardError) as refused:
        run_move(monkeypatch, fake, [12, 8, 9], "Ready")
    assert str(refused.value) == "reading #8: gh issue view failed: no issue"
    assert fake.writes() == []


def test_a_board_with_no_such_column_writes_nothing(monkeypatch):
    fake = MoveGh(options=[choice("b", "Backlog"), choice("d", "Done")])
    with pytest.raises(board.BoardError, match="no 'Ready' option"):
        run_move(monkeypatch, fake, [12], "Ready")
    assert fake.writes() == []


#: What a failed move ends with: the run that finishes the order.
AGAIN = "; the cards before it are placed, and the same command again makes the whole order"


@pytest.mark.parametrize(
    ("fail", "says"),
    [
        (issue(7), f"moving #7 to Ready: gh project item-add failed: boom{AGAIN}"),
        ("ITEM-7", f"moving #7 to Ready: gh project item-edit failed: boom{AGAIN}"),
    ],
)
def test_a_failure_partway_keeps_the_cards_before_it_and_a_run_again_makes_the_order(
    monkeypatch, fail, says
):
    fake = MoveGh(fail=fail)
    lines = []
    monkeypatch.setattr(board, "gh", fake)
    with pytest.raises(board.BoardError) as failed:
        board.move([12, 7, 9], "Ready", "o", 9, None, lines.append)
    assert str(failed.value) == says
    assert fake.places() == [("ITEM-12", None)] and lines == [
        "#12: Ready, top of the column (ITEM-12)"
    ]
    fake.fail, fake.calls = None, []
    run_move(monkeypatch, fake, [12, 7, 9], "Ready")
    assert fake.places() == [("ITEM-12", None), ("ITEM-7", "ITEM-12"), ("ITEM-9", "ITEM-7")]


def test_a_failed_place_names_its_card_and_step(monkeypatch):
    fake = MoveGh(fail="updateProjectV2ItemPosition")
    with pytest.raises(board.BoardError) as failed:
        run_move(monkeypatch, fake, [12], "Ready")
    assert str(failed.value) == (
        f"moving #12 to Ready: placing the card: gh api graphql failed: boom{AGAIN}"
    )


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
    assert not fake.made_views() and done.view is None and done.rename is None


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


@pytest.mark.parametrize(
    "body",
    [
        PLANNED,
        plan("proposed"),
        plan("proposed, plan round 2026-11-24: 3 required, 3 folded"),
        plan("accepted 2026-11-24 (plan round skipped: no shape; nothing to answer)"),
        PLANNED.replace("\n", "\r\n"),
        PLANNED.replace("\n", "\r\r\n"),
    ],
)
def test_a_plan_with_a_status_is_read_whatever_follows_it_and_whatever_the_line_ends(body):
    assert board.planned(body)


@pytest.mark.parametrize(
    "body",
    [
        None,
        "",
        CAPTURED,
        CAPTURED.replace("\n", "\r\n"),
        "## Goal\n\nA goal.\n\n## Plan\n\nAdded at Clarify.\n",
        "## Context\n\n**Status:** accepted 2026-11-24\n\n## Plan\n\nAdded at Clarify.\n",
        "## Plan\n\nAdded at Clarify.\n\n## Notes\n\n**Status:** accepted 2026-11-24\n",
        "## Plan when picked up\n\n**Status:** accepted 2026-11-24\n",
    ],
)
def test_no_plan_a_template_s_slot_or_a_status_outside_the_plan_is_no_plan(body):
    assert not board.planned(body)


@pytest.mark.parametrize("name", ["issue_template_task.md", "issue_template_bug.md"])
def test_a_capture_made_from_either_template_is_no_plan(name):
    text = (METHOD / name).read_text(encoding="utf-8")
    assert "\n## Plan\n" in text and "\n**Status:** " in text
    assert not board.planned(text) and not board.planned(text.replace("\n", "\r\n"))


def test_an_issue_past_clarify_takes_in_progress_wherever_setup_writes_its_card(monkeypatch):
    items = [card("A", 1), card("B", 2)]  # no Status: 1 planned, 2 closed
    issues = [
        open_issue(1, body=PLANNED),
        open_issue(3, body=PLANNED.replace("\n", "\r\n")),  # no card yet
        open_issue(4, body=CAPTURED),  # no card yet
        open_issue(8, body=PLANNED),  # reopened: its card was archived in Done
    ]
    fake = FakeGh(FOUR, items=items, issues=issues, archived={8: "Done"})
    done, lines = run_setup(monkeypatch, fake)
    sets = [(sent["variables"]["i"], sent["variables"]["v"]) for sent in fake.mutations("Value(")]
    assert sets == [("ADDED-3", "p"), ("ADDED-4", "b"), ("ADDED-8", "p"), ("A", "p"), ("B", "d")]
    assert lines == [
        "cards to write: 5",
        "#3: In Progress, added (its plan has a status)",
        "#4: Backlog, added",
        "#8: In Progress, brought back from the archive (its plan has a status)",
        "#1: In Progress (its plan has a status)",
        "#2: Done",
    ]
    assert done.written == 5


def test_a_card_held_in_backlog_under_a_plan_is_collected_and_left_there(monkeypatch):
    items = [card("A", 1, "Backlog"), card("C", 3, "Ready"), card("D", 4, "Backlog")]
    issues = [
        open_issue(1, body=PLANNED),
        open_issue(3, body=PLANNED),
        open_issue(4, body=CAPTURED),
        open_issue(5, body=PLANNED),  # its card was archived from Backlog
    ]
    fake = FakeGh(FOUR, items=items, issues=issues, archived={5: "Backlog"})
    done, lines = run_setup(monkeypatch, fake)
    assert fake.mutations("Value(") == []
    # The header counts the lines below it: a card left in Backlog is collected, not written.
    assert lines == ["cards to write: 1", "#5: Backlog, brought back from the archive"]
    assert (done.written, done.parked) == (1, [1, 5])


def test_the_board_and_the_issues_are_each_read_once_whatever_their_size(monkeypatch):
    items = [card(f"I{n}", n, "Done") for n in range(1, 885)]
    issues = [open_issue(n) for n in range(781, 885)]
    fake = FakeGh(FOUR, items=items, issues=issues)
    run_setup(monkeypatch, fake)
    pages = fake.mutations("items(first:100")
    assert [sent["variables"]["after"] for sent in pages] == [None, *map(str, range(100, 900, 100))]
    (listed,) = fake.commands("issue", "list")
    assert listed[listed.index("--limit") + 1] == board.LIMIT and len(fake.calls) == 11
    assert "body" in listed[listed.index("--json") + 1].split(",")


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


MADE = "made the Board view, its columns the Status options: https://github.com/users/o/projects"


def test_a_created_board_gets_a_board_view_on_status_after_its_cards(monkeypatch):
    fake = FakeGh(FRESH, issues=[open_issue(1)], views=FRESH_VIEWS)
    done, lines = run_setup(monkeypatch, fake, owner=None, number=None)
    ((args, sent),) = fake.made_views()
    assert args == ("api", "users/o/projectsV2/7/views", "--method", "POST", "--input", "-")
    assert sent == {"name": "Board", "layout": "board", "vertical_group_by": [STATUS_ID]}
    last_card = max(
        i for i, (_, s) in enumerate(fake.calls) if s and "Value(" in s.get("query", "")
    )
    assert fake.calls.index((args, sent)) > last_card
    assert lines[-2:] == ["#1: Backlog, added", f"{MADE}/7/views/2"]
    assert done.view == "https://github.com/users/o/projects/7/views/2"


def test_a_fresh_view_1_is_named_to_rename(monkeypatch):
    done, _ = run_setup(monkeypatch, FakeGh(FOUR, views=FRESH_VIEWS))
    assert done.rename == "https://github.com/users/o/projects/9/views/1"


@pytest.mark.parametrize(
    "views",
    [
        [
            view(1, "View 1", "TABLE_LAYOUT", ()),
            view(2, "Table", "TABLE_LAYOUT", ()),
            view(3, "Board"),
        ],
        [view(1, "View 1", columns=("Status",))],  # a board view, though it kept the name
        SET_UP,
    ],
)
def test_a_board_with_a_table_view_names_no_rename(monkeypatch, views):
    done, _ = run_setup(monkeypatch, FakeGh(FOUR, views=views))
    assert done.rename is None


def test_a_named_board_with_no_status_board_view_gets_one(monkeypatch):
    fake = FakeGh(FOUR, views=[view(1, "Table", "TABLE_LAYOUT", ())])
    done, lines = run_setup(monkeypatch, fake)
    ((args, _),) = fake.made_views()
    assert args[1] == "users/o/projectsV2/9/views" and lines == [f"{MADE}/9/views/2"]
    assert done.rename is None


@pytest.mark.parametrize("columns", [("Effort",), ()], ids=["another field", "no column field"])
def test_a_board_view_on_another_field_or_none_does_not_count(monkeypatch, columns):
    fake = FakeGh(
        FOUR, views=[view(1, "Table", "TABLE_LAYOUT", ()), view(2, "Mine", columns=columns)]
    )
    done, _ = run_setup(monkeypatch, fake)
    ((_, sent),) = fake.made_views()
    assert sent["name"] == "Board" and done.view.endswith("/views/3")
    # A run again finds the view it made, on Status, and makes none.
    run_setup(monkeypatch, fake)
    assert len(fake.made_views()) == 1


def test_an_organization_s_board_takes_the_organization_path(monkeypatch):
    fake = FakeGh(FOUR, views=[], kind="Organization")
    run_setup(monkeypatch, fake)
    ((args, _),) = fake.made_views()
    assert args[1] == "orgs/o/projectsV2/9/views"


def test_a_failed_view_names_its_path_and_the_view_by_hand_after_the_cards(monkeypatch):
    fake = FakeGh(
        FRESH, issues=[open_issue(1)], views=FRESH_VIEWS, fail="users/o/projectsV2/7/views"
    )
    monkeypatch.setattr(board, "gh", fake)
    lines = []
    with pytest.raises(board.BoardError) as failed:
        board.setup(REPO, None, None, lines.append)
    assert str(failed.value) == (
        "making the Board view: gh api users/o/projectsV2/7/views failed: boom; "
        "make one by hand at https://github.com/users/o/projects/7, a board layout whose "
        "columns are Status, then run setup again "
        "(board o/7 is created: run lifecycle board setup --number 7 again)"
    )
    assert lines[-1] == "#1: Backlog, added"


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
