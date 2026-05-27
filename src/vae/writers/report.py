"""Analysis report writer - emits JSON describing edit decisions."""

from __future__ import annotations

import json
from pathlib import Path

from vae.models.timeline import Timeline
from vae.pipeline.context import AnalysisContext


def write_report(
    ctx: AnalysisContext,
    timeline: Timeline,
    output: Path,
) -> Path:
    """Serialize the analysis context and timeline to a JSON report."""
    output.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "clips": [
            {
                "path": str(c.path),
                "duration": c.duration,
                "fps": c.fps,
                "resolution": [c.width, c.height],
                "has_audio": c.has_audio,
                "codec": c.codec,
            }
            for c in ctx.clips
        ],
        "silences": {
            str(path): [{"start": r.start, "end": r.end} for r in ranges]
            for path, ranges in ctx.silences.items()
        },
        "word_count": {
            str(path): len(words) for path, words in ctx.speech_words.items()
        },
        "timeline": {
            "width": timeline.width,
            "height": timeline.height,
            "fps": timeline.fps,
            "duration": timeline.duration,
            "tracks": [
                {
                    "kind": track.kind,
                    "segments": [
                        {
                            "source": str(seg.source),
                            "source_range": [seg.source_range.start, seg.source_range.end],
                            "timeline_start": seg.timeline_start,
                            "timeline_end": seg.timeline_end,
                            "reason": seg.reason,
                        }
                        for seg in track.segments
                    ],
                }
                for track in timeline.tracks
            ],
        },
    }

    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return output
