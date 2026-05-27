"use client";

type Segment = {
  source: string;
  source_range: [number, number];
  timeline_start: number;
  timeline_end: number;
  reason: string;
};

type Track = {
  kind: "video" | "audio" | "subtitle";
  segments: Segment[];
};

type Report = {
  timeline: {
    width: number;
    height: number;
    fps: number;
    duration: number;
    mode: string | null;
    tracks: Track[];
  };
};

const REASON_COLOR: Record<string, string> = {
  speech: "bg-emerald-500",
  scene_keep: "bg-cyan-500",
  highlight_peak: "bg-fuchsia-500",
  intro_window: "bg-amber-500",
};

type TimelineProps = {
  report: Report | null;
  onSegmentClick?: (sourceTime: number) => void;
};

export default function TimelinePreview({ report, onSegmentClick }: TimelineProps) {
  if (!report) {
    return (
      <div className="rounded-xl border border-dashed border-neutral-800 bg-neutral-900/30 p-6 text-center text-sm text-neutral-500">
        타임라인 데이터 대기 중…
      </div>
    );
  }

  const tl = report.timeline;
  const totalDuration = Math.max(tl.duration, 0.001);

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold">타임라인 미리보기</h3>
        <span className="text-xs text-neutral-500">
          {tl.width}×{tl.height} · {tl.fps.toFixed(1)}fps · {tl.duration.toFixed(2)}s
          {tl.mode && ` · ${tl.mode}`}
        </span>
      </div>

      <div className="space-y-3">
        {tl.tracks.map((track, ti) => (
          <div key={ti}>
            <p className="mb-1 text-xs uppercase tracking-wide text-neutral-500">{track.kind}</p>
            <div className="relative h-8 overflow-hidden rounded bg-neutral-950">
              {track.segments.map((seg, si) => {
                const left = (seg.timeline_start / totalDuration) * 100;
                const width = ((seg.timeline_end - seg.timeline_start) / totalDuration) * 100;
                const color = REASON_COLOR[seg.reason] ?? "bg-neutral-600";
                const clickable = !!onSegmentClick && track.kind === "video";
                return (
                  <button
                    key={si}
                    type="button"
                    onClick={
                      clickable
                        ? () => onSegmentClick?.(seg.source_range[0])
                        : undefined
                    }
                    title={`${seg.reason} · 원본 ${seg.source_range[0].toFixed(2)}→${seg.source_range[1].toFixed(2)}s${clickable ? " · 클릭하면 원본 재생" : ""}`}
                    className={`absolute top-0 h-full border-r border-neutral-950 ${color} opacity-80 transition hover:opacity-100 ${clickable ? "cursor-pointer hover:ring-2 hover:ring-white" : ""}`}
                    style={{ left: `${left}%`, width: `${Math.max(width, 0.5)}%` }}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-neutral-500">
        {Object.entries(REASON_COLOR).map(([reason, color]) => (
          <div key={reason} className="flex items-center gap-1.5">
            <span className={`inline-block h-2.5 w-2.5 rounded-sm ${color}`} />
            <span>{reason}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
