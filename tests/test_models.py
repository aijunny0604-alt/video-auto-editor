import pytest
from pydantic import ValidationError

from vae.models import Segment, TimeRange, Timeline, Track


def test_timerange_duration():
    assert TimeRange(start=1.0, end=3.5).duration == pytest.approx(2.5)


def test_timerange_rejects_negative_order():
    with pytest.raises(ValidationError):
        TimeRange(start=5.0, end=2.0)


def test_timerange_overlaps():
    a = TimeRange(start=0, end=5)
    b = TimeRange(start=4, end=6)
    c = TimeRange(start=6, end=8)
    assert a.overlaps(b)
    assert not a.overlaps(c)


def test_timeline_duration_max_of_segments(tmp_path):
    clip = tmp_path / "x.mp4"
    clip.touch()
    seg = Segment(
        source=clip,
        source_range=TimeRange(start=0, end=2),
        timeline_start=5.0,
        reason="t",
    )
    tl = Timeline(
        width=1920,
        height=1080,
        fps=30,
        tracks=[Track(kind="video", segments=[seg])],
    )
    assert tl.duration == pytest.approx(7.0)
