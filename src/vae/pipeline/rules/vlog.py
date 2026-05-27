"""Vlog rule: remove silences, keep 16:9, generate bottom subtitles."""

from __future__ import annotations

from vae.analyzers.audio import invert_silences
from vae.models.clip import TimeRange
from vae.models.timeline import Segment, Timeline, Track
from vae.pipeline.context import AnalysisContext


def build_vlog_timeline(
    ctx: AnalysisContext,
    silence_pad: float = 0.1,
    min_segment_duration: float = 0.5,
) -> Timeline:
    """Build a 16:9 vlog timeline by removing silences and concatenating clips in order.

    Args:
        ctx: Analyzer outputs.
        silence_pad: Seconds of padding kept around speech (avoids hard cuts).
        min_segment_duration: Drop segments shorter than this (likely noise).
    """
    width, height = 1920, 1080
    fps = ctx.clips[0].fps if ctx.clips else 30.0

    video_segments: list[Segment] = []
    cursor = 0.0

    for clip in ctx.clips:
        silences = ctx.silences.get(clip.path, [])
        keep_ranges = invert_silences(silences, clip.duration, pad=silence_pad)

        for r in keep_ranges:
            if r.duration < min_segment_duration:
                continue
            video_segments.append(
                Segment(
                    source=clip.path,
                    source_range=r,
                    timeline_start=cursor,
                    reason="speech" if silences else "scene_keep",
                )
            )
            cursor += r.duration

    return Timeline(
        width=width,
        height=height,
        fps=fps,
        tracks=[Track(kind="video", segments=video_segments)],
    )


def shift_subtitles(
    ctx: AnalysisContext,
    timeline: Timeline,
) -> list[TimeRange]:
    """Future use: remap word timestamps from original clip time to timeline time.

    Currently returns the union of timeline segments for reference.
    """
    out: list[TimeRange] = []
    for track in timeline.tracks:
        for seg in track.segments:
            out.append(TimeRange(start=seg.timeline_start, end=seg.timeline_end))
    return out
