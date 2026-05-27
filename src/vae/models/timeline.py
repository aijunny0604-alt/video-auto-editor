from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from vae.models.clip import TimeRange
from vae.models.style import CropRegion, SubtitleStyle


class Segment(BaseModel):
    source: Path
    source_range: TimeRange
    timeline_start: float = Field(ge=0)
    reason: str = ""
    crop: CropRegion | None = None

    @property
    def timeline_end(self) -> float:
        return self.timeline_start + self.source_range.duration


class Track(BaseModel):
    kind: Literal["video", "audio", "subtitle"]
    segments: list[Segment] = Field(default_factory=list)
    subtitle_style: SubtitleStyle | None = None


class Timeline(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: float = Field(gt=0)
    tracks: list[Track] = Field(default_factory=list)
    mode: str | None = None  # "vlog" | "shorts" — informational

    @property
    def duration(self) -> float:
        if not self.tracks:
            return 0.0
        return max(
            (seg.timeline_end for track in self.tracks for seg in track.segments),
            default=0.0,
        )
