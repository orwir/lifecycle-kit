"""The lifecycle kit's mechanics: the one ``lifecycle`` command.

Any agent, a git hook, CI or a person runs it; the Claude plugin only calls it.
Standard library only, Python 3.11 or later, so it runs wherever a repository does.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

KIT_ROOT = Path(__file__).resolve().parents[2]
METHOD = KIT_ROOT / "method"
_MANIFEST = KIT_ROOT / ".claude-plugin" / "plugin.json"


def kit_version() -> str:
    """The kit's release, whose one home is the plugin manifest."""
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))["version"]


def kit_repository() -> str:
    """The kit's ``owner/name`` on GitHub, from the manifest's repository: the prefix a kit
    issue reference takes outside the kit, where a bare ``#N`` is the repository's own."""
    url = json.loads(_MANIFEST.read_text(encoding="utf-8"))["repository"]
    return urlparse(url).path.strip("/").removesuffix(".git")


def is_kit(root: Path) -> bool:
    """Whether ``root`` is a checkout of the kit itself, whose ``method/`` is the canonical
    method: its manifest names the plugin this kit is, whichever
    copy of the kit is running (a plugin cache or the checkout)."""
    manifest = root / ".claude-plugin" / "plugin.json"
    if not (root / "method").is_dir() or not manifest.is_file():
        return False
    try:
        name = json.loads(manifest.read_text(encoding="utf-8")).get("name")
    except (OSError, ValueError, AttributeError):
        return False
    return name == json.loads(_MANIFEST.read_text(encoding="utf-8"))["name"]


def release(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))
