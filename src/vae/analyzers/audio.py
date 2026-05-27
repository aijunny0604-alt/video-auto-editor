"""Audio analyzers - silence detection via FFmpeg silencedetect filter."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from vae.models.clip import TimeRange

_SILENCE_START_RE = re.compile(r"silence_start:\s*([0-9.]+)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)")


def detect_silences(
    path: Path,
    noise_db: float = -30.0,
    min_duration: float = 0.5,
    ffmpeg_bin: str = "ffmpeg",
) -> list[TimeRange]:
    """Detect silence ranges in an audio/video file.

    Uses FFmpeg's silencedetect filter; parses stderr text.
    Returns ranges sorted by start time. Empty list if no silences.

    Args:
        path: Input media file.
        noise_db: Threshold in dB. -30 is a reasonable default; lower (e.g. -50)
                  is stricter (less detected), higher (e.g. -20) is looser.
        min_duration: Minimum silence length in seconds.
        ffmpeg_bin: ffmpeg binary name or path.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f",
        "null",
        "-",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0 and not result.stderr:
        raise RuntimeError(f"ffmpeg failed for {path}: {result.stderr or result.stdout}")

    return _parse_silencedetect(result.stderr)


def _parse_silencedetect(stderr_text: str) -> list[TimeRange]:
    starts: list[float] = []
    ranges: list[TimeRange] = []

    for line in stderr_text.splitlines():
        if "silence_start" in line:
            m = _SILENCE_START_RE.search(line)
            if m:
                starts.append(float(m.group(1)))
        elif "silence_end" in line:
            m = _SILENCE_END_RE.search(line)
            if m and starts:
                end = float(m.group(1))
                start = starts.pop(0)
                ranges.append(TimeRange(start=start, end=end))

    return sorted(ranges, key=lambda r: r.start)


def invert_silences(
    silences: list[TimeRange],
    total_duration: float,
    pad: float = 0.1,
) -> list[TimeRange]:
    """Given silence ranges within a clip, return the non-silent (speech) ranges.

    Args:
        silences: Detected silence ranges.
        total_duration: Full clip duration in seconds.
        pad: Padding added to each kept range (helps avoid abrupt cuts).
             Pad is applied symmetrically and clamped to [0, total_duration].
    """
    if total_duration <= 0:
        return []

    if not silences:
        return [TimeRange(start=0.0, end=total_duration)]

    keep: list[TimeRange] = []
    cursor = 0.0
    for s in sorted(silences, key=lambda r: r.start):
        if s.start > cursor:
            keep.append(TimeRange(start=cursor, end=s.start))
        cursor = max(cursor, s.end)
    if cursor < total_duration:
        keep.append(TimeRange(start=cursor, end=total_duration))

    if pad <= 0:
        return keep

    padded: list[TimeRange] = []
    for r in keep:
        padded.append(
            TimeRange(
                start=max(0.0, r.start - pad),
                end=min(total_duration, r.end + pad),
            )
        )
    return _merge_overlapping(padded)


def _merge_overlapping(ranges: list[TimeRange]) -> list[TimeRange]:
    if not ranges:
        return []
    sorted_r = sorted(ranges, key=lambda r: r.start)
    merged = [sorted_r[0]]
    for r in sorted_r[1:]:
        last = merged[-1]
        if r.start <= last.end:
            merged[-1] = TimeRange(start=last.start, end=max(last.end, r.end))
        else:
            merged.append(r)
    return merged
