import json

import pytest
from lifecycle import board

FIELDS = [{"name": "Status", "id": "F", "options": [{"name": "Done", "id": "D"}]}]


def test_option_finds_the_column():
    assert board.option(FIELDS, "Done") == ("F", "D")


def test_a_missing_column_is_named():
    with pytest.raises(board.BoardError, match="'Ready'"):
        board.option(FIELDS, "Ready")


def test_move_ends_at_the_top_of_the_column(monkeypatch):
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
    assert calls[-2][-2:] == ("--single-select-option-id", "D")
