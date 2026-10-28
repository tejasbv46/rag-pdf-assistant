export interface Citation {
  id: number;
  doc: string;
  page: number;
  snippet: string;
  score: number;
  used: boolean;
}
export interface Latency {
  retrieval_s: number;
  llm_s: number;
  total_s: number;
}
export interface AskResponse {
  answer: string;
  found: boolean;
  citations: Citation[];
  latency: Latency;
}
export interface DocInfo {
  name: string;
  pages: number;
  chunks: number;
}
export interface UploadResult {
  file: string;
  ok: boolean;
  pages?: number;
  chunks?: number;
  error?: string;
}
export interface LatencyStats {
  count: number;
  avg_total_s: number;
  p50_total_s: number;
  p95_total_s: number;
  avg_retrieval_s: number;
  avg_llm_s: number;
  recent: { time: string; question: string; total_s: number }[];
}
export type EvalRow = Record<string, string>;

export interface Message {
  id: number;
  question: string;
  response?: AskResponse;
  error?: string;
}
