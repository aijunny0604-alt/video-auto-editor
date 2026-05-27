"use client";

import { useState } from "react";
import type { CreateJobRequest, JobSummary } from "@/lib/api";
import { createJob, listFolder } from "@/lib/api";

type Props = {
  onCreated: (job: JobSummary) => void;
};

export default function JobForm({ onCreated }: Props) {
  const [mode, setMode] = useState<"vlog" | "shorts">("vlog");
  const [inputDir, setInputDir] = useState("C:\\tmp\\video-auto-editor\\clips");
  const [outputDir, setOutputDir] = useState("C:\\tmp\\video-auto-editor\\out");
  const [shortsCount, setShortsCount] = useState(3);
  const [shortsLength, setShortsLength] = useState(30);
  const [useStt, setUseStt] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [folderInfo, setFolderInfo] = useState<string | null>(null);

  const handleProbe = async () => {
    setError(null);
    setFolderInfo(null);
    try {
      const { files } = await listFolder(inputDir);
      setFolderInfo(`✓ ${files.length} media file(s) found`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const req: CreateJobRequest = {
        mode,
        input_dir: inputDir,
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
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
      <h2 className="text-lg font-semibold">새 작업</h2>

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
        <label className="mb-1 block text-sm text-neutral-400">입력 폴더</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={inputDir}
            onChange={(e) => setInputDir(e.target.value)}
            className="flex-1 rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 font-mono text-sm focus:border-emerald-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleProbe}
            className="rounded-lg bg-neutral-800 px-3 text-sm hover:bg-neutral-700"
          >
            확인
          </button>
        </div>
        {folderInfo && <p className="mt-1 text-xs text-emerald-400">{folderInfo}</p>}
      </div>

      <div>
        <label className="mb-1 block text-sm text-neutral-400">출력 폴더</label>
        <input
          type="text"
          value={outputDir}
          onChange={(e) => setOutputDir(e.target.value)}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 font-mono text-sm focus:border-emerald-500 focus:outline-none"
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

      {error && (
        <div className="rounded-lg border border-rose-700 bg-rose-950/50 px-3 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:bg-emerald-400 disabled:opacity-50"
      >
        {submitting ? "시작 중…" : "▶ 실행"}
      </button>
    </form>
  );
}
