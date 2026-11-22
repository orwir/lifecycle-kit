"""The ``lifecycle`` command."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence

from . import KIT_ROOT, METHOD, board, doctor, guides, hook, kit_version, ship
from .config import Config, ConfigError, load


def _config() -> Config:
    config = load()
    if config is None:
        raise ConfigError("no .lifecycle.toml here or above: this repository is not on the kit")
    return config


def _doctor(args: argparse.Namespace) -> int:
    findings = doctor.check(_config())
    if args.json:
        print(json.dumps([finding.as_dict() for finding in findings], indent=2, ensure_ascii=False))
    for finding in [] if args.json else findings:
        print(f"{finding.level}: {finding.message}")
        for detail in finding.details:
            print(f"  - {detail}")
    if not findings and not args.json:
        print(f"on kit {kit_version()}, nothing to do")
    return 0


def _upgrade(args: argparse.Namespace) -> int:
    config = _config()
    changes = guides.upgrade(config, adopt=args.adopt, dry_run=args.dry_run)
    print(f"kit {changes.before} -> {changes.after}{' (dry run)' if args.dry_run else ''}")
    if changes.deleted:
        verb = "would delete" if args.dry_run else "deleted"
        print(f"{verb} the kit's copy in {config.guides}: " + ", ".join(changes.deleted))
    if changes.kept:
        verb = "would keep" if args.dry_run else "kept"
        print(
            f"{verb}, named like the kit's but not its text, to compare with the kit's: "
            + ", ".join(f"{config.guides}/{name}" for name in changes.kept)
        )
    if changes.installed:
        verb = "would replace" if args.dry_run else "replaced"
        print(
            f"{verb} with the new template, unchanged since the old: "
            + ", ".join(changes.installed)
        )
    for port in changes.ports:
        if port.diff:
            print(f"port {port.name} -> {port.target}, by what the template changed:")
            print(port.diff, end="" if port.diff.endswith("\n") else "\n")
        else:
            print(
                f"port {port.name} -> {port.target}, read whole: {(METHOD / port.name).as_posix()}"
            )
    if not (changes.deleted or changes.kept or changes.installed or changes.ports):
        print("nothing to change beyond the lock")
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
    p = sub.add_parser(
        "upgrade",
        help="templates and lock to the installed kit; the upgrade skill runs it",
    )
    p.add_argument(
        "--adopt",
        action="store_true",
        help="a first move: deletes each guide that is the kit's text, keeps the rest named "
        "like the kit's (--dry-run lists both)",
    )
    p.add_argument("--dry-run", action="store_true")
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
            "upgrade": _upgrade,
            "board": _board,
            "release": _release,
            "hook": _hook,
        }[args.command]
        return handler(args)
    except (ConfigError, guides.GuidesError, board.BoardError, ship.ReleaseError) as error:
        print(f"lifecycle: {error}", file=sys.stderr)
        return 1
