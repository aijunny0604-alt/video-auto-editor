"""BGM auto-discovery: pick the first audio-only file in input_dir as BGM."""

from __future__ import annotations

from pathlib import Path

BGM_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".aac"}


def find_bgm(input_dir: Path) -> Path | None:
    """Return the first audio-only file in input_dir, alphabetically."""
    if not input_dir.exists():
        return None
    candidates = sorted(
        p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in BGM_EXTS
    )
    return candidates[0] if candidates else None
