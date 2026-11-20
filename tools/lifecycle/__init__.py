"""The lifecycle kit's mechanics: the one ``lifecycle`` command.

Any agent, a git hook, CI or a person runs it; the Claude plugin only calls it.
Standard library only, Python 3.11 or later, so it runs wherever a repository does.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]
METHOD = KIT_ROOT / "method"
_MANIFEST = KIT_ROOT / ".claude-plugin" / "plugin.json"


def kit_version() -> str:
    """The kit's release, whose one home is the plugin manifest."""
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))["version"]


def kit_remote() -> str:
    """Where the kit is pushed: the manifest's repository, or ``LIFECYCLE_KIT_REMOTE``."""
    if override := os.environ.get("LIFECYCLE_KIT_REMOTE"):
        return override
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))["repository"] + ".git"


def release(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))
