export type JobStatus = "pending" | "running" | "done" | "error";

export type PipelineEvent = {
  kind: string;
  ts: number;
  message: string;
  data: Record<string, unknown>;
};

export type JobSummary = {
  id: string;
  mode: string;
  status: JobStatus;
  input_dir: string;
  output_dir: string;
  error: string | null;
  event_count: number;
  artifact_count: number;
};

export type JobDetail = JobSummary & {
  events: PipelineEvent[];
  artifacts: string[];
};

export type CreateJobRequest = {
  mode: "vlog" | "shorts";
  input_dir: string;
  output_dir: string;
  shorts_count?: number;
  shorts_length?: number;
  use_stt?: boolean;
  render?: boolean;
  bgm_volume?: number;
  transition?: "fade" | "none";
};

export async function createJob(req: CreateJobRequest): Promise<JobSummary> {
  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function listFolder(path: string): Promise<{ path: string; files: { name: string; size: number }[] }> {
  const res = await fetch(`/api/folders/list?path=${encodeURIComponent(path)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type UploadResult = {
  upload_id: string;
  input_dir: string;
  files: { name: string; size: number }[];
};

export async function uploadFiles(files: File[]): Promise<UploadResult> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f, f.name));
  const res = await fetch("/api/uploads", { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJob(id: string): Promise<JobDetail> {
  const res = await fetch(`/api/jobs/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getArtifact(jobId: string, name: string): Promise<unknown> {
  const res = await fetch(`/api/jobs/${jobId}/artifact?name=${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function openJobWebSocket(
  jobId: string,
  onMessage: (event: PipelineEvent) => void,
  onClose?: () => void,
): WebSocket {
  const proto = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  // Backend runs on :8000 directly (Next.js rewrites only proxy /api, not /ws)
  const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
  const ws = new WebSocket(`${proto}//${host}:8000/ws/jobs/${jobId}`);
  ws.onmessage = (msg) => {
    try {
      onMessage(JSON.parse(msg.data));
    } catch {
      /* ignore */
    }
  };
  ws.onclose = () => onClose?.();
  return ws;
}
