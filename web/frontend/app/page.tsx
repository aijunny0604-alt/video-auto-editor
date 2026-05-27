"use client";

import { useEffect, useMemo, useState } from "react";
import JobForm from "@/components/JobForm";
import LogStream from "@/components/LogStream";
import Metrics from "@/components/Metrics";
import ProgressBar from "@/components/ProgressBar";
import TimelinePreview from "@/components/TimelinePreview";
import type { JobSummary, PipelineEvent } from "@/lib/api";
import { getArtifact, openJobWebSocket } from "@/lib/api";

export default function Home() {
  const [job, setJob] = useState<JobSummary | null>(null);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [report, setReport] = useState<unknown | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!job) return;
    setEvents([]);
    setReport(null);
    setConnected(true);
    const ws = openJobWebSocket(
      job.id,
      (ev) => setEvents((prev) => [...prev, ev]),
      () => setConnected(false),
    );
    return () => {
      ws.close();
    };
  }, [job]);

  const clipProgress = useMemo(() => {
    const lastClipEvent = [...events].reverse().find((e) => e.kind === "clip_start" || e.kind === "clip_done");
    if (!lastClipEvent) return { current: 0, total: 0 };
    return {
      current: (lastClipEvent.data.index as number) ?? 0,
      total: (lastClipEvent.data.total as number) ?? 0,
    };
  }, [events]);

  const status = useMemo(() => {
    if (!job) return "대기";
    if (events.find((e) => e.kind === "pipeline_done")) return "완료";
    if (events.find((e) => e.kind === "error")) return "오류";
    if (events.length > 0) return "실행 중";
    return job.status;
  }, [job, events]);

  useEffect(() => {
    if (!job) return;
    const writerEvent = events.find((e) => e.kind === "writer_done");
    if (!writerEvent) return;
    const reportPath = String(writerEvent.data.report ?? "");
    const name = reportPath.split(/[\\/]/).pop();
    if (!name) return;
    getArtifact(job.id, name)
      .then((r) => setReport(r))
      .catch(() => setReport(null));
  }, [job, events]);

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-6">
      <header className="flex items-end justify-between border-b border-neutral-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">🎬 video-auto-editor</h1>
          <p className="text-sm text-neutral-400">브이로그 · 숏폼 자동 컷편집 대시보드</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span
            className={`inline-flex h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-neutral-600"}`}
          />
          <span className="text-neutral-400">{connected ? "WebSocket 연결됨" : "대기"}</span>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[420px,1fr]">
        <aside>
          <JobForm onCreated={setJob} />
        </aside>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center gap-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
            <div>
              <p className="text-xs text-neutral-400">상태</p>
              <p className="text-lg font-semibold">{status}</p>
            </div>
            {job && (
              <>
                <div>
                  <p className="text-xs text-neutral-400">Job ID</p>
                  <p className="font-mono text-sm">{job.id}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-400">모드</p>
                  <p className="text-sm">{job.mode}</p>
                </div>
              </>
            )}
            <div className="ml-auto w-full max-w-sm">
              <ProgressBar
                current={clipProgress.current}
                total={clipProgress.total}
                label="클립 처리"
              />
            </div>
          </div>

          <Metrics events={events} />

          <div className="grid gap-4 xl:grid-cols-2">
            <LogStream events={events} />
            <TimelinePreview report={report as any} />
          </div>
        </section>
      </div>

      <footer className="pt-6 text-center text-xs text-neutral-600">
        FastAPI :8000 · Next.js :3000 · 같은 머신 로컬 실행 권장
      </footer>
    </main>
  );
}
