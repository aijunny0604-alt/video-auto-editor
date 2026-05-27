/**
 * Demo mode: replay a captured pipeline run so the GitHub Pages build works
 * without a backend. Real data was recorded from a live run on 2026-05-27.
 */

import type { JobSummary, PipelineEvent } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export const IS_DEMO =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_DEMO_MODE === "1";

type JobPayload = {
  id: string;
  mode: string;
  status: "done";
  input_dir: string;
  output_dir: string;
  error: null;
  event_count: number;
  artifact_count: number;
  events: PipelineEvent[];
  artifacts: string[];
};

export async function loadDemoJob(): Promise<JobPayload> {
  const res = await fetch(`${BASE}/demo/job.json`);
  return res.json();
}

export async function loadDemoReport(name: string): Promise<unknown> {
  const res = await fetch(`${BASE}/demo/${name}`);
  return res.json();
}

export function summary(job: JobPayload): JobSummary {
  return {
    id: job.id,
    mode: job.mode,
    status: job.status,
    input_dir: job.input_dir,
    output_dir: job.output_dir,
    error: null,
    event_count: job.event_count,
    artifact_count: job.artifact_count,
  };
}

/**
 * Replay events with their original time gaps (compressed to feel snappy).
 * Returns a cleanup function to cancel the replay.
 */
export function replayEvents(
  events: PipelineEvent[],
  onEvent: (event: PipelineEvent) => void,
  onDone: () => void,
  speed = 8,
): () => void {
  let cancelled = false;
  const timers: ReturnType<typeof setTimeout>[] = [];
  const t0 = events[0]?.ts ?? 0;

  events.forEach((ev, i) => {
    const delay = ((ev.ts - t0) * 1000) / speed;
    const handle = setTimeout(() => {
      if (cancelled) return;
      onEvent(ev);
      if (i === events.length - 1) onDone();
    }, Math.max(delay, i * 30));
    timers.push(handle);
  });

  return () => {
    cancelled = true;
    timers.forEach(clearTimeout);
  };
}
