from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vae.models.clip import ClipMeta, TimeRange
from vae.models.subtitle import Word


@dataclass
class AnalysisContext:
    """Bundles analyzer outputs keyed by clip path."""

    clips: list[ClipMeta] = field(default_factory=list)
    silences: dict[Path, list[TimeRange]] = field(default_factory=dict)
    speech_words: dict[Path, list[Word]] = field(default_factory=dict)
    scenes: dict[Path, list[TimeRange]] = field(default_factory=dict)

    def clip_by_path(self, path: Path) -> ClipMeta:
        for c in self.clips:
            if c.path == path:
                return c
        raise KeyError(path)
