"""Tests for pipeline/subtitles.py - timeline-aware word remapping."""

from __future__ import annotations

from pathlib import Path

from vae.models.clip import TimeRange
from vae.models.subtitle import Word
from vae.models.timeline import Segment, Timeline, Track
from vae.pipeline.subtitles import attach_subtitle_track, words_on_timeline


def _segment(source: Path, src_start: float, src_end: float, tl_start: float) -> Segment:
    return Segment(
        source=source,
        source_range=TimeRange(start=src_start, end=src_end),
        timeline_start=tl_start,
        reason="t",
    )


def test_words_on_timeline_shifts_into_timeline_coords(tmp_path: Path):
    clip = tmp_path / "c.mp4"
    clip.touch()
    timeline = Timeline(
        width=1920,
        height=1080,
        fps=30,
        tracks=[Track(kind="video", segments=[_segment(clip, 5.0, 10.0, 0.0)])],
    )
    words = {
        clip: [
            Word(text="안녕", start=5.2, end=5.6),  # inside, shifts to 0.2-0.6
            Word(text="밖", start=2.0, end=4.0),  # outside, dropped
        ]
    }
    out = words_on_timeline(timeline, words)
    assert len(out) == 1
    assert out[0].text == "안녕"
    assert abs(out[0].start - 0.2) < 1e-6
    assert abs(out[0].end - 0.6) < 1e-6


def test_words_on_timeline_drops_words_in_silence_cut(tmp_path: Path):
    clip = tmp_path / "c.mp4"
    clip.touch()
    # Two segments with a gap [3,5] cut out
    timeline = Timeline(
        width=1920,
        height=1080,
        fps=30,
        tracks=[
            Track(
                kind="video",
                segments=[
                    _segment(clip, 0.0, 3.0, 0.0),
                    _segment(clip, 5.0, 8.0, 3.0),
                ],
            )
        ],
    )
    words = {
        clip: [
            Word(text="처음", start=1.0, end=2.0),  # kept in seg1 -> 1.0-2.0
            Word(text="잘림", start=3.5, end=4.5),  # in the cut -> dropped
            Word(text="다음", start=6.0, end=7.0),  # in seg2 -> shifts to 4.0-5.0
        ]
    }
    out = words_on_timeline(timeline, words)
    texts = [w.text for w in out]
    assert texts == ["처음", "다음"]
    assert abs(out[1].start - 4.0) < 1e-6


def test_attach_subtitle_track_adds_track(tmp_path: Path):
    clip = tmp_path / "c.mp4"
    clip.touch()
    tl = Timeline(
        width=1920,
        height=1080,
        fps=30,
        tracks=[Track(kind="video", segments=[_segment(clip, 0.0, 2.0, 0.0)])],
    )
    new_tl = attach_subtitle_track(tl, [Word(text="hi", start=0.0, end=0.5)])
    assert len(new_tl.tracks) == 2
    sub_track = next(t for t in new_tl.tracks if t.kind == "subtitle")
    assert len(sub_track.segments) == 1
