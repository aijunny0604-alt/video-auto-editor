"""Remap word timestamps from source-clip time to timeline time."""

from __future__ import annotations

from pathlib import Path

from vae.models.subtitle import Word
from vae.models.timeline import Segment, Timeline, Track


def words_on_timeline(
    timeline: Timeline,
    speech_words: dict[Path, list[Word]],
) -> list[Word]:
    """Translate Words from original-clip time into timeline time.

    For each video segment, find words whose original timestamps fall inside
    the segment's source_range, then shift by (timeline_start - source_start).
    Words spanning a cut are clipped to the segment boundary.
    """
    video_segs = [
        seg for track in timeline.tracks if track.kind == "video" for seg in track.segments
    ]
    if not video_segs:
        return []

    result: list[Word] = []
    for seg in video_segs:
        clip_words = speech_words.get(seg.source, [])
        offset = seg.timeline_start - seg.source_range.start
        for w in clip_words:
            if w.end <= seg.source_range.start or w.start >= seg.source_range.end:
                continue
            start = max(w.start, seg.source_range.start) + offset
            end = min(w.end, seg.source_range.end) + offset
            if end <= start:
                continue
            result.append(
                Word(text=w.text, start=start, end=end, confidence=w.confidence)
            )

    result.sort(key=lambda w: w.start)
    return result


def attach_subtitle_track(timeline: Timeline, words: list[Word]) -> Timeline:
    """Return a new Timeline with a subtitle Track carrying one segment per word.

    Subtitle segments use timeline coordinates directly (source_range matches
    timeline time). source is left empty (Path('')) because subtitles aren't tied
    to a media file.
    """
    from vae.models.clip import TimeRange

    segments: list[Segment] = []
    for w in words:
        segments.append(
            Segment(
                source=Path(""),
                source_range=TimeRange(start=w.start, end=w.end),
                timeline_start=w.start,
                reason=f"word:{w.text}",
            )
        )

    new_tracks = list(timeline.tracks) + [Track(kind="subtitle", segments=segments)]
    return Timeline(
        width=timeline.width,
        height=timeline.height,
        fps=timeline.fps,
        tracks=new_tracks,
    )
