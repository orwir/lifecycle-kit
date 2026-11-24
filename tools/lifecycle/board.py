"""The project board: a card put in a column, at its top; a board set up in one pass.

Projects v2 has no created-date sort, so a column's order is the raw position the
API last set: every move ends by putting the card at the top. The card is added
first when the issue is not on the board yet, so the same command files a new
issue into Backlog, and brought back where it was archived. Ready is left out on
purpose: moving a card there is the maintainer's triage call, and its order is the
plan.

Setup writes the Status options in one call that replaces the whole list: an option
sent without its id is a new option, and every card that held the old one loses its
Status, which also empties each built-in workflow that set it. So every existing
option goes back with its id. No API creates or turns on a workflow, or reads its
value, so setup names the ones to make or confirm in the web UI.

Setup gives an open issue's card the column its plan says: In Progress once the plan
has a status, since the clarify skill moves the card there before it writes one, and
Backlog otherwise. A card that already holds a Status was someone's call and keeps it,
save one archived in Done whose issue is open again, which takes that issue's column;
one left in Backlog under a plan with a status is collected for the maintainer to move.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field

from .gap import LABEL

FIELD = "Status"
COLUMNS = ("Backlog", "In Progress", "Done")
STATUSES = ("Backlog", "Ready", "In Progress", "Done")
COLORS = {"Backlog": "GRAY", "Ready": "BLUE", "In Progress": "YELLOW", "Done": "GREEN"}
#: A fresh board's first option, which setup renames to Backlog, keeping its id.
FRESH = "Todo"
#: The built-in workflows a board keeps on, each with the value or filter it holds.
WORKFLOWS = (
    ("Item closed", "Status: Done"),
    ("Item added to project", "Status: Backlog"),
    ("Auto-add to project", f"is:issue is:open -label:{LABEL}"),
    ("Auto-archive items", "is:closed updated:<@today-14d"),
)
#: Past a project's cap of 50,000 items, so no list of open issues is cut short.
LIMIT = "50001"
#: A plan's status, whatever follows it; the templates' slot, `proposed | accepted …`, is none.
_STATUS = re.compile(r"\*\*Status:\*\*\s*(?:proposed|accepted)\b(?!\s*\|)")
_PLANNED = "its plan has a status"

_UNARCHIVE = "unarchiveProjectV2Item(input:{projectId:$p,itemId:$i}){clientMutationId}"
_TO_TOP = (
    f"mutation($p:ID!,$i:ID!){{{_UNARCHIVE} "
    "updateProjectV2ItemPosition(input:{projectId:$p,itemId:$i,afterId:null}){clientMutationId}}"
)
_PROJECT = """query($o:String!,$n:Int!){repositoryOwner(login:$o){... on ProjectV2Owner{
projectV2(number:$n){id url public
field(name:"Status"){... on ProjectV2SingleSelectField{id options{id name color description}}}
repositories(first:100){nodes{nameWithOwner}}
workflows(first:50){nodes{name enabled}}}}}}"""
# An archived card drops out of this list once its archive settles; one that still shows
# carries its flag, which `gh project item-list` does not give.
_ITEMS = """query($o:String!,$n:Int!,$after:String){repositoryOwner(login:$o){
... on ProjectV2Owner{projectV2(number:$n){items(first:100,after:$after){
pageInfo{hasNextPage endCursor}
nodes{id isArchived
fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}}
content{__typename
... on Issue{number url repository{nameWithOwner}}
... on PullRequest{number url repository{nameWithOwner}}}}}}}}}"""
_OPTIONS = """mutation($f:ID!,$o:[ProjectV2SingleSelectFieldOptionInput!]!){
updateProjectV2Field(input:{fieldId:$f,singleSelectOptions:$o}){
projectV2Field{... on ProjectV2SingleSelectField{options{id name}}}}}"""
_LINK = """mutation($p:ID!,$r:ID!){
linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){clientMutationId}}"""
_VALUE = """updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,
value:{singleSelectOptionId:$v}}){clientMutationId}"""
_SET = f"mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){{{_VALUE}}}"
# Adding an issue whose card is archived brings that card back, with its Status kept.
_ADD = """mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){
item{id fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}}}}}"""


class BoardError(Exception):
    pass


def gh(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["gh", *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise BoardError(f"gh {' '.join(args[:2])} failed: {result.stderr.strip()}")
    return result.stdout


def graphql(step: str, query: str, **variables: object) -> dict:
    """``query``'s data; a failure names ``step``, since every call is `gh api graphql`."""
    body = json.dumps({"query": query, "variables": variables})
    try:
        return json.loads(gh("api", "graphql", "--input", "-", stdin=body))["data"]
    except BoardError as error:
        raise BoardError(f"{step}: {error}") from error


def option(fields: list[dict], column: str) -> tuple[str, str]:
    """The Status field's id and the id of ``column``'s option in it."""
    for found in fields:
        if found.get("name") == FIELD:
            for choice in found.get("options", []):
                if choice["name"] == column:
                    return found["id"], choice["id"]
            raise BoardError(
                f"the board's {FIELD} field has no {column!r} option: lifecycle board setup adds it"
            )
    raise BoardError(f"the board has no {FIELD} field")


def move(issue: int, column: str, owner: str, number: int) -> str:
    """Put ``issue`` in ``column`` at the top, adding it to the board if needed; the item id."""
    board = ("--owner", owner, "--format", "json")
    url = gh("issue", "view", str(issue), "--json", "url", "-q", ".url").strip()
    item = json.loads(gh("project", "item-add", str(number), "--url", url, *board))["id"]
    project_id = json.loads(gh("project", "view", str(number), *board))["id"]
    fields = json.loads(gh("project", "field-list", str(number), *board))["fields"]
    field_id, option_id = option(fields, column)
    gh(
        "project", "item-edit", "--id", item, "--project-id", project_id,
        "--field-id", field_id, "--single-select-option-id", option_id,
    )  # fmt: skip
    gh("api", "graphql", "-f", f"query={_TO_TOP}", "-f", f"p={project_id}", "-f", f"i={item}")
    return item


def planned(body: str | None) -> bool:
    """Whether an issue's ``body`` holds a plan with a status: the issue is past Clarify.

    Only a `**Status:**` line in the `## Plan` section counts, so a capture made from a
    template, which carries the heading and its slot, is no plan.
    """
    inside = False
    for line in (body or "").splitlines():
        if line.startswith("## "):
            inside = line.rstrip() == "## Plan"
        elif inside and _STATUS.match(line):
            return True
    return False


def _sent(choice: dict, name: str | None = None) -> dict:
    return {
        "id": choice["id"],
        "name": name or choice["name"],
        "color": choice["color"],
        "description": choice.get("description") or "",
    }


def statuses(existing: list[dict]) -> tuple[list[dict] | None, list[str]]:
    """The option list to write, or None where all four are there; the options kept beyond them.

    The four come first, in the board's order, each with its id where it has one, and a
    fresh board's Todo becomes Backlog wherever Backlog is missing. Every other option
    goes back after Done, as it is.
    """
    by_name = {choice["name"]: choice for choice in existing}
    renamed = FRESH in by_name and "Backlog" not in by_name
    if renamed:
        by_name["Backlog"] = by_name.pop(FRESH)
    kept = {by_name[name]["id"] for name in STATUSES if name in by_name}
    extras = [choice for choice in existing if choice["id"] not in kept]
    if not renamed and all(name in by_name for name in STATUSES):
        return None, [choice["name"] for choice in extras]
    written = [
        _sent(by_name[name], name)
        if name in by_name
        else {"name": name, "color": COLORS[name], "description": ""}
        for name in STATUSES
    ]
    return written + [_sent(choice) for choice in extras], [choice["name"] for choice in extras]


@dataclass
class Setup:
    owner: str
    number: int
    url: str
    created: bool = False
    options: list[str] = field(default_factory=list)
    extras: list[str] = field(default_factory=list)
    linked: bool = False
    written: int = 0
    left: int = 0
    workflows: list[str] = field(default_factory=list)
    public: bool = True
    #: Issues whose card setup left in Backlog though their plan has a status.
    parked: list[int] = field(default_factory=list)


def setup(
    repo: dict,
    owner: str | None,
    number: int | None,
    report: Callable[[str], None] = print,
) -> Setup:
    """Create the board where ``number`` is None, then make it hold; what it did.

    ``repo`` is ``gh repo view``'s JSON: id, nameWithOwner, name, owner, visibility.
    Each step reads before it writes, so a run again after a stop resumes.
    """
    owner = owner or repo["owner"]["login"]
    created = number is None
    if number is None:
        made = json.loads(
            gh("project", "create", "--owner", owner, "--title", repo["name"], "--format", "json")
        )
        number = int(made["number"])
        report(
            f"created board {owner}/{number}: {made['url']} "
            f"(a run that stops: lifecycle board setup --number {number})"
        )
    try:
        done = _hold(repo, owner, number, report)
    except BoardError as error:
        if created:
            raise BoardError(
                f"{error} (board {owner}/{number} is created: "
                f"run lifecycle board setup --number {number} again)"
            ) from error
        raise
    done.created = created
    return done


def _items(owner: str, number: int) -> list[dict]:
    """The board's cards, a page of 100 at a time."""
    found: list[dict] = []
    after = None
    while True:
        data = graphql("reading the board's cards", _ITEMS, o=owner, n=number, after=after)
        page = data["repositoryOwner"]["projectV2"]["items"]
        for node in page["nodes"]:
            content = node.get("content") or {}
            found.append(
                {
                    "id": node["id"],
                    "archived": node["isArchived"],
                    "status": (node.get("fieldValueByName") or {}).get("name"),
                    "type": content.get("__typename"),
                    "url": content.get("url"),
                    "number": content.get("number"),
                    "repository": (content.get("repository") or {}).get("nameWithOwner"),
                }
            )
        if not page["pageInfo"]["hasNextPage"]:
            return found
        after = page["pageInfo"]["endCursor"]


def _hold(repo: dict, owner: str, number: int, report: Callable[[str], None]) -> Setup:
    project = graphql("reading the board", _PROJECT, o=owner, n=number)["repositoryOwner"]
    project = (project or {}).get("projectV2")
    if not project:
        raise BoardError(f"no board {owner}/{number}, or the gh login cannot read it")
    status = project.get("field")
    if not status:
        raise BoardError(f"board {owner}/{number} has no {FIELD} field")
    done = Setup(owner, number, project["url"], public=project["public"])

    written, done.extras = statuses(status["options"])
    choices = status["options"]
    if written is not None:
        reply = graphql("writing the Status options", _OPTIONS, f=status["id"], o=written)
        choices = reply["updateProjectV2Field"]["projectV2Field"]["options"]
        was = {choice["id"]: choice["name"] for choice in status["options"]}
        for choice in written[: len(STATUSES)]:
            before = was.get(choice.get("id"))
            if not before:
                done.options.append(f"{choice['name']} (added)")
            elif before != choice["name"]:
                done.options.append(f"{choice['name']} (was {before})")
        kept = f"; kept after Done: {', '.join(done.extras)}" if done.extras else ""
        report(f"Status: {', '.join(done.options)}{kept}")
    elif done.extras:
        report(f"Status keeps options beyond the four, where they are: {', '.join(done.extras)}")
    ids = {choice["name"]: choice["id"] for choice in choices}

    linked = {node["nameWithOwner"] for node in project["repositories"]["nodes"]}
    if repo["nameWithOwner"] not in linked:
        graphql("linking the repository", _LINK, p=project["id"], r=repo["id"])
        done.linked = True
        report(f"linked to {repo['nameWithOwner']}")

    items = [item for item in _items(owner, number) if not item["archived"]]
    issues = json.loads(
        gh(
            "issue", "list", "--repo", repo["nameWithOwner"], "--state", "open",
            "--limit", LIMIT, "--json", "id,url,number,labels,body",
        )
    )  # fmt: skip
    gapped = {i["url"] for i in issues if any(label["name"] == LABEL for label in i["labels"])}
    open_urls = {i["url"] for i in issues if i["url"] not in gapped}
    under_way = {i["url"] for i in issues if i["url"] in open_urls and planned(i.get("body"))}
    on_board = {item["url"] for item in items}

    def column(url: str) -> str:
        """The column an issue with no Status takes; In Progress says why on its line."""
        if url not in open_urls:
            return "Done"
        return "In Progress" if url in under_way else "Backlog"

    def why(target: str) -> str:
        return f" ({_PLANNED})" if target == "In Progress" else ""

    # An open issue with no card listed is added: a card archived after its close comes
    # back in the column its plan gives, a card archived from another column where it was.
    missing = [i for i in issues if i["url"] in open_urls and i["url"] not in on_board]
    unset: list[tuple[str, str, int]] = []  # (column, card, issue) for a card with no Status
    for item in items:
        ours = item["type"] == "Issue" and item["repository"] == repo["nameWithOwner"]
        if item["status"]:
            if item["status"] == "Backlog" and item["url"] in under_way:
                done.parked.append(item["number"])
            continue
        if not ours or item["url"] in gapped:
            done.left += 1
        else:
            unset.append((column(item["url"]), item["id"], item["number"]))

    if missing or unset:
        report(f"cards to write: {len(missing) + len(unset)}")
    for issue in missing:
        step = f"adding #{issue['number']}"
        added = graphql(step, _ADD, p=project["id"], c=issue["id"])["addProjectV2ItemById"]["item"]
        had = (added.get("fieldValueByName") or {}).get("name")
        done.written += 1
        if had and had != "Done":
            if had == "Backlog" and issue["url"] in under_way:
                done.parked.append(issue["number"])
            report(f"#{issue['number']}: {had}, brought back from the archive")
            continue
        target = column(issue["url"])
        step = f"putting #{issue['number']} in {target}"
        graphql(step, _SET, p=project["id"], i=added["id"], f=status["id"], v=ids[target])
        verb = "brought back from the archive" if had else "added"
        report(f"#{issue['number']}: {target}, {verb}{why(target)}")
    for target, card, issue_number in unset:
        step = f"putting #{issue_number} in {target}"
        graphql(step, _SET, p=project["id"], i=card, f=status["id"], v=ids[target])
        done.written += 1
        report(f"#{issue_number}: {target}{why(target)}")

    enabled = {node["name"]: node["enabled"] for node in project["workflows"]["nodes"]}
    for name, value in WORKFLOWS:
        if name == "Auto-add to project":
            value = f"repository {repo['nameWithOwner']} and filter {value}"
        verb = f'confirm "{name}" is set to' if enabled.get(name) else f'turn on "{name}" with'
        done.workflows.append(f"{verb} {value}")
    return done
