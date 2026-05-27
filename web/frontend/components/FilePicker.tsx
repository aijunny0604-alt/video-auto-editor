"use client";

import { useEffect, useRef, useState } from "react";
import { listFolder, uploadFiles } from "@/lib/api";
import { type HistoryEntry, loadHistory, pushHistory, removeHistory } from "@/lib/history";

type Props = {
  onResolved: (info: { input_dir: string; label: string; file_count: number }) => void;
  disabled?: boolean;
};

const MEDIA_EXTS = ["mp4", "mov", "mkv", "avi", "webm", "wav", "mp3", "m4a"];
const ACCEPT = MEDIA_EXTS.map((e) => `.${e}`).join(",");

function isMedia(name: string): boolean {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  return MEDIA_EXTS.includes(ext);
}

export default function FilePicker({ onResolved, disabled }: Props) {
  const [tab, setTab] = useState<"upload" | "local">("upload");
  const [dragOver, setDragOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [localPath, setLocalPath] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const handleUpload = async (raw: File[] | FileList) => {
    setError(null);
    setStatus(null);
    const files = Array.from(raw).filter((f) => isMedia(f.name));
    if (files.length === 0) {
      setError("지원하는 영상/오디오 파일이 없어요 (mp4, mov, mp3 …)");
      return;
    }
    setBusy(true);
    setStatus(`업로드 중 (${files.length}개)…`);
    try {
      const result = await uploadFiles(files);
      const label = `업로드 ${result.files.length}개 (${result.upload_id})`;
      const next = pushHistory({
        path: result.input_dir,
        label,
        kind: "upload",
        file_count: result.files.length,
      });
      setHistory(next);
      setStatus(`✓ ${result.files.length}개 파일 업로드 완료`);
      onResolved({ input_dir: result.input_dir, label, file_count: result.files.length });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleLocalProbe = async () => {
    setError(null);
    setStatus(null);
    if (!localPath.trim()) {
      setError("폴더 경로를 입력하세요");
      return;
    }
    setBusy(true);
    try {
      const result = await listFolder(localPath.trim());
      const label = localPath.split(/[\\/]/).filter(Boolean).pop() || localPath;
      const next = pushHistory({
        path: result.path,
        label,
        kind: "local",
        file_count: result.files.length,
      });
      setHistory(next);
      setStatus(`✓ ${result.files.length}개 미디어 파일 발견`);
      onResolved({ input_dir: result.path, label, file_count: result.files.length });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handlePickHistory = (entry: HistoryEntry) => {
    onResolved({
      input_dir: entry.path,
      label: entry.label,
      file_count: entry.file_count ?? 0,
    });
    setStatus(`✓ ${entry.label} 재사용`);
  };

  const handleRemoveHistory = (path: string) => {
    setHistory(removeHistory(path));
  };

  return (
    <div className="space-y-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
      <div>
        <h3 className="text-sm font-semibold">입력 영상</h3>
        <p className="text-xs text-neutral-500">파일을 끌어다 놓거나 폴더 경로를 직접 지정하세요</p>
      </div>

      <div className="flex gap-1.5 text-xs">
        <button
          type="button"
          onClick={() => setTab("upload")}
          className={`flex-1 rounded-md px-2.5 py-1.5 font-medium transition ${
            tab === "upload" ? "bg-emerald-500 text-black" : "bg-neutral-800 text-neutral-300"
          }`}
        >
          📂 업로드
        </button>
        <button
          type="button"
          onClick={() => setTab("local")}
          className={`flex-1 rounded-md px-2.5 py-1.5 font-medium transition ${
            tab === "local" ? "bg-emerald-500 text-black" : "bg-neutral-800 text-neutral-300"
          }`}
        >
          💻 로컬 경로
        </button>
      </div>

      {tab === "upload" ? (
        <>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer.files.length > 0) handleUpload(e.dataTransfer.files);
            }}
            className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-6 text-sm transition ${
              dragOver
                ? "border-emerald-400 bg-emerald-500/10 text-emerald-300"
                : "border-neutral-700 text-neutral-400 hover:border-neutral-500"
            }`}
          >
            <div className="text-2xl">📥</div>
            <p>여기로 파일을 끌어다 놓으세요</p>
            <p className="text-xs text-neutral-500">mp4 · mov · mp3 · wav · …</p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => e.target.files && handleUpload(e.target.files)}
          />
          <input
            ref={folderInputRef}
            type="file"
            // @ts-expect-error — webkitdirectory is non-standard but supported by Chromium/Firefox
            webkitdirectory=""
            directory=""
            multiple
            className="hidden"
            onChange={(e) => e.target.files && handleUpload(e.target.files)}
          />

          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy || disabled}
              onClick={() => fileInputRef.current?.click()}
              className="flex-1 rounded-md bg-neutral-800 px-3 py-2 text-xs hover:bg-neutral-700 disabled:opacity-50"
            >
              📄 파일 선택
            </button>
            <button
              type="button"
              disabled={busy || disabled}
              onClick={() => folderInputRef.current?.click()}
              className="flex-1 rounded-md bg-neutral-800 px-3 py-2 text-xs hover:bg-neutral-700 disabled:opacity-50"
            >
              📁 폴더 선택
            </button>
          </div>
        </>
      ) : (
        <div className="space-y-2">
          <input
            type="text"
            placeholder="C:\Users\..\Videos\원본"
            value={localPath}
            onChange={(e) => setLocalPath(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 font-mono text-xs focus:border-emerald-500 focus:outline-none"
          />
          <button
            type="button"
            disabled={busy || disabled}
            onClick={handleLocalProbe}
            className="w-full rounded-md bg-neutral-800 px-3 py-2 text-xs font-medium hover:bg-neutral-700 disabled:opacity-50"
          >
            🔍 확인 & 사용
          </button>
          <p className="text-xs text-neutral-500">
            서버가 접근할 수 있는 로컬 경로여야 합니다 (서버와 같은 PC).
          </p>
        </div>
      )}

      {status && (
        <div className="rounded-md bg-emerald-950/40 px-3 py-1.5 text-xs text-emerald-300">
          {status}
        </div>
      )}
      {error && (
        <div className="rounded-md bg-rose-950/40 px-3 py-1.5 text-xs text-rose-300">
          ⚠ {error}
        </div>
      )}

      {history.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs uppercase tracking-wide text-neutral-500">최근</p>
          <ul className="space-y-1">
            {history.map((entry) => (
              <li
                key={entry.path}
                className="group flex items-center gap-2 rounded-md bg-neutral-950/60 px-2.5 py-1.5 text-xs"
              >
                <button
                  type="button"
                  onClick={() => handlePickHistory(entry)}
                  className="flex-1 truncate text-left hover:text-emerald-300"
                  title={entry.path}
                >
                  <span className="mr-1.5">{entry.kind === "upload" ? "📂" : "💻"}</span>
                  {entry.label}
                  {typeof entry.file_count === "number" && (
                    <span className="ml-1.5 text-neutral-500">· {entry.file_count}개</span>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => handleRemoveHistory(entry.path)}
                  className="text-neutral-600 opacity-0 hover:text-rose-400 group-hover:opacity-100"
                  title="이력에서 제거"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
