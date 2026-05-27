"""CapCut draft writer - PLACEHOLDER until schema analysis is complete.

Currently emits a structural placeholder JSON. Once a sample CapCut project is
captured (see docs/02-design/capcut-schema.md), this writer will produce
draft_content.json compatible with CapCut Windows desktop.
"""

from __future__ import annotations

import json
from pathlib import Path

from vae.models.timeline import Timeline


def write_draft(timeline: Timeline, output_dir: Path) -> Path:
    """Write a placeholder draft.json describing the timeline.

    Returns the path to the generated file. Real CapCut draft generation lands
    after schema analysis (Phase 2 — pending user sample).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "draft.json"

    payload = {
        "_format": "vae-placeholder/v0",
        "_note": "Placeholder. Real CapCut draft_content.json pending schema analysis.",
        "canvas": {"width": timeline.width, "height": timeline.height, "fps": timeline.fps},
        "mode": timeline.mode,
        "duration_seconds": timeline.duration,
        "tracks": [
            {
                "kind": t.kind,
                "subtitle_style": (
                    t.subtitle_style.model_dump() if t.subtitle_style is not None else None
                ),
                "segments": [
                    {
                        "source": str(s.source),
                        "source_start": s.source_range.start,
                        "source_end": s.source_range.end,
                        "timeline_start": s.timeline_start,
                        "reason": s.reason,
                        "crop": s.crop.model_dump() if s.crop is not None else None,
                    }
                    for s in t.segments
                ],
            }
            for t in timeline.tracks
        ],
    }

    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return target
