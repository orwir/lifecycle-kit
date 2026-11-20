"""The ``lifecycle`` command."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from . import KIT_ROOT, board, doctor, guard, guides, hook, kit_version
from .config import Config, ConfigError, load


def _config() -> Config:
    config = load()
    if config is None:
        raise ConfigError("no .lifecycle.toml here or above: this repository is not on the kit")
    return config


def _doctor(args: argparse.Namespace) -> int:
    findings = doctor.check(_config())
    for finding in findings:
        print(f"{finding.level}: {finding.message}")
    if not findings:
        print(f"on kit {kit_version()}, nothing to do")
    blocked = any(finding.level == doctor.BLOCK for finding in findings)
    return 1 if args.require_current and blocked else 0


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
    templates = [name for name in changed if name in guides.TEMPLATES]
    if templates and not args.dry_run:
        paths = " ".join(f"{config.guides}/{name}" for name in templates)
        print(
            "templates changed: port what applies into this repository's own files "
            f"(git diff -- {paths}; a template new to this repository is read whole)"
        )
    return 0


def _guides(args: argparse.Namespace) -> int:
    config = _config()
    if args.action == "check":
        lock = guides.read_lock(config.root)
        edits = guides.local_edits(config, lock) if lock else []
        print("\n".join(edits) if edits else "no guide edits")
        return 0
    pushed, new = guides.push(config, args.message)
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


def _guard(args: argparse.Namespace) -> int:
    config = _config()
    if not config.protected:
        return 0
    if args.which == "push":
        return guard.push(config.protected, sys.stdin if not sys.stdin.isatty() else [])
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY")
    sha = args.sha or os.environ.get("GITHUB_SHA")
    if not repo or not sha:
        raise ConfigError("--repo and --sha are required outside GitHub Actions")
    return guard.deploy(config.protected, repo, sha)


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
    p.add_argument("--require-current", action="store_true", help="exit 1 when a round must wait")
    p = sub.add_parser("upgrade", help="pin this repository's guides to the installed kit")
    p.add_argument("--adopt", action="store_true", help="take over guides with no recorded source")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("guides", help="this repository's guide edits: list them, or push them")
    p.add_argument("action", choices=("check", "push"))
    p.add_argument("-m", "--message", help="the kit commit's one line: what changed and why")
    p = sub.add_parser("board", help="put an issue's card in a board column, at the top")
    p.add_argument("issue", type=int)
    p.add_argument("column", choices=board.COLUMNS)
    p = sub.add_parser("guard", help="the protected branch's push and deploy guards")
    p.add_argument("which", choices=("push", "deploy"))
    p.add_argument("--repo")
    p.add_argument("--sha")
    p = sub.add_parser("hook", help="an agent hook: the event as JSON on stdin")
    p.add_argument("event", choices=("pre-bash", "session-start"))
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "guides" and args.action == "push" and not args.message:
        parser().error("guides push needs --message")
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
            print(json.dumps(_config().as_dict(), indent=2))
            return 0
        handler = {
            "doctor": _doctor,
            "upgrade": _upgrade,
            "guides": _guides,
            "board": _board,
            "guard": _guard,
            "hook": _hook,
        }[args.command]
        return handler(args)
    except (ConfigError, guides.GuidesError, board.BoardError) as error:
        print(f"lifecycle: {error}", file=sys.stderr)
        return 1
