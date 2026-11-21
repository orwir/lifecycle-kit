"""The kit's changelog style, and the one reader of its release sections.

Each entry is one claim of at most ``CAP`` characters before its ``(#N)``, and a release
groups its entries once each under Added, Changed, Fixed and Removed, below a
``## [<version>] — <date>`` heading (``method/project_kickstart.md`` § CHANGELOG style).
``UPGRADING.md`` takes the same headings, so one reader walks both files.

A lone dash or a semicolon is how a second claim gets welded on, while a pair of dashes
encloses an aside, so an odd count of spaced dashes is the signal.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import release

CAP = 120
GROUPS = ("Added", "Changed", "Fixed", "Removed")

#: The release heading, and the bare ``## v<version>`` an older kit's guide push writes.
HEADING = re.compile(
    r"^## (?:\[(?P<dated>\d+\.\d+\.\d+)\] — \d{4}-\d{2}-\d{2}|v(?P<bare>\d+\.\d+\.\d+))\s*$"
)
_REF = re.compile(r"\s*\(#\d+(?:, #\d+)*\)$")
_DASH = re.compile(r"\s[-\N{EN DASH}\N{EM DASH}]\s")
_ISSUE = re.compile(r"(?<![\w/])#(\d+)")
#: The forms GitHub links as an issue, so the forms a closing keyword reaches. A colour
#: (``#1f2937``) or an anchor on a file name (``SKILL.md#2-guides``) is not one; a folder
#: before it (``complete/SKILL.md#2``) reads as ``owner/repo#N``, refused with the match quoted.
_LINKED_ISSUE = re.compile(
    r"(?<![\w/])#\d+\b|[\w.-]+/[\w.-]+#\d+\b|\bGH-\d+\b"
    r"|github\.com/[^/\s]+/[^/\s]+/(?:issues|pull)/\d+",
    re.I,
)


def heading(version: str, day: str) -> str:
    return f"## [{version}] — {day}"


def release_of(line: str) -> str | None:
    """The release a heading line opens, or None for any other line."""
    found = HEADING.match(line)
    return (found.group("dated") or found.group("bare")) if found else None


def entry_violations(entry: str) -> list[str]:
    """What breaks the style in one entry, given without its leading ``- ``."""
    ref = _REF.search(entry)
    claim = entry[: ref.start()] if ref else entry
    found = []
    if len(claim) > CAP:
        found.append(f"{len(claim)} characters, over the cap of {CAP}")
    if ";" in claim or len(_DASH.findall(claim)) % 2:
        found.append("a second claim welded on by a semicolon or a dash")
    return found


def violations(section: list[str]) -> list[str]:
    """What breaks the style in one release's lines, its heading left out."""
    found: list[str] = []
    seen: list[str] = []
    for line in section:
        if line.startswith("### "):
            group = line[4:].strip()
            if group not in GROUPS:
                found.append(f"{group}: not one of {', '.join(GROUPS)}")
            elif group in seen:
                found.append(f"{group}: a second block, where one per release collects them")
            seen.append(group)
        elif line.startswith("- "):
            if not seen:
                found.append(f"in no group: {line[2:]}")
            found.extend(f"{why}: {line[2:]}" for why in entry_violations(line[2:]))
    return found


def issue_named(text: str) -> str | None:
    """The first issue ``text`` names in a form GitHub links (``#N``, ``owner/repo#N``,
    ``GH-N`` or a link), which a guide push's words may not carry, or None."""
    found = _LINKED_ISSUE.search(text)
    return found.group(0) if found else None


def qualify(entry: str, repository: str) -> str:
    """``#N`` written as ``<repository>#N``, so it names the kit's issue wherever it is read."""
    return _ISSUE.sub(lambda m: f"{repository}#{m.group(1)}", entry)


def sections(path: Path, after: str, upto: str) -> list[tuple[str, list[str]]]:
    """Each release after ``after`` up to ``upto`` with its entries, in the file's order.

    Any ``## `` line ends a release's entries, so a heading in another shape drops its
    own entries rather than lending them to the release above it. A missing file has none.
    """
    if not path.is_file():
        return []
    found: list[tuple[str, list[str]]] = []
    taking = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            version = release_of(line)
            taking = bool(version) and release(after) < release(version) <= release(upto)
            if taking:
                found.append((version, []))
            continue
        if taking and line.startswith("- "):
            found[-1][1].append(line[2:])
    return found
