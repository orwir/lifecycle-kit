"""Agent hook entry points: a JSON event on stdin, a verdict back.

The event shape is Claude Code's (``tool_input.command``, ``agent_type``, ``cwd``);
another agent's adapter maps its own events onto it. The one guard here holds only the
reviewer, which a plugin agent cannot carry in its own definition: its hook fires here,
named by ``agent_type``. Every other session's commands pass.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import doctor, readonly
from .config import ConfigError, load

# The plugin-scoped name Claude Code gives a plugin subagent's events, as its docs say;
# a live session showed it on 2026-11-21, when the guard refused a reviewer's command.
REVIEWER = "lifecycle:reviewer"
#: The same name found in an event that cannot be parsed, so the guard still fails closed.
REVIEWER_EVENT = re.compile(rb'"agent_type"\s*:\s*"lifecycle:reviewer"')


def pre_bash(event: dict) -> str | None:
    """Why the command is blocked, or None to let it run."""
    if event.get("agent_type") != REVIEWER:
        return None
    command = event.get("tool_input", {}).get("command", "")
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
    lines = []
    for finding in findings:
        lines.append(f"- {finding.message}")
        lines.extend(f"  - {detail}" for detail in finding.details)
    return "lifecycle kit:\n" + "\n".join(lines)
