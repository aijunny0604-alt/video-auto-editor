"use client";

import { useState } from "react";
import FilePicker from "@/components/FilePicker";
import type { CreateJobRequest, JobSummary } from "@/lib/api";
import { createJob } from "@/lib/api";

type Props = {
  onCreated: (job: JobSummary) => void;
};

type Source = {
  input_dir: string;
  label: string;
  file_count: number;
} | null;

export default function JobForm({ onCreated }: Props) {
  const [source, setSource] = useState<Source>(null);
  const [mode, setMode] = useState<"vlog" | "shorts">("vlog");
  const [outputDir, setOutputDir] = useState("C:\\tmp\\video-auto-editor\\out");
  const [shortsCount, setShortsCount] = useState(3);
  const [shortsLength, setShortsLength] = useState(30);
  const [useStt, setUseStt] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!source) {
      setError("입력 영상을 먼저 선택하세요");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const req: CreateJobRequest = {
        mode,
        input_dir: source.input_dir,
        output_dir: outputDir,
        shorts_count: shortsCount,
        shorts_length: shortsLength,
        use_stt: useStt,
      };
      const job = await createJob(req);
      onCreated(job);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FilePicker onResolved={setSource} disabled={submitting} />

      <div className="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
        <div>
          <label className="mb-1 block text-sm text-neutral-400">모드</label>
          <div className="flex gap-2">
            {(["vlog", "shorts"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  mode === m
                    ? "bg-emerald-500 text-black"
                    : "bg-neutral-800 text-neutral-200 hover:bg-neutral-700"
                }`}
              >
                {m === "vlog" ? "🎒 브이로그 (16:9)" : "⚡ 숏폼 (9:16)"}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm text-neutral-400">출력 폴더</label>
          <input
            type="text"
            value={outputDir}
            onChange={(e) => setOutputDir(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 font-mono text-xs focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {mode === "shorts" && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm text-neutral-400">개수</label>
              <input
                type="number"
                min={1}
                max={10}
                value={shortsCount}
                onChange={(e) => setShortsCount(Number(e.target.value))}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-neutral-400">길이 (초)</label>
              <input
                type="number"
                min={5}
                max={180}
                value={shortsLength}
                onChange={(e) => setShortsLength(Number(e.target.value))}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm"
              />
            </div>
          </div>
        )}

        <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-300">
          <input
            type="checkbox"
            checked={useStt}
            onChange={(e) => setUseStt(e.target.checked)}
            className="h-4 w-4 accent-emerald-500"
          />
          Whisper STT 자막 생성 (느림, GPU 권장)
        </label>

        {source && (
          <div className="rounded-md bg-neutral-950/60 px-3 py-2 text-xs">
            <p className="text-neutral-400">선택된 소스</p>
            <p className="mt-0.5 truncate font-mono text-emerald-300" title={source.input_dir}>
              {source.label} · {source.file_count}개
            </p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-rose-700 bg-rose-950/50 px-3 py-2 text-sm text-rose-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !source}
          className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "시작 중…" : "▶ 실행"}
        </button>
      </div>
    </form>
  );
}
