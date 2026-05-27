"""Unit tests for face tracking models and face-aware crop logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from vae.analyzers.faces import FaceTrack
from vae.models.clip import ClipMeta
from vae.utils.crop import center_crop_for_aspect, face_aware_crop


def _clip(w: int = 1920, h: int = 1080) -> ClipMeta:
    return ClipMeta(
        path=Path("dummy.mp4"),
        duration=10.0,
        fps=30,
        width=w,
        height=h,
        has_audio=True,
        codec="h264",
    )


def test_face_track_time_range_empty():
    assert FaceTrack(track_id=0).time_range.start == 0.0
    assert FaceTrack(track_id=0).time_range.end == 0.0


def test_face_track_time_range_with_samples():
    t = FaceTrack(track_id=1, samples=[(1.0, 0.1, 0.1, 0.2, 0.2), (5.5, 0.2, 0.2, 0.2, 0.2)])
    assert t.time_range.start == 1.0
    assert t.time_range.end == 5.5


def test_face_track_center_at_nearest():
    t = FaceTrack(
        track_id=0,
        samples=[
            (0.0, 0.0, 0.0, 0.2, 0.2),
            (1.0, 0.4, 0.4, 0.2, 0.2),
            (2.0, 0.8, 0.8, 0.1, 0.1),
        ],
    )
    # At t=1.1, nearest sample is (1.0, ...) → center (0.5, 0.5)
    cx, cy = t.center_at(1.1)
    assert cx == pytest.approx(0.5)
    assert cy == pytest.approx(0.5)


def test_face_track_center_at_empty_returns_none():
    assert FaceTrack(track_id=0).center_at(0.0) is None


def test_face_aware_crop_empty_falls_back_to_center():
    clip = _clip(1920, 1080)
    expected = center_crop_for_aspect(clip, target_aspect=9 / 16)
    actual = face_aware_crop(clip, [], target_aspect=9 / 16)
    assert actual == expected


def test_face_aware_crop_left_face_pulls_window_left():
    clip = _clip(1920, 1080)
    face_left = FaceTrack(track_id=0, samples=[(0.0, 0.05, 0.4, 0.15, 0.2)])
    region = face_aware_crop(clip, [face_left], target_aspect=9 / 16, time=0.0)
    # Center crop would be x ≈ 0.342; left-leaning face should pull x lower (≤ center)
    center = center_crop_for_aspect(clip, target_aspect=9 / 16)
    assert region.x <= center.x


def test_face_aware_crop_right_face_pulls_window_right():
    clip = _clip(1920, 1080)
    face_right = FaceTrack(track_id=0, samples=[(0.0, 0.75, 0.4, 0.15, 0.2)])
    region = face_aware_crop(clip, [face_right], target_aspect=9 / 16, time=0.0)
    center = center_crop_for_aspect(clip, target_aspect=9 / 16)
    assert region.x >= center.x


def test_face_aware_crop_clamps_inside_frame():
    clip = _clip(1920, 1080)
    edge_face = FaceTrack(track_id=0, samples=[(0.0, 0.98, 0.4, 0.02, 0.1)])
    region = face_aware_crop(clip, [edge_face], target_aspect=9 / 16, time=0.0)
    # Window must stay inside [0,1] regardless of face being near edge
    assert region.x >= 0.0
    assert region.x + region.width <= 1.0 + 1e-9


def test_face_aware_crop_prefers_longest_track():
    clip = _clip(1920, 1080)
    short_left = FaceTrack(track_id=0, samples=[(0.0, 0.05, 0.4, 0.15, 0.2)])
    long_right = FaceTrack(
        track_id=1,
        samples=[(0.0, 0.75, 0.4, 0.15, 0.2)] * 5,
    )
    region = face_aware_crop(clip, [short_left, long_right], target_aspect=9 / 16, time=0.0)
    center = center_crop_for_aspect(clip, target_aspect=9 / 16)
    # Longer track wins → window pulled right
    assert region.x >= center.x
