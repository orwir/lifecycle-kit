"""A repository's ``.lifecycle.toml``: what the kit needs to know about it.

The file is hand-written settings; ``.lifecycle.lock`` beside it is what
``lifecycle upgrade`` writes. An unknown key is an error, so a typo fails loudly
instead of leaving a default in force.
"""

from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

FILE = ".lifecycle.toml"
#: The lens reviewers beside base, as the method's task_review.md names them.
LENSES = {"person-facing", "model-facing"}
#: The templates a project follows, each with the file it ports into, where the settings
#: name none. A repository that names any lists every template it follows.
DEFAULT_TEMPLATES = {
    "agents_template.md": "AGENTS.md",
    "contributing_template.md": "CONTRIBUTING.md",
    "issue_template_bug.md": ".github/ISSUE_TEMPLATE/bug.md",
    "issue_template_task.md": ".github/ISSUE_TEMPLATE/task.md",
    "pr_template.md": ".github/pull_request_template.md",
}

_SCHEMA: dict[str, set[str]] = {
    "": {"branches", "board", "gate", "guides", "review", "templates"},
    "branches": {"integration", "protected"},
    "board": {"owner", "number"},
    "gate": {"commands", "targeted"},
    "guides": {"path"},
    "review": {"allow", "lenses"},
    "lens": {"paths", "read"},
}


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Lens:
    paths: tuple[str, ...] = ()
    read: tuple[str, ...] = ()


@dataclass(frozen=True)
class Config:
    root: Path
    integration: str = "develop"
    protected: str | None = "master"
    board_owner: str | None = None
    board_number: int | None = None
    gate: tuple[str, ...] = ()
    targeted: str | None = None
    guides: str = "docs/guides"
    reviewer_allow: tuple[str, ...] = ()
    lenses: dict[str, Lens] = field(default_factory=dict)
    templates: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TEMPLATES))
    #: Whether ``templates`` is the repository's own ``[templates]``, not the defaults.
    templates_named: bool = False

    @property
    def guides_dir(self) -> Path:
        return self.root / self.guides

    def as_dict(self) -> dict:
        return {
            "root": str(self.root),
            "branches": {"integration": self.integration, "protected": self.protected},
            "board": {"owner": self.board_owner, "number": self.board_number},
            "gate": {"commands": list(self.gate), "targeted": self.targeted},
            "guides": {"path": self.guides},
            "review": {
                "allow": list(self.reviewer_allow),
                "lenses": {
                    name: {"paths": list(lens.paths), "read": list(lens.read)}
                    for name, lens in self.lenses.items()
                },
            },
            "templates": dict(self.templates),
        }


def find_root(start: Path | None = None) -> Path | None:
    """The nearest directory holding ``.lifecycle.toml``, else the git top level."""
    here = (start or Path.cwd()).resolve()
    for directory in (here, *here.parents):
        if (directory / FILE).is_file():
            return directory
    result = subprocess.run(
        ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def _check_keys(table: dict, schema: str, where: str) -> None:
    unknown = set(table) - _SCHEMA[schema]
    if unknown:
        raise ConfigError(f"{FILE}: unknown key {sorted(unknown)[0]!r} in {where}")


def _strings(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{FILE}: {where} must be a list of strings")
    return tuple(value)


def _templates(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ConfigError(f"{FILE}: [templates] must be a table")
    if not value:
        raise ConfigError(
            f"{FILE}: [templates] is empty: omit the table to follow the project templates"
        )
    for name, target in value.items():
        if isinstance(target, dict):
            raise ConfigError(
                f"{FILE}: [templates] {name!r} is a table: quote each file name, "
                'as in "idea_gauntlet.md" = "AGENTS.md"'
            )
        if not isinstance(target, str) or not target.strip():
            raise ConfigError(f"{FILE}: [templates] {name!r} must name the file it ports into")
    return dict(value)


def parse(data: dict, root: Path) -> Config:
    _check_keys(data, "", "the top level")
    for section in ("branches", "board", "gate", "guides", "review"):
        if section in data:
            if not isinstance(data[section], dict):
                raise ConfigError(f"{FILE}: [{section}] must be a table")
            _check_keys(data[section], section, f"[{section}]")
    branches = data.get("branches", {})
    board = data.get("board", {})
    gate = data.get("gate", {})
    review = data.get("review", {})
    lenses = {}
    for name, table in review.get("lenses", {}).items():
        if name not in LENSES:
            raise ConfigError(f"{FILE}: unknown lens {name!r}; the method's are {sorted(LENSES)}")
        _check_keys(table, "lens", f"[review.lenses.{name}]")
        lenses[name] = Lens(
            paths=_strings(table.get("paths", []), f"[review.lenses.{name}] paths"),
            read=_strings(table.get("read", []), f"[review.lenses.{name}] read"),
        )
    named = "templates" in data
    templates = _templates(data["templates"]) if named else dict(DEFAULT_TEMPLATES)
    if bool(board.get("owner")) != bool(board.get("number")):
        raise ConfigError(f"{FILE}: [board] needs both owner and number")
    return Config(
        root=root,
        integration=branches.get("integration", "develop"),
        protected=branches.get("protected", "master") or None,
        board_owner=board.get("owner"),
        board_number=board.get("number"),
        gate=_strings(gate.get("commands", []), "[gate] commands"),
        targeted=gate.get("targeted"),
        guides=data.get("guides", {}).get("path", "docs/guides"),
        reviewer_allow=_strings(review.get("allow", []), "[review] allow"),
        lenses=lenses,
        templates=templates,
        templates_named=named,
    )


def load(start: Path | None = None) -> Config | None:
    """The repository's settings, or None when it has no ``.lifecycle.toml``."""
    root = find_root(start)
    if root is None or not (root / FILE).is_file():
        return None
    try:
        data = tomllib.loads((root / FILE).read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{FILE}: {error}") from error
    return parse(data, root)
