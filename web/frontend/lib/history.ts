/** localStorage-backed recent folder/upload history. */

const KEY = "vae:recent-folders";
const MAX = 5;

export type HistoryEntry = {
  path: string;
  label: string;
  kind: "local" | "upload";
  ts: number;
  file_count?: number;
};

export function loadHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function pushHistory(entry: Omit<HistoryEntry, "ts">): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  const existing = loadHistory().filter((e) => e.path !== entry.path);
  const next = [{ ...entry, ts: Date.now() }, ...existing].slice(0, MAX);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function removeHistory(path: string): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  const next = loadHistory().filter((e) => e.path !== path);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
