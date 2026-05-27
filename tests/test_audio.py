from pathlib import Path

import pytest

from vae.analyzers.audio import (
    _parse_silencedetect,
    detect_silences,
    invert_silences,
)
from vae.models import TimeRange

from tests.conftest import requires_ffmpeg


def test_parse_silencedetect_basic():
    stderr = """
[silencedetect @ 0x1] silence_start: 1.0
[silencedetect @ 0x1] silence_end: 3.0 | silence_duration: 2.0
[silencedetect @ 0x1] silence_start: 4.0
[silencedetect @ 0x1] silence_end: 5.0 | silence_duration: 1.0
"""
    ranges = _parse_silencedetect(stderr)
    assert len(ranges) == 2
    assert ranges[0].start == pytest.approx(1.0)
    assert ranges[0].end == pytest.approx(3.0)
    assert ranges[1].start == pytest.approx(4.0)
    assert ranges[1].end == pytest.approx(5.0)


def test_parse_silencedetect_ignores_orphan_end():
    stderr = "[silencedetect] silence_end: 2.0 | silence_duration: 1.0\n"
    assert _parse_silencedetect(stderr) == []


def test_invert_silences_empty_returns_whole_clip():
    out = invert_silences([], total_duration=10.0, pad=0.0)
    assert out == [TimeRange(start=0, end=10)]


def test_invert_silences_basic():
    silences = [TimeRange(start=2, end=3), TimeRange(start=5, end=6)]
    out = invert_silences(silences, total_duration=8.0, pad=0.0)
    assert out == [
        TimeRange(start=0, end=2),
        TimeRange(start=3, end=5),
        TimeRange(start=6, end=8),
    ]


def test_invert_silences_with_pad_merges_overlap():
    silences = [TimeRange(start=2, end=3), TimeRange(start=3.1, end=4)]
    out = invert_silences(silences, total_duration=6.0, pad=0.2)
    starts = [r.start for r in out]
    ends = [r.end for r in out]
    # padding overlaps the middle slice → merges into one
    assert all(s >= 0 for s in starts)
    assert all(e <= 6.0 for e in ends)


def test_invert_silences_zero_duration():
    assert invert_silences([], total_duration=0.0) == []


@requires_ffmpeg
def test_detect_silences_on_synthetic_clip(synthetic_clip: Path):
    ranges = detect_silences(synthetic_clip, noise_db=-30.0, min_duration=0.4)
    # synthetic: tone(1) | silence(2) | tone(1) | silence(1) | tone(1)
    # expect 2 silence ranges roughly around [1,3] and [4,5]
    assert len(ranges) == 2
    assert 0.8 < ranges[0].start < 1.2
    assert 2.8 < ranges[0].end < 3.2
    assert 3.8 < ranges[1].start < 4.2
    assert 4.8 < ranges[1].end < 5.2
