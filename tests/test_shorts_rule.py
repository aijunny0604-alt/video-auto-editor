"""Unit tests for pipeline/rules/shorts.py logic (no ffmpeg needed)."""

from __future__ import annotations

from pathlib import Path

from vae.models.clip import ClipMeta, TimeRange
from vae.pipeline.context import AnalysisContext
from vae.pipeline.rules.shorts import build_shorts_timelines


def _clip(path: Path, duration: float = 60.0, w: int = 1920, h: int = 1080) -> ClipMeta:
    return ClipMeta(
        path=path,
        duration=duration,
        fps=30.0,
        width=w,
        height=h,
        has_audio=True,
        codec="h264",
    )


def test_no_loudness_produces_single_intro_window(tmp_path: Path):
    clip = _clip(tmp_path / "c.mp4")
    ctx = AnalysisContext(clips=[clip], silences={clip.path: []})
    timelines = build_shorts_timelines(ctx, loudness_samples=None, target_length=10.0)
    assert len(timelines) == 1
    tl = timelines[0]
    assert tl.width == 1080 and tl.height == 1920
    assert tl.mode == "shorts"
    video_segs = next(t for t in tl.tracks if t.kind == "video").segments
    assert len(video_segs) >= 1
    # All video segments have a crop region attached
    for seg in video_segs:
        assert seg.crop is not None
    # Subtitle track present with shorts style preset
    sub_track = next(t for t in tl.tracks if t.kind == "subtitle")
    assert sub_track.subtitle_style is not None
    assert sub_track.subtitle_style.anchor == "middle-center"


def test_top_n_peaks_drives_timeline_count(tmp_path: Path):
    clip = _clip(tmp_path / "c.mp4", duration=120.0)
    # Three loud peaks well-separated
    loudness = [(t, -10.0 if t in (10.0, 50.0, 100.0) else -40.0) for t in range(0, 120)]
    ctx = AnalysisContext(
        clips=[clip],
        silences={clip.path: []},
        loudness={clip.path: loudness},
    )
    timelines = build_shorts_timelines(
        ctx,
        loudness_samples={clip.path: loudness},
        target_length=10.0,
        top_n=3,
    )
    assert len(timelines) == 3
    for tl in timelines:
        assert tl.width == 1080 and tl.height == 1920


def test_short_segments_below_threshold_are_dropped(tmp_path: Path):
    clip = _clip(tmp_path / "c.mp4", duration=20.0)
    # Silence covering almost the whole intro window
    silences = [TimeRange(start=0.0, end=9.95)]
    ctx = AnalysisContext(
        clips=[clip],
        silences={clip.path: silences},
    )
    timelines = build_shorts_timelines(
        ctx,
        loudness_samples=None,
        target_length=10.0,
        min_segment_duration=1.0,
    )
    # Either the timeline is dropped entirely or has no qualifying segments
    if timelines:
        for tl in timelines:
            video_segs = next(t for t in tl.tracks if t.kind == "video").segments
            assert all(s.source_range.duration >= 1.0 for s in video_segs)


def test_subtitle_track_has_shorts_preset(tmp_path: Path):
    clip = _clip(tmp_path / "c.mp4")
    ctx = AnalysisContext(clips=[clip], silences={clip.path: []})
    timelines = build_shorts_timelines(ctx, target_length=5.0)
    sub_track = next(t for t in timelines[0].tracks if t.kind == "subtitle")
    style = sub_track.subtitle_style
    assert style is not None
    assert style.font_size == 60
    assert style.emphasis_color == "#FFD400"
