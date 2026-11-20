"""Whether a shell command only reads: the reviewer's guard.

The reviewer reads a tree the developer is still working in, so a command that
writes a file, moves a ref or takes a lock can corrupt the work under review.
Only what is recognised passes. Refused: anything the shell would rewrite before
running (``$VAR``, ``$(...)``, backticks, ``{a,b}``; a glob is fine), a redirection
anywhere but ``/dev/null`` or another descriptor, and every unknown command. The
reason tells the reviewer how to read the same thing another way.
Modelled on the first adoption's command guard, reduced to the reviewer's rule.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Sequence

GIT_READ = {
    "blame", "cat-file", "describe", "diff", "for-each-ref", "grep", "log", "ls-files",
    "ls-tree", "merge-base", "name-rev", "range-diff", "rev-list", "rev-parse", "shortlog",
    "show", "status",
}  # fmt: skip
GIT_LISTS = {"worktree": "list", "stash": "list"}
GH_READ = {
    "issue": {"view", "list"},
    "pr": {"view", "diff", "list", "checks"},
    "run": {"view", "list"},
    "repo": {"view"},
}
READERS = {
    "basename", "cat", "cmp", "comm", "cut", "diff", "dirname", "du", "echo", "false", "file",
    "grep", "head", "ls", "nl", "printf", "pwd", "realpath", "rg", "stat", "tail", "test",
    "tr", "tree", "true", "wc", "which",
}  # fmt: skip
ENV_OK = {"PYTHONUTF8", "LC_ALL", "LANG", "NO_COLOR", "PAGER", "GIT_PAGER", "TERM"}
FIND_WRITES = {
    "-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fprintf", "-fls",
}  # fmt: skip
_SAFE_TARGET = re.compile(r">?[ \t]*(/dev/null|&\d)(?=[\s|;&)]|$)")
_FD = re.compile(r"(^|\s)\d$")
_SED_PRINT = re.compile(r"^(\d+|\$)(,(\d+|\$))?p$")
_ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")

SUBSTITUTION = (
    "the shell would rewrite this before it runs ($VAR, $(...), backticks, <(...), {a,b}): "
    "write the command out literally, with a literal $ or brace inside single quotes"
)
HEREDOC = "no heredocs: read a file with Read, or an older version with `git show <rev>:<path>`"
WRITE_REDIRECT = "no redirection into a file: the reviewer writes nothing"
UNKNOWN = (
    "the reviewer runs only commands that read: git's read commands, gh issue/pr view, plain "
    "readers (cat, head, grep, ls, find without -exec) and the repository's own checks in "
    ".lifecycle.toml [review] allow. Read the same thing another way; a refusal is not a finding"
)


def _scan(command: str) -> tuple[list[str], str | None]:
    """Split on unquoted ``|``, ``&&``, ``||``, ``;``, ``&`` and newlines.

    Refuses substitutions and heredocs, and drops the redirections that write
    nothing (``2>/dev/null``, ``2>&1``); any other output redirection is refused.
    """
    segments, current, quote, i = [], "", None, 0
    while i < len(command):
        char = command[i]
        if quote == "'":
            quote = None if char == "'" else quote
        elif char == "\\":
            current += command[i : i + 2]
            i += 2
            continue
        elif char in "$`":
            return [], SUBSTITUTION
        elif quote == '"':
            quote = None if char == '"' else quote
        elif char in "'\"":
            quote = char
        elif char == "{":
            return [], SUBSTITUTION
        elif command.startswith("<<", i):
            return [], HEREDOC
        elif command.startswith(("<(", ">("), i):
            return [], SUBSTITUTION
        elif char == ">" or command.startswith("&>", i):
            safe = _SAFE_TARGET.match(command, i + (2 if char == "&" else 1))
            if not safe:
                return [], WRITE_REDIRECT
            current = _FD.sub(r"\1", current)
            i = safe.end()
            continue
        elif char in "|;&\n":
            segments.append(current)
            current = ""
            i += 2 if char in "|&" and command[i + 1 : i + 2] == char else 1
            continue
        current += char
        i += 1
    segments.append(current)
    return [segment.strip() for segment in segments if segment.strip()], None


def _words(segment: str) -> tuple[list[str], str | None]:
    kept = shlex.split(segment, posix=True)
    while kept and (match := _ASSIGNMENT.match(kept[0])):
        if match.group(1) not in ENV_OK:
            return [], UNKNOWN
        kept.pop(0)
    return kept, None


def _git(args: list[str]) -> bool:
    while args and args[0].startswith("-"):
        flag = args.pop(0)
        if flag == "-C" and args:
            args.pop(0)
        elif flag not in {"--no-pager", "-P", "--no-optional-locks"}:
            return False
    if not args:
        return False
    sub, rest = args[0], args[1:]
    if any(_long_flag(arg, "--output", "--ext-diff") for arg in rest):
        return False
    if sub == "grep" and any(
        _short_flag(arg, "O") or _long_flag(arg, "--open-files-in-pager") for arg in rest
    ):
        return False
    if sub in GIT_LISTS:
        return rest[:1] == [GIT_LISTS[sub]]
    return sub in GIT_READ


def _short_flag(arg: str, flag: str) -> bool:
    """``arg`` is a cluster of short options holding ``flag`` (``-ro`` holds ``o``)."""
    return arg.startswith("-") and not arg.startswith("--") and flag in arg


def _long_flag(arg: str, *options: str) -> bool:
    """``arg`` names one of ``options`` in full or by the prefix getopt and git accept."""
    name = arg.split("=", 1)[0]
    if not name.startswith("--") or len(name) < 4:
        return False
    return any(option == name or option.startswith(name) for option in options)


def _gh(args: list[str]) -> bool:
    return len(args) >= 2 and args[1] in GH_READ.get(args[0], set())


def _reader(name: str, args: list[str]) -> bool:
    if name == "lifecycle":
        reads = (["config"], ["doctor"], ["version"], ["where"], ["upgraded"])
        return args[:1] in reads or args[:2] == ["guides", "check"]
    if name == "find":
        return not FIND_WRITES.intersection(args)
    if name == "sed":
        return len(args) >= 2 and args[0] == "-n" and bool(_SED_PRINT.match(args[1]))
    if name == "sort":
        return not any(
            _short_flag(arg, "o") or _long_flag(arg, "--output", "--compress-program")
            for arg in args
        )
    if name == "rg":
        return not any(arg.startswith("--pre") for arg in args)
    if name == "tree":
        return not any(_short_flag(arg, "o") or _long_flag(arg, "--output") for arg in args)
    if name == "uniq":
        return len([arg for arg in args if not arg.startswith("-")]) <= 1
    return name in READERS


def _allowed_extra(segment: str, allow: Sequence[str]) -> bool:
    normal = " ".join(segment.split())
    return any(normal == entry or normal.startswith(entry + " ") for entry in allow)


def check(command: str, allow: Sequence[str] = ()) -> str | None:
    """None when every part of ``command`` only reads; otherwise why it is refused."""
    segments, reason = _scan(command)
    if reason:
        return reason
    for segment in segments:
        if _allowed_extra(segment, allow):
            continue
        try:
            words, reason = _words(segment)
        except ValueError:
            return "an unclosed quote: write the command out again"
        if reason:
            return reason
        if not words:
            continue
        name = words[0].replace("\\", "/").rsplit("/", 1)[-1].removesuffix(".exe")
        ok = (
            _git(words[1:])
            if name == "git"
            else _gh(words[1:])
            if name == "gh"
            else _reader(name, words[1:])
        )
        if not ok:
            return UNKNOWN
    return None
