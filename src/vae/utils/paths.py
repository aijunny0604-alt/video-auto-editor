"""Path helpers — locate CapCut draft folder etc."""

from __future__ import annotations

import os
from pathlib import Path


def capcut_draft_root() -> Path | None:
    """Return CapCut's project root folder on Windows, or None if not found."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        return None
    candidate = Path(local_appdata) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    return candidate if candidate.exists() else None


def list_capcut_projects() -> list[Path]:
    """List CapCut project folders (UUID-named directories)."""
    root = capcut_draft_root()
    if not root:
        return []
    return sorted(
        [p for p in root.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
