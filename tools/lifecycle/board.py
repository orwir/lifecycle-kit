"""Put an issue's card in a column of the project board, at the top of it.

Projects v2 has no created-date sort, so a column's order is the raw position the
API last set: every move ends by putting the card at the top. The card is added
first when the issue is not on the board yet, so the same command files a new
issue into Backlog. Ready is left out on purpose: moving a card there is the
maintainer's triage call, and its order is the release plan.
"""

from __future__ import annotations

import json
import subprocess

FIELD = "Status"
COLUMNS = ("Backlog", "In Progress", "Done")

_TO_TOP = (
    "mutation($p:ID!,$i:ID!){updateProjectV2ItemPosition("
    "input:{projectId:$p,itemId:$i,afterId:null}){clientMutationId}}"
)


class BoardError(Exception):
    pass


def gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode != 0:
        raise BoardError(f"gh {' '.join(args[:2])} failed: {result.stderr.strip()}")
    return result.stdout


def option(fields: list[dict], column: str) -> tuple[str, str]:
    """The Status field's id and the id of ``column``'s option in it."""
    for found in fields:
        if found.get("name") == FIELD:
            for choice in found.get("options", []):
                if choice["name"] == column:
                    return found["id"], choice["id"]
            raise BoardError(f"the board's {FIELD} field has no {column!r} option")
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
