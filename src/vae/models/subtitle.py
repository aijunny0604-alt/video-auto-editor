from __future__ import annotations

from pydantic import BaseModel, Field


class Word(BaseModel):
    text: str
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    confidence: float | None = None


class Subtitle(BaseModel):
    text: str
    start: float
    end: float
    words: list[Word] = Field(default_factory=list)
