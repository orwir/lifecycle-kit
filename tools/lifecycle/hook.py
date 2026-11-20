"""Agent hook entry points: a JSON event on stdin, a verdict back.

The event shape is Claude Code's (``tool_input.command``, ``agent_type``, ``cwd``);
another agent's adapter maps its own events onto it. Two guards hold every session
on this kit and one holds only the reviewer, which a plugin agent cannot carry in
its own definition: its hook fires here, named by ``agent_type``.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import doctor, readonly
from .config import ConfigError, load

# The plugin-scoped name Claude Code's docs give a plugin subagent's events; a live
# session has not shown it yet, so the guard rests on the docs until one does.
REVIEWER = "lifecycle:reviewer"
#: The same name found in an event that cannot be parsed, so the guard still fails closed.
REVIEWER_EVENT = re.compile(rb'"agent_type"\s*:\s*"lifecycle:reviewer"')

HERESTRING = """\
BLOCKED: a PowerShell here-string (@'...'@ or @"..."@) in a Bash command.

Bash has no here-strings: the @ passes through as a literal character, so the command
succeeds with a corrupted argument instead of failing. For a multi-line string use a
heredoc with the terminator at column 0, or write the text to a file with the Write tool
and pass its path."""

CD_ABSOLUTE = """\
BLOCKED: the command starts with `cd <absolute path>`.

The shell already starts in the repository root. Drop the prefix and use repo-relative
paths; a command that acts on another directory names it as an argument (`git -C <dir>`,
`ls <dir>`) instead of changing into it."""

_HERESTRING_OPEN = re.compile(r"@(['\"])\r?\n")
_CD_ABSOLUTE = re.compile(r"\s*cd\s+['\"]?(/|~|[A-Za-z]:[/\\])")


def _herestring(command: str) -> bool:
    opened = _HERESTRING_OPEN.search(command)
    return bool(opened) and re.search(r"\n" + opened.group(1) + "@", command) is not None


def pre_bash(event: dict) -> str | None:
    """Why the command is blocked, or None to let it run."""
    command = event.get("tool_input", {}).get("command", "")
    if _herestring(command):
        return HERESTRING
    if _CD_ABSOLUTE.match(command):
        return CD_ABSOLUTE
    if event.get("agent_type") != REVIEWER:
        return None
    try:
        config = load(Path(event.get("cwd") or "."))
    except ConfigError as error:
        return f"BLOCKED for the reviewer: {error}"
    reason = readonly.check(command, config.reviewer_allow if config else ())
    return f"BLOCKED for the reviewer: {reason}" if reason else None


def session_start(event: dict) -> str:
    """What the session should know before its first task, or nothing."""
    try:
        config = load(Path(event.get("cwd") or "."))
    except ConfigError as error:
        return f"lifecycle kit: {error}"
    if config is None:
        return ""
    findings = doctor.check(config)
    if not findings:
        return ""
    lines = [f"- {finding.message}" for finding in findings]
    return "lifecycle kit, before the next task:\n" + "\n".join(lines)
