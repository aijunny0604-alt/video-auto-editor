"use client";

import { useEffect, useRef } from "react";
import type { PipelineEvent } from "@/lib/api";

const KIND_COLOR: Record<string, string> = {
  pipeline_start: "text-emerald-400",
  pipeline_done: "text-emerald-400",
  clip_start: "text-cyan-400",
  clip_done: "text-cyan-400",
  stage_start: "text-neutral-400",
  stage_done: "text-neutral-200",
  stage_progress: "text-yellow-300",
  timeline_built: "text-fuchsia-400",
  writer_done: "text-fuchsia-300",
  error: "text-rose-400",
  log: "text-neutral-300",
};

export default function LogStream({ events }: { events: PipelineEvent[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [events.length]);

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950">
      <div className="flex items-center justify-between border-b border-neutral-800 px-4 py-2.5">
        <h3 className="text-sm font-medium">실시간 로그</h3>
        <span className="text-xs text-neutral-500">{events.length} events</span>
      </div>
      <div ref={scrollRef} className="max-h-96 overflow-y-auto px-4 py-3 font-mono text-xs leading-relaxed">
        {events.length === 0 ? (
          <p className="text-neutral-600">대기 중…</p>
        ) : (
          events.map((ev, i) => {
            const time = new Date(ev.ts * 1000).toLocaleTimeString("ko-KR", { hour12: false });
            const color = KIND_COLOR[ev.kind] ?? "text-neutral-300";
            return (
              <div key={i} className="flex gap-3 py-0.5">
                <span className="shrink-0 text-neutral-600">{time}</span>
                <span className={`shrink-0 ${color}`}>[{ev.kind}]</span>
                <span className="text-neutral-200">{ev.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
