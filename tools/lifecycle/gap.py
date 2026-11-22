"""File a gap a task finds in one of the kit's guides where its finder can write.

On the kit, for one who can push to the repository the kit's manifest names. Anywhere
else in the repository the task runs in, labelled ``kit-gap``, where the kit's maintainer
can lift it onto the kit if they can read that repository. Either way the issue is in the
kit's words, naming nothing of the repository, so it can be lifted as it is.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import is_kit, kit_repository
from .config import Config

LABEL = "kit-gap"
LABEL_COLOR = "d4c5f9"
LABEL_DESCRIPTION = (
    "A gap in a lifecycle kit guide, in the kit's words, for the kit's maintainer to lift"
)
#: A read that gives no answer in this long fails, so a stalled network leaves the gap
#: unfiled at once. The filing has no limit, and only a refusal of it reads as nothing filed:
#: one that may have gone through is never reported unfiled, so it is not filed twice.
CALL_SECONDS = 60
_ISSUE_URL = re.compile(r"https://\S+/issues/(\d+)")
_REFUSED = re.compile(r"HTTP 4\d\d")


class GapError(Exception):
    pass


class Uncertain(GapError):
    """The filing failed in a way that does not show nothing was filed."""


@dataclass(frozen=True)
class Filed:
    reference: str
    url: str
    label: str | None


def gh(*args: str, cwd: Path, filing: bool = False) -> str:
    """``gh``'s output, or the reason nothing was filed. The filing runs with no time limit,
    and a failure of it that GitHub did not refuse raises ``Uncertain``."""
    command = " ".join(args[:2])
    timeout = None if filing else CALL_SECONDS
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            cwd=cwd,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise GapError("no issue filed: gh is not installed") from error
    except subprocess.TimeoutExpired as error:
        raise GapError(f"no issue filed: gh {command} gave no answer in {timeout} s") from error
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if filing and not _REFUSED.search(stderr):
            raise Uncertain(f"gh {command} failed: {stderr}")
        raise GapError(f"no issue filed: gh {command} failed: {stderr}")
    return result.stdout


def can_push(kit: str, cwd: Path) -> bool:
    return gh("api", f"repos/{kit}", "--jq", ".permissions.push", cwd=cwd).strip() == "true"


def has_label(repository: str, cwd: Path) -> bool:
    """Whether ``repository`` has the label, by a search: a plain list reads only the oldest
    30 labels. GitHub matches label names without case."""
    listed = gh(
        "label", "list", "--repo", repository, "--search", LABEL, "--limit", "100",
        "--json", "name", cwd=cwd,
    )  # fmt: skip
    return any(found.get("name", "").casefold() == LABEL for found in json.loads(listed or "[]"))


def file(config: Config, title: str, body_file: Path) -> Filed:
    """File the gap ``body_file`` holds, titled ``title``: on the kit where the signed-in
    ``gh`` user can push to it, otherwise in this repository with the label, created where
    it is missing. The reference is the one a brief names: the kit's ``owner/name#M`` outside
    a checkout of the kit, a bare ``#M`` in the repository the task runs in."""
    if not body_file.is_file():
        raise GapError(f"no issue filed: {body_file} is not a file")
    root, kit = config.root, kit_repository()
    if can_push(kit, root):
        target, label = kit, None
    else:
        target = gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner", cwd=root)
        target, label = target.strip(), LABEL
        if not has_label(target, root):
            gh(
                "label", "create", LABEL, "--repo", target, "--color", LABEL_COLOR,
                "--description", LABEL_DESCRIPTION, cwd=root,
            )  # fmt: skip
    create = ["issue", "create", "--repo", target, "--title", title, "--body-file", str(body_file)]
    check = f"the issue may be filed anyway: read {target}'s issues before filing again"
    try:
        printed = gh(*create, *(["--label", label] if label else []), cwd=root, filing=True)
    except Uncertain as error:
        raise GapError(f"{error}; {check}") from error
    found = _ISSUE_URL.search(printed)
    if not found:
        raise GapError(
            f"gh issue create printed no issue link ({printed.strip() or 'nothing'}); {check}"
        )
    qualified = target == kit and not is_kit(root)
    return Filed(
        reference=f"{kit}#{found.group(1)}" if qualified else f"#{found.group(1)}",
        url=found.group(0),
        label=label,
    )
