"""Scene analyzer - shot boundary detection via PySceneDetect."""

from __future__ import annotations

from pathlib import Path

from vae.models.clip import TimeRange


def detect_scenes(
    path: Path,
    threshold: float = 27.0,
    min_scene_len: float = 1.0,
) -> list[TimeRange]:
    """Detect scene (shot) boundaries.

    Returns scene ranges covering the entire clip. If PySceneDetect is unavailable
    or detection finds no cuts, returns a single range covering the whole clip.

    Args:
        path: Input video file.
        threshold: ContentDetector threshold (lower = more cuts).
        min_scene_len: Minimum scene duration in seconds.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    try:
        from scenedetect import ContentDetector, SceneManager, open_video  # type: ignore[import]
    except ImportError:
        return _whole_clip_fallback(path)

    video = open_video(str(path))
    manager = SceneManager()
    manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=int(min_scene_len * video.frame_rate))
    )
    manager.detect_scenes(video=video)

    scenes = manager.get_scene_list()
    if not scenes:
        return _whole_clip_fallback(path)

    return [
        TimeRange(start=start.get_seconds(), end=end.get_seconds()) for start, end in scenes
    ]


def _whole_clip_fallback(path: Path) -> list[TimeRange]:
    from vae.utils.ffmpeg import probe_duration

    duration = probe_duration(path)
    return [TimeRange(start=0.0, end=duration)] if duration > 0 else []
