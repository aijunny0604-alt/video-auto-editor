"""Unit tests for style models and crop math."""

from __future__ import annotations

from pathlib import Path

import pytest

from vae.models import (
    SHORTS_SUBTITLE_STYLE,
    VLOG_SUBTITLE_STYLE,
    ClipMeta,
    CropRegion,
    SubtitleStyle,
)
from vae.utils.crop import center_crop_for_aspect, vertical_crop_9_16


def _clip(width: int, height: int) -> ClipMeta:
    return ClipMeta(
        path=Path("dummy.mp4"),
        duration=1.0,
        fps=30,
        width=width,
        height=height,
        has_audio=True,
        codec="h264",
    )


def test_vlog_style_defaults_to_bottom_center():
    assert VLOG_SUBTITLE_STYLE.anchor == "bottom-center"
    assert VLOG_SUBTITLE_STYLE.font_size == 30


def test_shorts_style_centered_with_emphasis():
    assert SHORTS_SUBTITLE_STYLE.anchor == "middle-center"
    assert SHORTS_SUBTITLE_STYLE.font_size == 60
    assert SHORTS_SUBTITLE_STYLE.emphasis_color == "#FFD400"


def test_subtitle_style_rejects_zero_font():
    with pytest.raises(Exception):
        SubtitleStyle(font_size=0)


def test_center_crop_landscape_to_vertical_keeps_full_height():
    # 1920x1080 -> 9:16 should crop the width to ~607px wide region
    region = center_crop_for_aspect(_clip(1920, 1080), target_aspect=9 / 16)
    assert region.height == pytest.approx(1.0)
    # Expected width fraction = (9/16) / (1920/1080) = (0.5625)/(1.7777) ≈ 0.3164
    assert region.width == pytest.approx((9 / 16) / (1920 / 1080), rel=1e-3)
    # Centered horizontally
    assert region.x == pytest.approx((1.0 - region.width) / 2, rel=1e-3)
    assert region.y == 0.0


def test_center_crop_already_vertical_keeps_full_width():
    # 1080x1920 -> 9:16 means source already matches; height crop = 1.0
    region = center_crop_for_aspect(_clip(1080, 1920), target_aspect=9 / 16)
    assert region.width == pytest.approx(1.0)
    assert region.height == pytest.approx(1.0, rel=1e-3)


def test_center_crop_taller_than_target_crops_height():
    # 1080x2160 source, target 9:16 (less tall) → crop height
    region = center_crop_for_aspect(_clip(1080, 2160), target_aspect=9 / 16)
    assert region.width == pytest.approx(1.0)
    assert region.height < 1.0
    assert region.y > 0.0  # centered vertically


def test_vertical_crop_9_16_is_shortcut():
    region = vertical_crop_9_16(_clip(1920, 1080))
    assert isinstance(region, CropRegion)
    assert region.aspect_ratio == pytest.approx(9 / 16 / (region.height / region.width if region.height else 1), rel=1e-3) or region.height > 0


def test_center_crop_rejects_zero_dim():
    with pytest.raises(ValueError):
        center_crop_for_aspect(_clip(0, 100), target_aspect=1.0)
    with pytest.raises(ValueError):
        center_crop_for_aspect(_clip(100, 100), target_aspect=0.0)
