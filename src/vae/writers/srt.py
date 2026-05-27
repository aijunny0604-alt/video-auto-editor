"""SRT subtitle file writer."""

from __future__ import annotations

from pathlib import Path

from vae.models.subtitle import Subtitle


def write_srt(subtitles: list[Subtitle], output: Path) -> Path:
    """Write subtitles to an .srt file (UTF-8)."""
    output.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for i, sub in enumerate(subtitles, start=1):
        lines.append(str(i))
        lines.append(f"{_fmt_ts(sub.start)} --> {_fmt_ts(sub.end)}")
        lines.append(sub.text)
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def _fmt_ts(seconds: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
