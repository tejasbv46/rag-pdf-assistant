import type { AskResponse, DocInfo, EvalRow, LatencyStats, UploadResult } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export const api = {
  documents: () => request<DocInfo[]>("/documents"),

  upload: (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return request<{ results: UploadResult[] }>("/upload", { method: "POST", body: form });
  },

  remove: (name: string) =>
    request<{ deleted: string }>(`/documents/${encodeURIComponent(name)}`, { method: "DELETE" }),

  ask: (question: string, k: number, docs: string[]) =>
    request<AskResponse>("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, k, docs: docs.length ? docs : null }),
    }),

  latency: () => request<LatencyStats>("/metrics/latency"),
  evalResults: () => request<EvalRow[]>("/eval/results"),
};
