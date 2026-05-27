"use client";

import type { PipelineEvent } from "@/lib/api";

type Props = { events: PipelineEvent[] };

function sumStage(events: PipelineEvent[], stage: string, key: string): number {
  return events
    .filter((e) => e.kind === "stage_done" && e.data.stage === stage)
    .reduce((acc, e) => acc + ((e.data[key] as number) ?? 0), 0);
}

function timelineDurations(events: PipelineEvent[]): number[] {
  return events
    .filter((e) => e.kind === "timeline_built")
    .map((e) => (e.data.duration as number) ?? 0);
}

export default function Metrics({ events }: Props) {
  const silenceRanges = sumStage(events, "silence", "count");
  const sttWords = sumStage(events, "stt", "words");
  const loudnessSamples = sumStage(events, "loudness", "samples");
  const scenes = sumStage(events, "scenes", "count");
  const durations = timelineDurations(events);
  const totalOut = durations.reduce((a, b) => a + b, 0);

  const card = (label: string, value: string, hint?: string) => (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <p className="text-xs text-neutral-400">{label}</p>
      <p className="mt-1 text-xl font-semibold text-neutral-100">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-neutral-500">{hint}</p>}
    </div>
  );

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {card("무음 구간", `${silenceRanges}`, "감지된 silencedetect 범위")}
      {card("STT 단어", `${sttWords}`, "Whisper 추출 단어 수")}
      {card("씬 전환", `${scenes}`, "PySceneDetect 컷")}
      {card("음량 샘플", `${loudnessSamples}`, "astats 윈도우")}
      {card("타임라인 수", `${durations.length}`, "vlog=1 / shorts=N")}
      {card("총 출력 시간", `${totalOut.toFixed(1)}s`, "결합된 timeline 길이")}
    </div>
  );
}
