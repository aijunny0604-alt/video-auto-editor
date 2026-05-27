"""Crop region calculation helpers."""

from __future__ import annotations

from vae.models.clip import ClipMeta
from vae.models.style import CropRegion


def center_crop_for_aspect(
    clip: ClipMeta,
    target_aspect: float,
) -> CropRegion:
    """Return a normalized center crop that fits the given aspect ratio.

    Args:
        clip: Source clip (uses width/height).
        target_aspect: Desired width/height ratio (e.g. 9/16 ≈ 0.5625 for shorts).

    Returns:
        CropRegion in normalized coords (0..1 of source frame).
    """
    if clip.width <= 0 or clip.height <= 0:
        raise ValueError("clip has zero dimension")
    if target_aspect <= 0:
        raise ValueError("target_aspect must be positive")

    source_aspect = clip.width / clip.height

    if source_aspect > target_aspect:
        # Source is wider than target → crop width
        crop_norm_width = target_aspect / source_aspect
        return CropRegion(
            x=(1.0 - crop_norm_width) / 2,
            y=0.0,
            width=crop_norm_width,
            height=1.0,
        )
    else:
        # Source is taller (or equal) → crop height
        crop_norm_height = source_aspect / target_aspect
        return CropRegion(
            x=0.0,
            y=(1.0 - crop_norm_height) / 2,
            width=1.0,
            height=crop_norm_height,
        )


def vertical_crop_9_16(clip: ClipMeta) -> CropRegion:
    """Shortcut for shorts canvas: 9:16 center crop."""
    return center_crop_for_aspect(clip, target_aspect=9 / 16)
