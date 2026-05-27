"""Loudness analyzer - detect volume peaks via FFmpeg astats per-window.

Lightweight pure-FFmpeg implementation (no librosa) - parses `astats` filter
output to find high-RMS windows.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from vae.models.clip import TimeRange

_RMS_RE = re.compile(r"lavfi\.astats\.Overall\.RMS_level=(-?[0-9.]+)")
_TIME_RE = re.compile(r"pts_time:([0-9.]+)")


def analyze_loudness(
    path: Path,
    window: float = 1.0,
    ffmpeg_bin: str = "ffmpeg",
) -> list[tuple[float, float]]:
    """Return per-window (time_seconds, rms_db) samples for the input file.

    Uses `astats=metadata=1:reset=<window>` so each window emits one frame
    of metadata that we parse from stderr (with `-loglevel info`).
    """
    if not path.exists():
        raise FileNotFoundError(path)

    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "info",
        "-i",
        str(path),
        "-vn",
        "-af",
        f"astats=metadata=1:reset={window},ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    samples: list[tuple[float, float]] = []
    current_time: float | None = None
    for line in result.stderr.splitlines():
        t = _TIME_RE.search(line)
        if t:
            current_time = float(t.group(1))
            continue
        m = _RMS_RE.search(line)
        if m and current_time is not None:
            rms = float(m.group(1))
            samples.append((current_time, rms))
            current_time = None
    return samples


def find_peak_windows(
    samples: list[tuple[float, float]],
    top_n: int = 3,
    min_gap: float = 5.0,
) -> list[float]:
    """Pick the top-N loudest window centers, enforcing a min gap between picks.

    Args:
        samples: (time, rms_db) from analyze_loudness().
        top_n: How many peaks to return at most.
        min_gap: Minimum seconds between consecutive picks.

    Returns:
        Sorted list of window center times.
    """
    if not samples:
        return []

    sorted_by_rms = sorted(samples, key=lambda s: s[1], reverse=True)
    picks: list[float] = []
    for time, _rms in sorted_by_rms:
        if all(abs(time - p) >= min_gap for p in picks):
            picks.append(time)
        if len(picks) >= top_n:
            break
    return sorted(picks)


def windows_around_peaks(
    peaks: list[float],
    clip_duration: float,
    length: float = 30.0,
) -> list[TimeRange]:
    """Build TimeRanges of fixed length centered (approximately) on peaks.

    Clamps to [0, clip_duration].
    """
    ranges: list[TimeRange] = []
    half = length / 2
    for p in peaks:
        start = max(0.0, p - half)
        end = min(clip_duration, start + length)
        start = max(0.0, end - length)
        if end - start <= 0:
            continue
        ranges.append(TimeRange(start=start, end=end))
    return ranges
