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
    base,
    board,
    ci,
    doctor,
    gap,
    guides,
    home,
    hook,
    kit_repository,
    kit_version,
    merge,
    ship,
    tidy,
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
    if args.setup:
        return _board_setup(args)
    config = _config()
    if not config.board_owner:
        raise ConfigError(".lifecycle.toml has no [board]: this repository tracks no board")
    board.move(
        args.issues,
        args.column,
        config.board_owner,
        config.board_number,
        args.after,
        lambda line: print(line, flush=True),
    )
    return 0


def _board_setup(args: argparse.Namespace) -> int:
    config = load()
    named = config.board_owner if config else None
    repo = json.loads(
        board.gh("repo", "view", "--json", "id,nameWithOwner,name,owner,visibility,url")
    )
    number = args.number or (config.board_number if config else None)
    done = board.setup(repo, named, number, lambda line: print(line, flush=True))
    if done.left:
        print(
            f"left with no Status: {done.left} card(s) the board tracks no column for "
            f"(a pull request, a draft, a {gap.LABEL} issue, another repository's)"
        )
    elsewhere = not named or bool(config and config.board_number != done.number)
    if elsewhere:
        print("in .lifecycle.toml:")
        print(f'  [board]\n  owner = "{done.owner}"\n  number = {done.number}')
    if done.parked:
        # A move goes to the board .lifecycle.toml names, which may not be this one yet.
        once = ", once .lifecycle.toml names this board" if elsewhere else ""
        print(
            f"left in Backlog though its plan has a status: {len(done.parked)} card(s); "
            f"the maintainer's call to move each one under way{once}:"
        )
        for number in sorted(done.parked):
            print(f'  lifecycle board {number} "In Progress"')
    print(f"in the web UI, {done.url}/workflows (no API turns a workflow on or reads its value):")
    for line in done.workflows:
        print(f"  {line}")
    if done.rename:
        print(
            f'in the web UI, {done.rename}: rename "{board.FRESH_VIEW}" to "{board.TABLE}" '
            "(no API renames a view)"
        )
    if repo["visibility"] == "PUBLIC" and not done.public:
        print(
            "once the board is triaged, make it public as the repository is: "
            f"gh project edit {done.number} --owner {done.owner} --visibility PUBLIC"
        )
    return 0


def _commit(config: Config, name: str) -> str:
    """``name`` as the full SHA of a commit in this repository."""
    resolved = subprocess.run(
        ["git", "-C", str(config.root), "rev-parse", "--verify", f"{name}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if resolved.returncode != 0:
        raise ConfigError(f"{name} is not a commit in this repository")
    return resolved.stdout.strip()


def _release(args: argparse.Namespace) -> int:
    config = _config()
    if not config.release_workflow:
        raise ConfigError(
            ".lifecycle.toml names no [release] workflow: this repository ships no release by it"
        )
    ref = args.ref or config.integration
    code, line = ship.release(config.release_workflow, ref, _commit(config, args.commit))
    print(f"release: {line}", file=sys.stdout if code == ship.SHIPPED else sys.stderr)
    return code


def _ci(args: argparse.Namespace) -> int:
    config = _config()
    if args.pr is not None:
        code, line = ci.pull_request(config.root, args.pr)
    else:
        ref = args.ref or config.integration
        code, line = ci.push(config.root, _commit(config, args.commit), ref)
    print(f"ci: {line}", file=sys.stdout if code == ci.PASSED else sys.stderr)
    return code


def _merge(args: argparse.Namespace) -> int:
    code, lines = merge.merge(_config().root, args.pr)
    for line in lines:
        print(line, file=sys.stdout if code == merge.MERGED else sys.stderr)
    return code


def _base(args: argparse.Namespace) -> int:
    config = _config()
    print(base.base(config.root, config.integration))
    return 0


def _tidy(args: argparse.Namespace) -> int:
    config = _config()
    report = tidy.tidy(config.root, config.integration, remove=args.remove)
    for line in report.lines:
        print(line)
    return 1 if report.refused else 0


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
        for item in made.ignored:
            print(f"warning: {home.warning(made.folder, item)}")
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


def _columns() -> str:
    """The columns a move takes, a name with a space quoted as the shell needs it."""
    return ", ".join(f'"{name}"' if " " in name else name for name in board.COLUMNS)


def _check_board(args: argparse.Namespace) -> None:
    """Split ``targets`` into setup, or the issues and their column; refuse what argparse cannot.

    Every refusal is ``lifecycle board``'s own usage error, before anything is read.
    """
    fail, targets = args.board_parser.error, args.targets
    columns = _columns()
    args.setup, args.issues, args.column = targets[0] == "setup", [], None
    if args.setup:
        if len(targets) > 1:
            fail("setup takes no column")
        if args.after is not None:
            fail("--after is a move's: setup places no card")
        return
    if targets[-1] in board.COLUMNS:
        args.column, targets = targets[-1], targets[:-1]
    elif len(targets) > 1 and not targets[-1].isdigit():
        fail(f"{targets[-1]!r} is not a column: {columns}")
    for value in targets:
        try:
            args.issues.append(int(value))
        except ValueError:
            fail(f"{value!r} is not an issue number or setup")
    if not args.issues:
        fail(f"{args.column} needs the issues' numbers before it")
    if args.column is None:
        fail(f"#{args.issues[-1]} needs a column after it: {columns}")
    twice = sorted({issue for issue in args.issues if args.issues.count(issue) > 1})
    if twice:
        fail(f"#{twice[0]} is listed twice: each card takes one place")
    if args.after in args.issues:
        fail(f"--after {args.after} is a card this move places: name one already in the column")
    if args.number is not None:
        fail("--number is setup's: a move uses the board .lifecycle.toml names")


def _check_ci(args: argparse.Namespace) -> None:
    if (args.commit is None) == (args.pr is None):
        args.ci_parser.error("name a pushed commit, or a pull request by --pr, not both")
    if args.pr is not None and args.ref:
        args.ci_parser.error("--ref is a push's: a pull request's checks are its own")


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
    summary = (
        "put issues' cards in a board column in the order given, at its top or after "
        "--after's card (Ready only on the maintainer's triage call); setup creates a board "
        "or fixes one in place"
    )
    p = sub.add_parser(
        "board",
        help=summary,
        description=summary[0].upper() + summary[1:] + ".",
        usage="%(prog)s N... COLUMN [--after M]\n       %(prog)s setup [--number NUMBER]",
    )
    p.set_defaults(board_parser=p)
    p.add_argument(
        "targets",
        nargs="+",
        metavar="N",
        help=f"the issues' numbers, in the order their cards take, then the column "
        f"({_columns()}); or setup alone",
    )
    p.add_argument(
        "--after",
        type=int,
        metavar="M",
        help="a move: the first card right after #M's, which must be in the column "
        "(default: the column's top)",
    )
    p.add_argument(
        "--number",
        type=int,
        help="setup: the board to fix in place (default: the one .lifecycle.toml names, "
        "otherwise a new one)",
    )
    p = sub.add_parser("release", help="ship a reviewed commit by the release workflow, watched")
    p.add_argument("commit", help="the head the release review read")
    p.add_argument("--ref", help="the branch to dispatch on (default: the integration branch)")
    p = sub.add_parser(
        "ci",
        help="wait on the CI a push started, or a pull request's checks, and say how it ended",
    )
    p.set_defaults(ci_parser=p)
    p.add_argument("commit", nargs="?", help="the pushed commit")
    p.add_argument("--ref", help="the branch it was pushed to (default: the integration branch)")
    p.add_argument("--pr", type=int, help="a pull request: wait on its checks instead")
    p = sub.add_parser(
        "merge",
        help="squash-merge a pull request, read its state after, and delete its branch on "
        "GitHub and here where nothing is lost; a linked worktree's branch stays",
    )
    p.add_argument("pr", type=int, help="the pull request's number")
    sub.add_parser(
        "base",
        help="the commit a task's work is measured from: where HEAD forked from the integration "
        "branch, here or on origin, as a full SHA",
    )
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
    p = sub.add_parser(
        "tidy",
        help="fast-forward the primary checkout's integration branch to origin's, and list "
        "the linked worktrees whose own work has landed; offline",
    )
    p.add_argument(
        "--remove",
        action="store_true",
        help="remove those worktrees, their git-ignored files with them, and delete their "
        "branches: run on the maintainer's word, since a session may still have one open",
    )
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
    if args.command == "board":
        _check_board(args)
    if args.command == "ci":
        _check_ci(args)
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
            "ci": _ci,
            "merge": _merge,
            "base": _base,
            "tidy": _tidy,
            "gap": _gap,
            "home": _home,
            "hook": _hook,
        }[args.command]
        return handler(args)
    except (
        ConfigError,
        base.BaseError,
        guides.GuidesError,
        board.BoardError,
        ship.ReleaseError,
        merge.MergeError,
        gap.GapError,
        home.HomeError,
    ) as error:
        print(f"lifecycle: {error}", file=sys.stderr)
        return 1
