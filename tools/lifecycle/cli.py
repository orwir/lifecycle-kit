"""The ``lifecycle`` command."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from . import (
    KIT_ROOT,
    METHOD,
    board,
    doctor,
    gap,
    guides,
    home,
    hook,
    kit_repository,
    kit_version,
    ship,
)
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


def _gap(args: argparse.Namespace) -> int:
    filed = gap.file(_config(), args.title, Path(args.body_file).resolve())
    line = f"filed {filed.reference} {filed.url}"
    if filed.label:
        line += (
            f", labelled {filed.label}: the signed-in gh account cannot push to {kit_repository()}"
        )
    print(line)
    return 0


def _home(args: argparse.Namespace) -> int:
    folder = Path(args.folder or ".").resolve()
    if args.check:
        print(json.dumps(home.check(folder if args.folder else None), indent=2, ensure_ascii=False))
        return 0
    if args.github:
        folder = home.containing(folder) or folder
    if args.github and not home.is_home(folder):
        _, why = home.gh_login(home.nearest(folder))
        if why:
            raise home.HomeError(f"nothing written or created: {why}")
    made = home.setup(folder)
    if made.made:
        print(f"set up the ideas home in {made.folder}, committed: {', '.join(made.committed)}")
    elif not args.github:
        print(f"{made.folder} is an ideas home already: nothing written")
    if args.github:
        backup = home.backup(folder, args.github)
        if backup.created:
            print(f"backed up to {backup.url}, a new private repository, main pushed")
        elif backup.pushed:
            print(f"pushed main to {backup.url}: nothing created")
        else:
            print(f"backed up already: main is on {backup.url} as it is here, nothing created")
    return 0


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
    p = sub.add_parser(
        "gap",
        help="file a gap in a kit guide: on the kit where you can push to it, otherwise here, "
        f"labelled {gap.LABEL}",
    )
    p.add_argument("--title", required=True)
    p.add_argument(
        "--body-file",
        required=True,
        help="the gap in the kit's words: what the guide says, what the task met, the gap",
    )
    p = sub.add_parser(
        "home",
        help="set up an ideas home in a folder, committed; --check writes nothing, --github "
        "backs it up to a new private GitHub repository",
    )
    p.add_argument("folder", nargs="?", help="the home's folder (default: the current one)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="as JSON: the home found, the folder a new one would go in or why none can, "
        "whether git can commit, gh's login",
    )
    mode.add_argument("--github", metavar="NAME", help="the private repository's name")
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
            "gap": _gap,
            "home": _home,
            "hook": _hook,
        }[args.command]
        return handler(args)
    except (
        ConfigError,
        guides.GuidesError,
        board.BoardError,
        ship.ReleaseError,
        gap.GapError,
        home.HomeError,
    ) as error:
        print(f"lifecycle: {error}", file=sys.stderr)
        return 1
