"""FastAPI app — REST + WebSocket for the GUI dashboard."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vae.utils.paths import list_capcut_projects
from web.backend.jobs import Job, manager

app = FastAPI(title="video-auto-editor GUI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _bind_loop() -> None:
    manager.bind_loop(asyncio.get_event_loop())


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class JobRequest(BaseModel):
    mode: str
    input_dir: str
    output_dir: str
    shorts_count: int = 3
    shorts_length: float = 30.0
    use_stt: bool = False


class JobResponse(BaseModel):
    id: str
    mode: str
    status: str
    input_dir: str
    output_dir: str
    error: str | None = None
    event_count: int
    artifact_count: int

    @classmethod
    def from_job(cls, job: Job) -> "JobResponse":
        return cls(
            id=job.id,
            mode=job.mode,
            status=job.status,
            input_dir=str(job.input_dir),
            output_dir=str(job.output_dir),
            error=job.error,
            event_count=len(job.events),
            artifact_count=len(job.artifacts),
        )


# ---------------------------------------------------------------------------
# REST
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/capcut/projects")
def capcut_projects() -> dict[str, list[str]]:
    return {"projects": [str(p) for p in list_capcut_projects()]}


@app.get("/api/folders/list")
def list_folder(path: str) -> dict:
    """Return media files in a folder for the input picker."""
    target = Path(path)
    if not target.exists() or not target.is_dir():
        raise HTTPException(404, f"directory not found: {path}")
    exts = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".wav", ".mp3", ".m4a"}
    files = sorted(
        [
            {"name": p.name, "size": p.stat().st_size}
            for p in target.iterdir()
            if p.is_file() and p.suffix.lower() in exts
        ],
        key=lambda x: x["name"],
    )
    return {"path": str(target), "files": files}


@app.post("/api/jobs", response_model=JobResponse)
def create_job(req: JobRequest) -> JobResponse:
    try:
        job = manager.submit(
            mode=req.mode,
            input_dir=Path(req.input_dir),
            output_dir=Path(req.output_dir),
            shorts_count=req.shorts_count,
            shorts_length=req.shorts_length,
            use_stt=req.use_stt,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return JobResponse.from_job(job)


@app.get("/api/jobs", response_model=list[JobResponse])
def list_jobs() -> list[JobResponse]:
    return [JobResponse.from_job(j) for j in manager.list_jobs()]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return {
        **JobResponse.from_job(job).model_dump(),
        "events": [e.model_dump() for e in job.events],
        "artifacts": job.artifacts,
    }


@app.get("/api/jobs/{job_id}/artifact")
def get_artifact(job_id: str, name: str) -> dict:
    """Return artifact content (JSON only, for timeline preview)."""
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    for path_str in job.artifacts:
        path = Path(path_str)
        if path.name == name and path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(404, f"artifact {name} not found")


# ---------------------------------------------------------------------------
# WebSocket — live event stream
# ---------------------------------------------------------------------------

@app.websocket("/ws/jobs/{job_id}")
async def job_stream(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    try:
        queue = manager.subscribe(job_id)
    except KeyError:
        await ws.send_json({"kind": "error", "message": "job not found"})
        await ws.close()
        return

    try:
        while True:
            event = await queue.get()
            await ws.send_json(event.model_dump(mode="json"))
            if event.kind in ("pipeline_done", "error") and manager.get(job_id) and \
                    manager.get(job_id).status in ("done", "error"):
                # Drain any remaining events then close
                while not queue.empty():
                    pending = queue.get_nowait()
                    await ws.send_json(pending.model_dump(mode="json"))
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(job_id, queue)
        try:
            await ws.close()
        except RuntimeError:
            pass
