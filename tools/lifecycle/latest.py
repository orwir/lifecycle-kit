"""The newest kit release on its remote, asked at most once a day per machine.

A machine whose kit never updates itself (no credentials for the private remote,
offline, auto-update off) would otherwise run an old kit with nothing saying so. One
`git ls-remote` with a short timeout and no prompts answers it. The day is recorded
before asking, so a failed or cut-short check is silent and still waits a day.
``bounded.run`` keeps the timeout whatever git starts, and kills git's process group at it:
on Windows, Git's ``git.exe`` launcher and a hung remote helper would otherwise hold the
call for the helper's whole hang.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from . import bounded, kit_remote, release

DAY_SECONDS = 24 * 60 * 60
TIMEOUT_SECONDS = 3
_TAG = re.compile(r"refs/tags/v(\d+\.\d+\.\d+)$")
# No terminal prompt, no askpass, no credential-manager window: a check that would ask
# for anything fails instead.
_QUIET = {"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "", "GCM_INTERACTIVE": "never"}


def cache_file() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "lifecycle-kit" / "latest.json"


def _read() -> dict:
    try:
        return json.loads(cache_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write(entry: dict) -> None:
    path = cache_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        pass


def _ask() -> str | None:
    try:
        listed = bounded.run(
            ["git", "ls-remote", "--tags", "--refs", kit_remote()],
            timeout=TIMEOUT_SECONDS,
            env={**os.environ, **_QUIET},
        )
    except OSError:
        return None
    if listed is None or listed.returncode != 0:
        return None
    versions = [m.group(1) for line in listed.stdout.splitlines() if (m := _TAG.search(line))]
    return max(versions, key=release) if versions else None


def latest_release(now: float | None = None) -> str | None:
    """The newest release tag, from a cache under a day old, else from the remote."""
    now = time.time() if now is None else now
    cached = _read()
    if now - cached.get("checked", 0) < DAY_SECONDS:
        return cached.get("latest")
    _write({"checked": now, "latest": cached.get("latest")})
    found = _ask()
    if found:
        _write({"checked": now, "latest": found})
    return found or cached.get("latest")
