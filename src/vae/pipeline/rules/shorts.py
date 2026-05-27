"""Shorts rule: extract highlight windows, 9:16 canvas, aggressive silence trim."""

from __future__ import annotations

from vae.analyzers.audio import invert_silences
from vae.analyzers.loudness import find_peak_windows, windows_around_peaks
from vae.models.clip import TimeRange
from vae.models.timeline import Segment, Timeline, Track
from vae.pipeline.context import AnalysisContext


def build_shorts_timelines(
    ctx: AnalysisContext,
    loudness_samples: dict | None = None,
    target_length: float = 30.0,
    top_n: int = 3,
    min_segment_duration: float = 0.3,
    silence_pad: float = 0.05,
) -> list[Timeline]:
    """Build N vertical-shorts timelines, one per detected highlight window.

    Args:
        ctx: Analyzer outputs.
        loudness_samples: Per-clip (time, rms) lists; if None, single window from start.
        target_length: Desired shorts length in seconds.
        top_n: Max number of shorts to emit per clip.
        min_segment_duration: Drop sub-segments shorter than this after silence trim.
        silence_pad: Smaller padding than vlog (shorts want punchy cuts).
    """
    width, height = 1080, 1920
    timelines: list[Timeline] = []

    for clip in ctx.clips:
        samples = (loudness_samples or {}).get(clip.path, [])
        if samples:
            peaks = find_peak_windows(samples, top_n=top_n, min_gap=target_length)
            windows = windows_around_peaks(peaks, clip.duration, length=target_length)
        else:
            windows = [TimeRange(start=0.0, end=min(target_length, clip.duration))]

        for window in windows:
            silences = ctx.silences.get(clip.path, [])
            local_silences = _clamp_silences_to_window(silences, window)
            keep_local = invert_silences(
                local_silences,
                total_duration=window.duration,
                pad=silence_pad,
            )

            segments: list[Segment] = []
            cursor = 0.0
            for r in keep_local:
                if r.duration < min_segment_duration:
                    continue
                source_range = TimeRange(
                    start=window.start + r.start,
                    end=window.start + r.end,
                )
                segments.append(
                    Segment(
                        source=clip.path,
                        source_range=source_range,
                        timeline_start=cursor,
                        reason="highlight_peak" if samples else "intro_window",
                    )
                )
                cursor += r.duration

            if not segments:
                continue

            timelines.append(
                Timeline(
                    width=width,
                    height=height,
                    fps=clip.fps,
                    tracks=[Track(kind="video", segments=segments)],
                )
            )

    return timelines


def _clamp_silences_to_window(
    silences: list[TimeRange],
    window: TimeRange,
) -> list[TimeRange]:
    """Translate global silence ranges into window-local coordinates."""
    out: list[TimeRange] = []
    for s in silences:
        if s.end <= window.start or s.start >= window.end:
            continue
        local = TimeRange(
            start=max(0.0, s.start - window.start),
            end=min(window.duration, s.end - window.start),
        )
        if local.duration > 0:
            out.append(local)
    return out
