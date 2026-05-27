"""Pipeline orchestrator - wires analyzers, rules, and writers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal

from vae.analyzers.audio import detect_silences
from vae.models.subtitle import Word
from vae.models.timeline import Timeline
from vae.pipeline.context import AnalysisContext
from vae.pipeline.rules.vlog import build_vlog_timeline
from vae.utils.ffmpeg import probe_clip

Mode = Literal["vlog", "shorts"]

# Type alias for STT injection (skips real model in tests)
TranscribeFn = Callable[[Path], list[Word]]


def collect_clips(input_dir: Path) -> list[Path]:
    """Return sorted list of supported video/audio files in input_dir."""
    exts = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".wav", ".mp3", ".m4a"}
    return sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in exts)


def analyze(
    clips: list[Path],
    transcribe_fn: TranscribeFn | None = None,
    silence_noise_db: float = -30.0,
    silence_min_duration: float = 0.5,
) -> AnalysisContext:
    """Run analyzers over the given clips.

    Args:
        clips: Input file paths.
        transcribe_fn: Optional STT function. None skips transcription (faster, no GPU).
    """
    ctx = AnalysisContext()
    for path in clips:
        ctx.clips.append(probe_clip(path))
        ctx.silences[path] = detect_silences(
            path, noise_db=silence_noise_db, min_duration=silence_min_duration
        )
        if transcribe_fn is not None:
            try:
                ctx.speech_words[path] = transcribe_fn(path)
            except Exception:  # noqa: BLE001 - STT failure shouldn't kill pipeline
                ctx.speech_words[path] = []
    return ctx


def run_pipeline(
    mode: Mode,
    input_dir: Path,
    transcribe_fn: TranscribeFn | None = None,
) -> tuple[AnalysisContext, Timeline]:
    """End-to-end: collect clips, analyze, build timeline for the given mode."""
    clips = collect_clips(input_dir)
    if not clips:
        raise ValueError(f"No supported media files in {input_dir}")

    ctx = analyze(clips, transcribe_fn=transcribe_fn)

    if mode == "vlog":
        timeline = build_vlog_timeline(ctx)
    elif mode == "shorts":
        # Shorts mode reuses vlog logic for now; specialized rule lands in Phase 3.
        timeline = build_vlog_timeline(ctx)
    else:
        raise ValueError(f"unknown mode: {mode}")

    return ctx, timeline
