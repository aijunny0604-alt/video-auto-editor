"""FFmpeg / ffprobe wrapper helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from vae.models.clip import ClipMeta


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def probe_duration(path: Path) -> float:
    """Return clip duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def probe_clip(path: Path) -> ClipMeta:
    """Probe a media file and return ClipMeta."""
    if not path.exists():
        raise FileNotFoundError(path)

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio_stream = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    duration = float(data["format"].get("duration", 0.0))

    if video_stream is None:
        # audio-only file
        return ClipMeta(
            path=path,
            duration=duration,
            fps=1.0,
            width=1,
            height=1,
            has_audio=audio_stream is not None,
            codec=audio_stream["codec_name"] if audio_stream else "unknown",
        )

    fps_str = video_stream.get("r_frame_rate", "30/1")
    num, _, den = fps_str.partition("/")
    fps = float(num) / float(den) if den and float(den) != 0 else 30.0

    return ClipMeta(
        path=path,
        duration=duration,
        fps=fps,
        width=int(video_stream["width"]),
        height=int(video_stream["height"]),
        has_audio=audio_stream is not None,
        codec=video_stream["codec_name"],
    )
