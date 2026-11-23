"""An ideas home, found, checked, set up and backed up.

One private repository holds every idea from capture to verdict (the method's
``idea_gauntlet.md`` § The ideas home). What a home is, which folder can become one, and
its layout, settings and lock are decided here, once, and the capture skill proposes from
``lifecycle home --check``. Nothing leaves the machine but by ``--github``, which the skill
runs on the person's go-ahead: gh only creates the repository, and git adds it as
``origin`` and pushes, so the local state is always this tool's to read.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import guides
from .config import FILE, ConfigError, parse

TEMPLATE = "ideas_home_template.md"
TARGET = "AGENTS.md"
GAUNTLET = "idea_gauntlet.md"
#: The folder in the user folder a new home is proposed in, and the repository's name.
NAME = "ideas"
#: What an OS writes into a folder it shows: a folder holding only these is empty.
OS_FILES = {".DS_Store", "desktop.ini", "Thumbs.db"}
SETTINGS = ".claude/settings.json"
#: The mark that ``main`` reached ``origin``: set by a push that succeeded, read offline.
PUSHED = "refs/remotes/origin/main"
#: A read that gives no answer in this long fails. The creation and the push have none.
CALL_SECONDS = 60
NO_GIT = "git is not installed: install it from https://git-scm.com, then run this again"
#: What git prints when a push is refused for want of credentials, which a rerun cannot clear.
_NO_CREDENTIALS = (
    "Authentication failed",
    "could not read Username",
    "Permission denied",
    "terminal prompts disabled",
    "403",
)
LOGS = (
    ("archived.md", "Archived ideas", "One line per killed idea; its folder is in `archive/`."),
    ("graduated.md", "Graduated ideas", "One line per graduated idea, with its next check."),
)
SETTINGS_TOML = f"""\
# The ideas home's settings for the lifecycle kit: no tasks, board or gate. Its
# procedures are in AGENTS.md, and it commits to main.

[branches]
integration = "main"

[templates]
"{TEMPLATE}" = "{TARGET}"
"""


class HomeError(Exception):
    pass


@dataclass
class Setup:
    folder: Path
    #: False where the folder was a home already and nothing was written.
    made: bool
    committed: list[str] = field(default_factory=list)


@dataclass
class Backup:
    url: str
    created: bool = False
    pushed: bool = False


def user_folder() -> Path:
    return Path.home()


def run(*args: str, cwd: Path, timeout: float | None = CALL_SECONDS) -> subprocess.CompletedProcess:
    """A command's result; a missing program or no answer in time is a ``HomeError``."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        return subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            cwd=cwd,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError as error:
        raise HomeError(f"{args[0]} is not installed") from error
    except subprocess.TimeoutExpired as error:
        raise HomeError(f"{' '.join(args[:3])} gave no answer in {timeout} s") from error


def gh(*args: str, cwd: Path, timeout: float | None = CALL_SECONDS) -> subprocess.CompletedProcess:
    return run("gh", *args, cwd=cwd, timeout=timeout)


def git(
    folder: Path, *args: str, timeout: float | None = CALL_SECONDS
) -> subprocess.CompletedProcess:
    """git run in ``folder``, which exists."""
    return run("git", *args, cwd=folder, timeout=timeout)


def nearest(folder: Path) -> Path:
    """``folder``, or the nearest of its parents that exists."""
    for candidate in (folder, *folder.parents):
        if candidate.is_dir():
            return candidate
    return Path.cwd()


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "no reason given")


def is_home(folder: Path) -> bool:
    """A home is a folder whose ``.lifecycle.toml`` names the home's template."""
    path = folder / FILE
    if not path.is_file():
        return False
    try:
        config = parse(tomllib.loads(path.read_text(encoding="utf-8")), folder)
    except (ConfigError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return False
    return config.templates_named and TEMPLATE in config.templates


def containing(start: Path) -> Path | None:
    """The home ``start`` is in, from it up, or None."""
    start = start.resolve()
    return next((folder for folder in (start, *start.parents) if is_home(folder)), None)


def find(start: Path) -> Path | None:
    """The home ``start`` is in, from it up, else ``ideas`` in the user folder, else None."""
    default = user_folder() / NAME
    return containing(start) or (default if is_home(default) else None)


def refusal(folder: Path) -> str | None:
    """Why ``folder`` cannot become a home, or None where it can. Checks nothing of git's
    identity, which ``identity`` does."""
    if folder.exists() and not folder.is_dir():
        return f"{folder} is a file"
    if is_home(folder):
        return f"{folder} is an ideas home already"
    if folder.is_dir():
        others = sorted(
            entry.name
            for entry in folder.iterdir()
            if entry.name not in OS_FILES
            and not (entry.name in (".claude", ".git") and entry.is_dir())
        )
        if others:
            shown = ", ".join(others[:5]) + (
                f" and {len(others) - 5} more" if len(others) > 5 else ""
            )
            return f"{folder} is not empty: it holds {shown}"
    if shutil.which("git") is None:
        return NO_GIT
    own = (folder / ".git").is_dir()
    if own:
        if git(folder, "rev-parse", "--verify", "-q", "HEAD").returncode == 0:
            return f"{folder} is a git repository with history"
        remotes = git(folder, "remote", "-v").stdout.split()
        if remotes:
            return (
                f"{folder} is a git repository with the remote {remotes[1]}: a home's remote "
                "is made by `lifecycle home --github`, on the person's go-ahead"
            )
    top = git(nearest(folder.parent if own else folder), "rev-parse", "--show-toplevel")
    if top.returncode == 0 and top.stdout.strip():
        return f"{folder} is inside the git repository at {Path(top.stdout.strip())}"
    return None


def identity(folder: Path) -> str | None:
    """Why git cannot commit in ``folder``, or None. Only a name and an email set in git's
    config count: one git would guess from the account and the host is nobody's choice."""
    if shutil.which("git") is None:
        return NO_GIT
    here = nearest(folder)
    missing = [
        key
        for key in ("user.name", "user.email")
        if not git(here, "config", "--get", key).stdout.strip()
    ]
    if missing:
        return f"git has no {' or '.join(missing)} to commit with: set " + " and ".join(
            f"`git config --global {key} <...>`" for key in missing
        )
    return None


def gh_login(cwd: Path) -> tuple[str | None, str | None]:
    """The signed-in gh account's login, or None with why there is none."""
    try:
        result = gh("api", "user", "--jq", ".login", cwd=cwd)
    except HomeError as error:
        return None, str(error)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "auth login" in stderr or "not logged" in stderr:
            return None, "gh is not signed in: `gh auth login`"
        return None, f"gh cannot read the signed-in account: {_first_line(stderr)}"
    return result.stdout.strip() or None, None


def here(start: Path) -> dict:
    """The git repository ``start`` is in, and whether it holds a project: a commit, or an
    ``AGENTS.md`` of its own. An empty repository, a fresh clone's among them, holds none."""
    if shutil.which("git") is None:
        return {"repository": None, "project": False}
    top = git(nearest(start), "rev-parse", "--show-toplevel")
    if top.returncode != 0 or not top.stdout.strip():
        return {"repository": None, "project": False}
    root = Path(top.stdout.strip())
    history = git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0
    return {"repository": str(root), "project": history or (root / TARGET).is_file()}


def check(folder: Path | None) -> dict:
    """What the capture skill proposes from, writing nothing: the home found, the folder a
    new one would go in or why none can, the repository the folder is in and whether it holds
    a project, whether git can commit, and gh's login."""
    start = (folder or Path.cwd()).resolve()
    candidates = [start] if folder else [start, (user_folder() / NAME).resolve()]
    proposed, refused = None, []
    for candidate in candidates:
        why = refusal(candidate)
        if why is None:
            proposed = candidate
            break
        refused.append({"folder": str(candidate), "why": why})
    found = find(start)
    git_why = identity(proposed or start)
    login, gh_why = gh_login(nearest(start))
    return {
        "home": str(found) if found else None,
        "proposed": str(proposed) if proposed else None,
        "refused": refused,
        "here": here(start),
        "git": {"ready": git_why is None, "why": git_why},
        "gh": {"login": login, "why": gh_why},
    }


def log_headers() -> list[str]:
    """The header and separator rows of the first two tables in the gauntlet's § The logs:
    the killed ideas', then the graduated ones'. Their example rows stay in the guide."""
    lines = guides.text(guides.METHOD / GAUNTLET).splitlines()
    try:
        start = lines.index("## The logs")
    except ValueError as error:
        raise HomeError(f"{GAUNTLET} has no § The logs to take the logs' tables from") from error
    tables: list[list[str]] = []
    previous = False
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        row = line.startswith("|")
        if row and not previous:
            tables.append([])
        if row:
            tables[-1].append(line)
        previous = row
    if len(tables) < 2 or any(len(table) < 2 for table in tables[:2]):
        raise HomeError(f"{GAUNTLET} § The logs no longer opens with the two logs' tables")
    return ["\n".join(table[:2]) for table in tables[:2]]


def setup(folder: Path) -> Setup:
    """Make ``folder`` a home: a git repository on ``main`` with the gauntlet's layout, the
    settings, the template as ``AGENTS.md`` and the lock at the installed release, in one
    commit of exactly those files and ``.claude/settings.json`` where it is there. Refuses,
    writing nothing, a folder that cannot become one or a git that cannot commit."""
    folder = folder.resolve()
    if is_home(folder):
        return Setup(folder, made=False)
    why = refusal(folder) or identity(folder)
    if why:
        raise HomeError(f"no home set up: {why}")
    headers = log_headers()
    template = guides.text(guides.METHOD / TEMPLATE)
    existed, repository = folder.is_dir(), (folder / ".git").is_dir()
    files = {TARGET: template, FILE: SETTINGS_TOML, "active/.gitkeep": "", "archive/.gitkeep": ""}
    for (name, title, line), header in zip(LOGS, headers, strict=True):
        files[name] = f"# {title}\n\n{line}\n\n{header}\n"
    written = [*files, guides.LOCK]
    committed = sorted([*written, *([SETTINGS] if (folder / SETTINGS).is_file() else [])])
    message = f"Set up the ideas home on lifecycle kit {guides.kit_version()}"
    added: list[str] = []  # what a git add was asked for, which may stage some and fail
    folder.mkdir(parents=True, exist_ok=True)
    try:
        if not repository:
            _ok(git(folder, "init", "-q"), "git init")
        _ok(git(folder, "symbolic-ref", "HEAD", "refs/heads/main"), "git symbolic-ref")
        for name, body in files.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8", newline="\n")
        lock = guides.Lock(kit=guides.kit_version(), templates={TEMPLATE: template})
        guides.write_lock(folder, lock)
        added = committed
        _ok(git(folder, "add", "--", *committed), "git add")
        _ok(git(folder, "commit", "-q", "-m", message), "git commit")
    except HomeError as error:
        left = _undo(folder, written, added, existed, repository)
        kept = (
            f"Not taken away: {'; '.join(left)}. Remove {'it' if len(left) == 1 else 'them'} and,"
            if left
            else "Nothing was kept:"
        )
        raise HomeError(
            f"{error}. {kept} once that is dealt with, run `lifecycle home {folder}` again"
        ) from error
    return Setup(folder, made=True, committed=committed)


def _undo(
    folder: Path, written: list[str], added: list[str], existed: bool, repository: bool
) -> list[str]:
    """Take away what a failed setup wrote, so nothing reads as a home and the folder is as
    it was: the files, what its git add staged, a repository and a folder it made. Raises
    nothing: returns what could not be taken away, each named in full for a reader anywhere."""
    left = []
    if repository and added:
        staged, why = _staged(folder, added), None
        if staged:
            try:
                result = git(folder, "rm", "-r", "-q", "--cached", "--", *staged)
            except HomeError as error:
                why = str(error)
            else:
                if result.returncode != 0:
                    why = _first_line(result.stderr or result.stdout)
        if why:
            left.append(f"the staging of {', '.join(staged)} in {folder / '.git'} ({why})")
    for name in written:
        with contextlib.suppress(OSError):
            (folder / name).unlink(missing_ok=True)
    for name in ("active", "archive"):
        with contextlib.suppress(OSError):
            (folder / name).rmdir()  # only an empty one goes
    if not repository:
        # git's objects are read-only, which Windows will not delete; a directory keeps
        # its mode, as one without its search bit hides what is in it on POSIX
        with contextlib.suppress(OSError):
            for path in (folder / ".git").rglob("*"):
                if not path.is_dir():
                    path.chmod(stat.S_IWRITE | stat.S_IREAD)
        shutil.rmtree(folder / ".git", ignore_errors=True)
    left += [str(folder / name) for name in written if (folder / name).exists()]
    if not repository and (folder / ".git").exists():
        left.append(str(folder / ".git"))
    if not existed:
        with contextlib.suppress(OSError):
            folder.rmdir()  # only an empty one goes
    return left


def _staged(folder: Path, paths: list[str]) -> list[str]:
    """Which of ``paths`` the index holds, read without taking its lock; all of them where
    git cannot say."""
    try:
        result = git(folder, "ls-files", "-z", "--", *paths)
    except HomeError:
        return paths
    if result.returncode != 0:
        return paths
    return sorted(name for name in result.stdout.split("\0") if name)


def _ok(result: subprocess.CompletedProcess, what: str) -> None:
    if result.returncode != 0:
        raise HomeError(f"{what} failed: {_first_line(result.stderr or result.stdout)}")


def origin(folder: Path) -> str | None:
    result = git(folder, "remote", "get-url", "origin")
    return result.stdout.strip() if result.returncode == 0 else None


def pushed(folder: Path) -> bool:
    """Whether ``main`` is on ``origin``, as the last push that landed left it: the remote's
    ref exists and ``main`` holds no commit past it. Read offline."""
    if git(folder, "rev-parse", "--verify", "-q", PUSHED).returncode != 0:
        return False
    ahead = git(folder, "rev-list", "--count", f"{PUSHED}..refs/heads/main")
    return ahead.returncode == 0 and ahead.stdout.strip() == "0"


def create_private(name: str, cwd: Path) -> str:
    """Create the private GitHub repository ``name`` under the signed-in account, and return
    the link gh prints, its last line. Only the creation: the remote and the push are git's."""
    _, why = gh_login(cwd)
    if why:
        raise HomeError(f"no repository created: {why}")
    result = gh("repo", "create", name, "--private", cwd=cwd, timeout=None)
    printed = result.stdout.strip().splitlines() if result.returncode == 0 else []
    if not printed:
        reason = _first_line(result.stderr or result.stdout)
        raise HomeError(
            f"no repository created: {reason}. With another name, or later, run "
            f"`lifecycle home {cwd} --github <name>` again"
        )
    return printed[-1].strip()


def push(folder: Path, name: str) -> None:
    result = git(folder, "push", "-u", "origin", "main", timeout=None)
    if result.returncode == 0:
        return
    reason = _first_line(result.stderr)
    again = f"`lifecycle home {folder} --github {name}` again"
    if any(mark in result.stderr for mark in _NO_CREDENTIALS):
        raise HomeError(
            f"the push to {origin(folder)} was refused: {reason}. git has no GitHub credentials: "
            f"run `gh auth setup-git`, then {again}"
        )
    raise HomeError(
        f"the push to {origin(folder)} failed: {reason}. Once that is dealt with, {again} pushes"
    )


def backup(folder: Path, name: str) -> Backup:
    """Back the home in ``folder`` up on GitHub: create a private repository ``name``, add it
    as ``origin`` and push ``main``. A home with an ``origin`` is only pushed, where ``main``
    holds commits the last push did not carry; one whose ``main`` is there is left as it is."""
    folder = folder.resolve()
    if not is_home(folder):
        raise HomeError(f"{folder} is not an ideas home: `lifecycle home {folder}` sets it up")
    url = origin(folder)
    if url and pushed(folder):
        return Backup(url)
    created = False
    if url is None:
        url = create_private(name, folder)
        _ok(git(folder, "remote", "add", "origin", url), "git remote add")
        created = True
    push(folder, name)
    return Backup(url, created=created, pushed=True)
