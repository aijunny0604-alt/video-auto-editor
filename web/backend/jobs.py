"""In-memory job manager. Runs pipeline in a thread and broadcasts events."""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from vae.analyzers.stt import words_to_subtitles
from vae.pipeline.events import PipelineEvent
from vae.pipeline.orchestrator import run_pipeline
from vae.pipeline.subtitles import words_on_timeline
from vae.utils.bgm import find_bgm
from vae.writers.capcut import write_draft
from vae.writers.renderer import RenderOptions, render_timeline
from vae.writers.report import write_report

JobStatus = Literal["pending", "running", "done", "error"]


@dataclass
class Job:
    id: str
    mode: str
    input_dir: Path
    output_dir: Path
    shorts_count: int = 3
    shorts_length: float = 30.0
    use_stt: bool = False
    render: bool = True
    bgm_volume: float = 0.18
    transition: str = "fade"
    status: JobStatus = "pending"
    error: str | None = None
    events: list[PipelineEvent] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def list_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def submit(
        self,
        mode: str,
        input_dir: Path,
        output_dir: Path,
        shorts_count: int = 3,
        shorts_length: float = 30.0,
        use_stt: bool = False,
        render: bool = True,
        bgm_volume: float = 0.18,
        transition: str = "fade",
    ) -> Job:
        if mode not in ("vlog", "shorts"):
            raise ValueError(f"invalid mode: {mode}")
        if not input_dir.exists():
            raise FileNotFoundError(f"input_dir not found: {input_dir}")

        job_id = uuid.uuid4().hex[:12]
        job = Job(
            id=job_id,
            mode=mode,
            input_dir=input_dir,
            output_dir=output_dir,
            shorts_count=shorts_count,
            shorts_length=shorts_length,
            use_stt=use_stt,
            render=render,
            bgm_volume=bgm_volume,
            transition=transition,
        )
        with self._lock:
            self._jobs[job_id] = job
            self._subscribers[job_id] = []

        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()
        return job

    def subscribe(self, job_id: str) -> asyncio.Queue:
        """Return an asyncio.Queue that will receive PipelineEvent objects.

        Existing events are replayed first so late subscribers see the full log.
        """
        queue: asyncio.Queue = asyncio.Queue()
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            for ev in job.events:
                queue.put_nowait(ev)
            self._subscribers[job_id].append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        with self._lock:
            if job_id in self._subscribers and queue in self._subscribers[job_id]:
                self._subscribers[job_id].remove(queue)

    # ------------------------------------------------------------------
    def _emit(self, job: Job, event: PipelineEvent) -> None:
        job.events.append(event)
        loop = self._loop
        if loop is None:
            return
        with self._lock:
            queues = list(self._subscribers.get(job.id, []))
        for q in queues:
            try:
                loop.call_soon_threadsafe(q.put_nowait, event)
            except RuntimeError:
                pass

    def _run_job(self, job: Job) -> None:
        job.status = "running"
        try:
            transcribe_fn = None
            if job.use_stt:
                from vae.analyzers.stt import transcribe as _transcribe

                def transcribe_fn(p: Path):
                    return _transcribe(p)

            ctx, timelines = run_pipeline(
                job.mode,
                job.input_dir,
                transcribe_fn=transcribe_fn,
                shorts_count=job.shorts_count,
                shorts_length=job.shorts_length,
                emit=lambda ev: self._emit(job, ev),
            )

            job.output_dir.mkdir(parents=True, exist_ok=True)
            bgm_path = find_bgm(job.input_dir)
            for i, tl in enumerate(timelines, start=1):
                suffix = "" if len(timelines) == 1 else f"_{i:02d}"
                report = write_report(ctx, tl, job.output_dir / f"analysis_report{suffix}.json")
                draft = write_draft(tl, job.output_dir / f"capcut_project{suffix}")
                job.artifacts.append(str(report))
                job.artifacts.append(str(draft))
                self._emit(
                    job,
                    PipelineEvent(
                        kind="writer_done",
                        message=f"wrote timeline #{i} (report + draft)",
                        data={
                            "index": i,
                            "report": str(report),
                            "draft": str(draft),
                        },
                    ),
                )

                if job.render:
                    self._emit(
                        job,
                        PipelineEvent(
                            kind="stage_start",
                            message=f"render #{i} (ffmpeg)",
                            data={"stage": "render", "index": i},
                        ),
                    )
                    try:
                        tl_words = (
                            words_on_timeline(tl, ctx.speech_words)
                            if ctx.speech_words
                            else []
                        )
                        tl_subs = words_to_subtitles(tl_words) if tl_words else []
                        opts = RenderOptions(
                            burn_subtitles=bool(tl_subs),
                            transition=job.transition,
                            bgm_path=bgm_path,
                            bgm_volume=job.bgm_volume,
                        )
                        out_mp4 = job.output_dir / f"final{suffix}.mp4"
                        render_timeline(tl, out_mp4, subtitles=tl_subs, options=opts)
                        job.artifacts.append(str(out_mp4))
                        self._emit(
                            job,
                            PipelineEvent(
                                kind="stage_done",
                                message=f"render #{i} done · {out_mp4.stat().st_size // 1024}KB",
                                data={
                                    "stage": "render",
                                    "index": i,
                                    "output": str(out_mp4),
                                    "bytes": out_mp4.stat().st_size,
                                },
                            ),
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._emit(
                            job,
                            PipelineEvent(
                                kind="error",
                                message=f"render #{i} failed: {exc}",
                                data={"stage": "render", "index": i},
                            ),
                        )

            job.status = "done"
            self._emit(job, PipelineEvent(kind="pipeline_done", message="ok"))
        except Exception as exc:  # noqa: BLE001
            job.status = "error"
            job.error = str(exc)
            self._emit(job, PipelineEvent(kind="error", message=str(exc)))


manager = JobManager()
