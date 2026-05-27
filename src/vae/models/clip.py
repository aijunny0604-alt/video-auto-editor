from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class TimeRange(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(ge=0)

    @model_validator(mode="after")
    def _check_order(self) -> "TimeRange":
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")
        return self

    @property
    def duration(self) -> float:
        return self.end - self.start

    def overlaps(self, other: "TimeRange") -> bool:
        return self.start < other.end and other.start < self.end


class ClipMeta(BaseModel):
    path: Path
    duration: float = Field(gt=0)
    fps: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    has_audio: bool
    codec: str
