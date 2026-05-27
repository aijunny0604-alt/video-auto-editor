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
from vae.pipeline.events import EventEmitter, PipelineEvent, noop_emitter
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
    emit: EventEmitter = noop_emitter,
) -> AnalysisContext:
    """Run analyzers over the given clips.

    Args:
        clips: Input file paths.
        transcribe_fn: Optional STT function. None skips transcription.
        loudness: If True, compute per-window RMS for highlight detection (shorts).
        scenes: If True, detect scene boundaries.
        emit: Event callback for progress streaming (default = no-op).
    """
    ctx = AnalysisContext()
    total = len(clips)
    for index, path in enumerate(clips, start=1):
        emit(
            PipelineEvent(
                kind="clip_start",
                message=f"clip {index}/{total}: {path.name}",
                data={"index": index, "total": total, "path": str(path)},
            )
        )

        emit(PipelineEvent(kind="stage_start", message="probe", data={"stage": "probe", "clip": str(path)}))
        ctx.clips.append(probe_clip(path))
        emit(PipelineEvent(kind="stage_done", message="probe", data={"stage": "probe", "clip": str(path)}))

        emit(PipelineEvent(kind="stage_start", message="silence", data={"stage": "silence", "clip": str(path)}))
        ctx.silences[path] = detect_silences(
            path, noise_db=silence_noise_db, min_duration=silence_min_duration
        )
        emit(
            PipelineEvent(
                kind="stage_done",
                message=f"silence: {len(ctx.silences[path])} ranges",
                data={"stage": "silence", "clip": str(path), "count": len(ctx.silences[path])},
            )
        )

        if loudness:
            emit(PipelineEvent(kind="stage_start", message="loudness", data={"stage": "loudness", "clip": str(path)}))
            ctx.loudness[path] = analyze_loudness(path, window=loudness_window)
            emit(
                PipelineEvent(
                    kind="stage_done",
                    message=f"loudness: {len(ctx.loudness[path])} samples",
                    data={"stage": "loudness", "clip": str(path), "samples": len(ctx.loudness[path])},
                )
            )

        if scenes:
            emit(PipelineEvent(kind="stage_start", message="scenes", data={"stage": "scenes", "clip": str(path)}))
            try:
                ctx.scenes[path] = detect_scenes(path)
            except Exception:  # noqa: BLE001
                ctx.scenes[path] = []
            emit(
                PipelineEvent(
                    kind="stage_done",
                    message=f"scenes: {len(ctx.scenes[path])}",
                    data={"stage": "scenes", "clip": str(path), "count": len(ctx.scenes[path])},
                )
            )

        if transcribe_fn is not None:
            emit(PipelineEvent(kind="stage_start", message="stt", data={"stage": "stt", "clip": str(path)}))
            try:
                ctx.speech_words[path] = transcribe_fn(path)
            except Exception as exc:  # noqa: BLE001
                ctx.speech_words[path] = []
                emit(PipelineEvent(kind="error", message=f"stt failed: {exc}", data={"clip": str(path)}))
            emit(
                PipelineEvent(
                    kind="stage_done",
                    message=f"stt: {len(ctx.speech_words.get(path, []))} words",
                    data={"stage": "stt", "clip": str(path), "words": len(ctx.speech_words.get(path, []))},
                )
            )

        emit(
            PipelineEvent(
                kind="clip_done",
                message=f"clip {index}/{total} done",
                data={"index": index, "total": total, "path": str(path)},
            )
        )
    return ctx


def run_pipeline(
    mode: Mode,
    input_dir: Path,
    transcribe_fn: TranscribeFn | None = None,
    shorts_count: int = 3,
    shorts_length: float = 30.0,
    emit: EventEmitter = noop_emitter,
) -> tuple[AnalysisContext, list[Timeline]]:
    """End-to-end: collect clips, analyze, build timeline(s) for the given mode."""
    clips = collect_clips(input_dir)
    if not clips:
        raise ValueError(f"No supported media files in {input_dir}")

    emit(
        PipelineEvent(
            kind="pipeline_start",
            message=f"mode={mode} clips={len(clips)}",
            data={"mode": mode, "clip_count": len(clips), "input_dir": str(input_dir)},
        )
    )

    if mode == "vlog":
        ctx = analyze(clips, transcribe_fn=transcribe_fn, scenes=True, emit=emit)
        timelines = [build_vlog_timeline(ctx)]
    elif mode == "shorts":
        ctx = analyze(clips, transcribe_fn=transcribe_fn, loudness=True, emit=emit)
        timelines = build_shorts_timelines(
            ctx,
            loudness_samples=ctx.loudness,
            target_length=shorts_length,
            top_n=shorts_count,
        )
        if not timelines:
            emit(PipelineEvent(kind="error", message="no peaks → no shorts produced"))
            raise ValueError("shorts mode produced no timelines (no peaks found)")
    else:
        raise ValueError(f"unknown mode: {mode}")

    if ctx.speech_words:
        timelines = [
            attach_subtitle_track(tl, words_on_timeline(tl, ctx.speech_words))
            for tl in timelines
        ]

    for i, tl in enumerate(timelines, start=1):
        emit(
            PipelineEvent(
                kind="timeline_built",
                message=f"timeline #{i}: {tl.duration:.2f}s",
                data={
                    "index": i,
                    "total": len(timelines),
                    "duration": tl.duration,
                    "width": tl.width,
                    "height": tl.height,
                    "mode": tl.mode,
                    "segment_count": sum(len(t.segments) for t in tl.tracks),
                },
            )
        )

    emit(PipelineEvent(kind="pipeline_done", message=f"produced {len(timelines)} timeline(s)"))
    return ctx, timelines
