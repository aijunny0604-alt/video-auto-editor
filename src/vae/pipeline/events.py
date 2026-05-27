"""Pipeline event types for streaming progress to GUI / log consumers."""

from __future__ import annotations

import time
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field

EventKind = Literal[
    "pipeline_start",
    "clip_start",
    "stage_start",
    "stage_progress",
    "stage_done",
    "clip_done",
    "timeline_built",
    "writer_done",
    "log",
    "error",
    "pipeline_done",
]


class PipelineEvent(BaseModel):
    kind: EventKind
    ts: float = Field(default_factory=time.time)
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


EventEmitter = Callable[[PipelineEvent], None]


def noop_emitter(event: PipelineEvent) -> None:
    return None
