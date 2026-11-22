import re
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "method" / "agents_template.md"
TOKEN = re.compile(r"\{\{([^{}]+?)\}\}")


def named(text):
    """The tokens a repository fills by name: not a choice (`a | b`) or an example (`e.g., …`)."""
    return {t for t in TOKEN.findall(text) if "|" not in t and not t.startswith("e.g.")}


def missing(template):
    """The named tokens of a template's body that its *Placeholder reference* has no row for."""
    body = template.split("````\n")[1]
    reference = template.split("## Placeholder reference")[1].split("\n---\n")[0]
    cells = [line.split("|")[1] for line in reference.splitlines() if line.startswith("|")]
    return named(body) - {t for cell in cells for t in named(cell)}


def test_every_named_token_in_the_agents_template_has_a_reference_row():
    assert missing(AGENTS.read_text(encoding="utf-8")) == set()


def test_a_token_with_no_row_is_found_and_choices_and_examples_need_none():
    template = (
        "````\nRun `{{TEST_CMD}}` and `{{NEW_CMD}}`, {{a | b}}, in {{e.g., `src/`}}.\n````\n"
        "## Placeholder reference\n\n| Token | Example |\n|---|---|\n"
        "| `{{TEST_CMD}}` | `pytest` |\n\n---\n"
    )
    assert missing(template) == {"NEW_CMD"}
