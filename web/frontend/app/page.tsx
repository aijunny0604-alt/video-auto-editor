"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import HowToUse from "@/components/HowToUse";
import JobForm from "@/components/JobForm";
import LogStream from "@/components/LogStream";
import Metrics from "@/components/Metrics";
import ProgressBar from "@/components/ProgressBar";
import TimelinePreview from "@/components/TimelinePreview";
import VideoPlayer, { type VideoPlayerHandle, type VideoTab } from "@/components/VideoPlayer";
import type { JobSummary, PipelineEvent } from "@/lib/api";
import { getArtifact, openJobWebSocket } from "@/lib/api";
import { IS_DEMO, loadDemoJob, loadDemoReport, replayEvents, summary } from "@/lib/demo";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const DEMO_VIDEO_TABS: VideoTab[] = [
  {
    key: "original",
    label: "🎬 원본 (16:9)",
    src: `${BASE}/demo/original.mp4`,
    ratio: "16-9",
    caption: "vlog_demo.mp4 · 1280×720 · 20초",
  },
  {
    key: "shorts1",
    label: "⚡ Shorts #1",
    src: `${BASE}/demo/shorts_01.mp4`,
    ratio: "9-16",
    caption: "highlight_peak · 0.75s→5.75s · 1080×1920 자동 크롭",
  },
  {
    key: "shorts2",
    label: "⚡ Shorts #2",
    src: `${BASE}/demo/shorts_02.mp4`,
    ratio: "9-16",
    caption: "highlight_peak · 9.95s→12.97s · 1080×1920 자동 크롭",
  },
];

export default function Home() {
  const [job, setJob] = useState<JobSummary | null>(null);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [report, setReport] = useState<unknown | null>(null);
  const [connected, setConnected] = useState(false);
  const playerRef = useRef<VideoPlayerHandle>(null);

  // Live mode: connect WebSocket
  useEffect(() => {
    if (IS_DEMO || !job) return;
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

  // Demo mode: replay captured events
  const handleDemoRun = async () => {
    const captured = await loadDemoJob();
    setJob(summary(captured));
    setEvents([]);
    setReport(null);
    setConnected(true);
    replayEvents(
      captured.events,
      (ev) => setEvents((prev) => [...prev, ev]),
      () => {
        setConnected(false);
        loadDemoReport("report_01.json")
          .then((r) => setReport(r))
          .catch(() => undefined);
      },
      6,
    );
  };

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
    if (IS_DEMO || !job) return;
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
          <p className="text-sm text-neutral-400">
            브이로그 · 숏폼 자동 컷편집 대시보드
            {IS_DEMO && (
              <span className="ml-2 rounded bg-amber-500/20 px-2 py-0.5 text-xs text-amber-300">
                DEMO MODE — 캡처된 실제 실행 재생
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span
            className={`inline-flex h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-neutral-600"}`}
          />
          <span className="text-neutral-400">
            {connected ? (IS_DEMO ? "재생 중" : "WebSocket 연결됨") : "대기"}
          </span>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[420px,1fr]">
        <aside className="space-y-4">
          {IS_DEMO ? (
            <div className="space-y-4 rounded-xl border border-amber-700/40 bg-amber-950/20 p-5">
              <h2 className="text-lg font-semibold text-amber-200">🎮 데모 투어</h2>
              <p className="text-sm text-neutral-300">
                이 페이지는 정적 배포본입니다. 실제 백엔드 대신{" "}
                <code className="rounded bg-black/40 px-1.5 py-0.5 text-xs">2026-05-27</code>에 로컬에서
                돌렸던 실제 파이프라인 실행 결과를 그대로 재생합니다.
              </p>
              <div className="rounded-lg bg-black/40 p-3 font-mono text-xs text-neutral-400">
                <div>입력: vlog_demo.mp4 (20s, 1280×720)</div>
                <div>모드: shorts · 5초 × 2개</div>
                <div>이벤트 15개 · 결과 4 파일</div>
              </div>
              <button
                onClick={handleDemoRun}
                className="w-full rounded-lg bg-amber-500 px-4 py-2.5 text-sm font-semibold text-black hover:bg-amber-400"
              >
                ▶ 데모 재생
              </button>
              <p className="text-xs text-neutral-500">
                실제 사용은{" "}
                <a
                  href="https://github.com/aijunny0604-alt/video-auto-editor"
                  className="text-amber-300 underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub 레포
                </a>{" "}
                README 참고. 로컬에서 백엔드+프론트 실행 시 작업 폼이 활성화됩니다.
              </p>
            </div>
          ) : (
            <JobForm onCreated={setJob} />
          )}
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

          {IS_DEMO && (
            <VideoPlayer ref={playerRef} tabs={DEMO_VIDEO_TABS} />
          )}

          <div className="grid gap-4 xl:grid-cols-2">
            <LogStream events={events} />
            <TimelinePreview
              report={report as any}
              onSegmentClick={
                IS_DEMO
                  ? (t) => playerRef.current?.jumpToOriginal(t)
                  : undefined
              }
            />
          </div>
        </section>
      </div>

      {IS_DEMO && <HowToUse />}

      <footer className="pt-6 text-center text-xs text-neutral-600">
        FastAPI :8000 · Next.js :3000 · 같은 머신 로컬 실행 권장
      </footer>
    </main>
  );
}
