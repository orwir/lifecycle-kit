"""The ``lifecycle`` command."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from . import KIT_ROOT, board, doctor, guides, hook, kit_version, latest, ship
from .config import Config, ConfigError, load


def _config() -> Config:
    config = load()
    if config is None:
        raise ConfigError("no .lifecycle.toml here or above: this repository is not on the kit")
    return config


def _doctor(args: argparse.Namespace) -> int:
    findings = doctor.check(_config(), latest=latest.latest_release())
    if args.json:
        print(json.dumps([finding.as_dict() for finding in findings], indent=2, ensure_ascii=False))
    for finding in [] if args.json else findings:
        print(f"{finding.level}: {finding.message}")
        for detail in finding.details:
            print(f"  - {detail}")
    if not findings and not args.json:
        print(f"on kit {kit_version()}, nothing to do")
    return 0


def _upgraded(args: argparse.Namespace) -> int:
    found = doctor.upgraded(_config(), args.base)
    if args.json:
        print(json.dumps(found, indent=2, ensure_ascii=False))
    elif found is None:
        print("no upgrade the integration branch lacks")
    else:
        print(f"kit {found['from'] or 'none'} -> {found['to']}")
        for change in found["changes"]:
            print(f"  - {change}")
        print("required of this repository:" + ("" if found["required"] else " none"))
        for step in found["required"]:
            print(f"  - {step}")
        print("guides rewritten: " + (", ".join(found["guides"]) or "none"))
        print("guides deleted: " + (", ".join(found["deleted"]) or "none"))
        print("templates installed whole: " + (", ".join(found["installed"]) or "none"))
    return 0


def _upgrade(args: argparse.Namespace) -> int:
    config = _config()
    changed = guides.upgrade(config, adopt=args.adopt, dry_run=args.dry_run)
    verb = "would change" if args.dry_run else "changed"
    print(f"kit {kit_version()}: {verb} {len(changed)} guide file(s) in {config.guides}")
    for name in changed:
        print(f"  {name}")
    lock = guides.read_lock(config.root)
    carried = guides.local_edits(config, lock) if lock and not args.dry_run else []
    if carried:
        print(
            "carried onto the new release, still to push at their task's Complete: "
            + ", ".join(carried)
        )
    if changed.installed:
        verb = "would install" if args.dry_run else "installed"
        print(f"{verb} unchanged from the old template: " + ", ".join(changed.installed))
    mapping = config.templates
    templates = [
        name for name in changed if name in mapping and mapping[name] not in changed.installed
    ]
    if templates and not args.dry_run:
        ports = ", ".join(f"{name} -> {mapping[name]}" for name in templates)
        paths = " ".join(f"{config.guides}/{name}" for name in templates)
        print(
            f"templates changed: port what applies into this repository's own files: {ports} "
            f"(git diff -- {paths}; a template new to this repository is read whole)"
        )
    return 0


def _message_file(path: str) -> tuple[str, str]:
    """A guide push's line and reason, from a file: no shell rewrites a file, where an
    inline argument loses its backticks, ``$`` or second line."""
    try:
        body = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise guides.GuidesError(f"cannot read the message file {path}: {error}") from error
    line, _, rest = body.partition("\n")
    if rest.split("\n", 1)[0].strip():
        raise guides.GuidesError(
            f"{path}: the line is the file's first line alone, and a blank line comes before "
            "the reason"
        )
    return line.strip(), rest


def _guides(args: argparse.Namespace) -> int:
    config = _config()
    if args.action == "check":
        lock = guides.read_lock(config.root)
        edits = guides.local_edits(config, lock) if lock else []
        print("\n".join(edits) if edits else "no guide edits")
        return 0
    pushed, new = guides.push(config, *_message_file(args.file))
    if not pushed:
        print("no guide edits to push")
        return 0
    print(
        f"pushed {', '.join(pushed)} as kit v{new}. Commit .lifecycle.lock with the task; "
        "this repository's next upgrade waits until the installed kit has that release."
    )
    return 0


def _board(args: argparse.Namespace) -> int:
    config = _config()
    if not config.board_owner:
        raise ConfigError(".lifecycle.toml has no [board]: this repository tracks no board")
    item = board.move(args.issue, args.column, config.board_owner, config.board_number)
    print(f"#{args.issue}: {args.column}, top of the column ({item})")
    return 0


def _release(args: argparse.Namespace) -> int:
    config = _config()
    if not config.release_workflow:
        raise ConfigError(
            ".lifecycle.toml names no [release] workflow: this repository ships no release by it"
        )
    resolved = subprocess.run(
        ["git", "-C", str(config.root), "rev-parse", "--verify", f"{args.commit}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if resolved.returncode != 0:
        raise ConfigError(f"{args.commit} is not a commit in this repository")
    ref = args.ref or config.integration
    code, line = ship.release(config.release_workflow, ref, resolved.stdout.strip())
    print(f"release: {line}", file=sys.stdout if code == ship.SHIPPED else sys.stderr)
    return code


def _hook(args: argparse.Namespace) -> int:
    raw = sys.stdin.buffer.read()
    if args.event == "pre-bash":
        try:
            reason = hook.pre_bash(json.loads(raw.decode("utf-8") or "{}"))
        except Exception as error:  # a broken guard lets a session run, never the reviewer
            if not hook.REVIEWER_EVENT.search(raw):
                print(f"lifecycle hook: {error}", file=sys.stderr)
                return 0
            reason = f"BLOCKED for the reviewer: the guard failed ({error})"
        if reason:
            print(reason, file=sys.stderr)
            return 2
        return 0
    text = hook.session_start(json.loads(raw.decode("utf-8") or "{}"))
    if text:
        print(text)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="lifecycle", description=__doc__)
    root.add_argument("-C", dest="directory", help="run as if started in this directory")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="the installed kit's release")
    sub.add_parser("where", help="the installed kit's folder, which holds agents/ and method/")
    sub.add_parser("config", help="this repository's .lifecycle.toml, resolved, as JSON")
    p = sub.add_parser("doctor", help="what this repository needs before its next task")
    p.add_argument("--json", action="store_true", help="the findings as JSON, each with its fix")
    p = sub.add_parser("upgraded", help="the upgrade the tree holds that has not landed, if any")
    p.add_argument("--json", action="store_true")
    p.add_argument("--base", help="measure from this commit (default: the flow's base)")
    p = sub.add_parser("upgrade", help="pin this repository's guides to the installed kit")
    p.add_argument("--adopt", action="store_true", help="take over guides with no recorded source")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("guides", help="this repository's guide edits: list them, or push them")
    p.add_argument("action", choices=("check", "push"))
    p.add_argument(
        "-F",
        "--file",
        help="the push's message file: its first line the kit commit's subject and changelog "
        "entry (what changed, one claim), then a blank line and the reason, the commit's body",
    )
    # Points a guides copy from before 0.6.0, which still says -m, at -F; goes at the next major.
    p.add_argument("-m", "--message", help=argparse.SUPPRESS)
    p = sub.add_parser("board", help="put an issue's card in a board column, at the top")
    p.add_argument("issue", type=int)
    p.add_argument("column", choices=board.COLUMNS)
    p = sub.add_parser("release", help="ship a reviewed commit by the release workflow, watched")
    p.add_argument("commit", help="the head the release review read")
    p.add_argument("--ref", help="the branch to dispatch on (default: the integration branch)")
    p = sub.add_parser("hook", help="an agent hook: the event as JSON on stdin")
    p.add_argument("event", choices=("pre-bash", "session-start"))
    return root


def _utf8_streams() -> None:
    """Agents read the output as UTF-8; Windows writes piped output in its ANSI page."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    _utf8_streams()
    args = parser().parse_args(argv)
    if args.command == "guides" and args.message is not None:
        parser().error(
            "guides push takes its message as a file now: -F <file>, the line, a blank line, "
            "then the reason"
        )
    if args.command == "guides" and args.action == "push" and not args.file:
        parser().error("guides push needs --file (-F): the line, a blank line, then the reason")
    if args.directory:
        os.chdir(args.directory)
    try:
        if args.command == "version":
            print(kit_version())
            return 0
        if args.command == "where":
            print(KIT_ROOT.as_posix())
            return 0
        if args.command == "config":
            print(json.dumps(_config().as_dict(), indent=2, ensure_ascii=False))
            return 0
        handler = {
            "doctor": _doctor,
            "upgraded": _upgraded,
            "upgrade": _upgrade,
            "guides": _guides,
            "board": _board,
            "release": _release,
            "hook": _hook,
        }[args.command]
        return handler(args)
    except (ConfigError, guides.GuidesError, board.BoardError, ship.ReleaseError) as error:
        print(f"lifecycle: {error}", file=sys.stderr)
        return 1
