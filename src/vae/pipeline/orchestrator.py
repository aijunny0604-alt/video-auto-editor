"""Pipeline orchestrator - wires analyzers, rules, and writers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal

from vae.analyzers.audio import detect_silences
from vae.analyzers.loudness import analyze_loudness
from vae.analyzers.scene import detect_scenes
from vae.models.subtitle import Word
from vae.models.timeline import Timeline
from vae.pipeline.context import AnalysisContext
from vae.pipeline.rules.shorts import build_shorts_timelines
from vae.pipeline.rules.vlog import build_vlog_timeline
from vae.pipeline.subtitles import attach_subtitle_track, words_on_timeline
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
    loudness: bool = False,
    loudness_window: float = 1.0,
    scenes: bool = False,
) -> AnalysisContext:
    """Run analyzers over the given clips.

    Args:
        clips: Input file paths.
        transcribe_fn: Optional STT function. None skips transcription.
        loudness: If True, compute per-window RMS for highlight detection (shorts).
        scenes: If True, detect scene boundaries (vlog rule step 5 reference).
    """
    ctx = AnalysisContext()
    for path in clips:
        ctx.clips.append(probe_clip(path))
        ctx.silences[path] = detect_silences(
            path, noise_db=silence_noise_db, min_duration=silence_min_duration
        )
        if loudness:
            ctx.loudness[path] = analyze_loudness(path, window=loudness_window)
        if scenes:
            try:
                ctx.scenes[path] = detect_scenes(path)
            except Exception:  # noqa: BLE001 - scene failure shouldn't kill pipeline
                ctx.scenes[path] = []
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
    shorts_count: int = 3,
    shorts_length: float = 30.0,
) -> tuple[AnalysisContext, list[Timeline]]:
    """End-to-end: collect clips, analyze, build timeline(s) for the given mode.

    Returns:
        (context, list[Timeline]) - vlog always returns 1 timeline; shorts may
        return up to `shorts_count` timelines per input clip.
    """
    clips = collect_clips(input_dir)
    if not clips:
        raise ValueError(f"No supported media files in {input_dir}")

    if mode == "vlog":
        ctx = analyze(clips, transcribe_fn=transcribe_fn, scenes=True)
        timelines = [build_vlog_timeline(ctx)]
    elif mode == "shorts":
        ctx = analyze(clips, transcribe_fn=transcribe_fn, loudness=True)
        timelines = build_shorts_timelines(
            ctx,
            loudness_samples=ctx.loudness,
            target_length=shorts_length,
            top_n=shorts_count,
        )
        if not timelines:
            raise ValueError("shorts mode produced no timelines (no peaks found)")
    else:
        raise ValueError(f"unknown mode: {mode}")

    if ctx.speech_words:
        timelines = [
            attach_subtitle_track(tl, words_on_timeline(tl, ctx.speech_words))
            for tl in timelines
        ]

    return ctx, timelines
