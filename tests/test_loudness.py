"""Unit tests for analyzers/loudness.py (pure-function logic)."""

from __future__ import annotations

from vae.analyzers.loudness import find_peak_windows, windows_around_peaks
from vae.models.clip import TimeRange


def test_find_peak_windows_returns_top_n():
    samples = [(0.0, -40.0), (1.0, -10.0), (2.0, -5.0), (3.0, -50.0)]
    picks = find_peak_windows(samples, top_n=2, min_gap=0.0)
    assert picks == sorted([1.0, 2.0])


def test_find_peak_windows_enforces_min_gap():
    samples = [(0.0, -10.0), (1.0, -5.0), (10.0, -7.0)]
    # min_gap=5 forces the second pick to skip the close neighbour
    picks = find_peak_windows(samples, top_n=2, min_gap=5.0)
    assert picks == sorted([1.0, 10.0])


def test_find_peak_windows_empty_input():
    assert find_peak_windows([], top_n=3) == []


def test_find_peak_windows_top_n_caps_output():
    samples = [(i * 1.0, -float(i)) for i in range(10)]
    picks = find_peak_windows(samples, top_n=3, min_gap=0.0)
    assert len(picks) == 3


def test_windows_around_peaks_centers_and_clamps():
    peaks = [5.0, 50.0]
    windows = windows_around_peaks(peaks, clip_duration=20.0, length=10.0)
    # First peak: centered at 5 → [0, 10] (start clamped to 0, end follows)
    assert windows[0] == TimeRange(start=0.0, end=10.0)
    # Second peak: 50 is past end → end clamps to 20 → start = 20-10 = 10
    assert windows[1] == TimeRange(start=10.0, end=20.0)


def test_windows_around_peaks_skips_when_clip_too_short():
    # Clip 0s long → no valid window
    windows = windows_around_peaks([1.0], clip_duration=0.0, length=10.0)
    assert windows == []


def test_windows_around_peaks_empty_peaks():
    assert windows_around_peaks([], clip_duration=10.0) == []
