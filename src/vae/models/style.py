"""Subtitle and crop style models — describe how text/video should render."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Anchor = Literal[
    "top-left", "top-center", "top-right",
    "middle-left", "middle-center", "middle-right",
    "bottom-left", "bottom-center", "bottom-right",
]


class SubtitleStyle(BaseModel):
    """Visual style for a subtitle track.

    Coordinates are normalized to canvas (0..1) where applicable. Sizes use the
    same unit CapCut uses (display pt at 1080p reference height).
    """

    font_family: str = "Noto Sans CJK KR"
    font_size: int = Field(default=30, gt=0)
    color: str = "#FFFFFF"  # hex RGB
    outline_color: str = "#000000"
    outline_width: int = Field(default=2, ge=0)
    anchor: Anchor = "bottom-center"
    # offset from anchor in normalized canvas units (0..1)
    offset_x: float = 0.0
    offset_y: float = 0.05
    # Optional: highlight individual emphasis words
    emphasis_color: str | None = None
    emphasis_keywords: list[str] = Field(default_factory=list)


VLOG_SUBTITLE_STYLE = SubtitleStyle(
    font_family="Noto Sans CJK KR",
    font_size=30,
    color="#FFFFFF",
    outline_color="#000000",
    outline_width=2,
    anchor="bottom-center",
    offset_y=0.06,
)

SHORTS_SUBTITLE_STYLE = SubtitleStyle(
    font_family="Noto Sans CJK KR",
    font_size=60,
    color="#FFFFFF",
    outline_color="#000000",
    outline_width=4,
    anchor="middle-center",
    offset_y=0.0,
    emphasis_color="#FFD400",  # TikTok-style yellow accent
)


class CropRegion(BaseModel):
    """Normalized crop window (0..1 of source frame).

    `(x, y)` is top-left corner; `width`/`height` are dimensions.
    """

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height > 0 else 0.0
