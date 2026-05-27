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


def face_aware_crop(
    clip: ClipMeta,
    faces: list,  # list[FaceTrack] — kept untyped to avoid analyzers import cycle
    target_aspect: float,
    time: float = 0.0,
) -> CropRegion:
    """Compute crop region that keeps the primary face centered.

    Falls back to center_crop_for_aspect when no usable face data exists at the
    given time. The "primary" face is the track with the most samples that has
    a valid centroid at `time` (nearest-sample lookup).

    Args:
        clip: Source clip metadata.
        faces: List of FaceTrack from detect_faces().
        target_aspect: Desired width/height ratio (e.g. 9/16 for shorts).
        time: Seconds into the clip at which to sample the face position.
    """
    if not faces:
        return center_crop_for_aspect(clip, target_aspect)

    # Prefer tracks with more samples (longer-lived = more reliable).
    candidates = sorted(faces, key=lambda f: -len(getattr(f, "samples", [])))
    center = None
    for track in candidates:
        c = track.center_at(time) if hasattr(track, "center_at") else None
        if c is not None:
            center = c
            break

    if center is None:
        return center_crop_for_aspect(clip, target_aspect)

    cx, cy = center
    source_aspect = clip.width / clip.height if clip.height > 0 else 1.0

    if source_aspect > target_aspect:
        # Crop width — full height, slide horizontally to follow face
        crop_w = target_aspect / source_aspect
        x = cx - crop_w / 2
        x = max(0.0, min(1.0 - crop_w, x))
        return CropRegion(x=x, y=0.0, width=crop_w, height=1.0)
    else:
        # Crop height — full width, slide vertically
        crop_h = source_aspect / target_aspect
        y = cy - crop_h / 2
        y = max(0.0, min(1.0 - crop_h, y))
        return CropRegion(x=0.0, y=y, width=1.0, height=crop_h)
