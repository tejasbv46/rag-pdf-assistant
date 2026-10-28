import { useEffect, useState } from "react";
import { api } from "../api";
import type { EvalRow, LatencyStats } from "../types";

const COLUMNS: [string, string][] = [
  ["label", "Run"],
  ["chunk_size", "Chunk size"],
  ["k", "k"],
  ["model", "Model"],
  ["retrieval_hit_rate", "Right page retrieved"],
  ["context_precision", "Context precision"],
  ["context_recall", "Context recall"],
  ["answer_relevancy", "Answer relevancy"],
  ["faithfulness", "Faithfulness"],
  ["avg_latency_s", "Avg latency (s)"],
];

export default function Stats() {
  const [lat, setLat] = useState<LatencyStats | null>(null);
  const [rows, setRows] = useState<EvalRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.latency(), api.evalResults()])
      .then(([l, r]) => {
        setLat(l);
        setRows(r);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error pad">{error}</p>;
  if (!lat) return <p className="muted pad">Loading…</p>;

  return (
    <section className="stats">
      <h2>Response time</h2>
      {lat.count === 0 ? (
        <p className="muted">No questions asked yet.</p>
      ) : (
        <>
          <dl className="numbers">
            <div><dt>Questions</dt><dd>{lat.count}</dd></div>
            <div><dt>Median</dt><dd>{lat.p50_total_s}s</dd></div>
            <div><dt>Average</dt><dd>{lat.avg_total_s}s</dd></div>
            <div><dt>Slowest 5%</dt><dd>{lat.p95_total_s}s</dd></div>
            <div><dt>Avg retrieval</dt><dd>{lat.avg_retrieval_s}s</dd></div>
            <div><dt>Avg model</dt><dd>{lat.avg_llm_s}s</dd></div>
          </dl>
          <div className="scroll">
            <table>
              <thead>
                <tr><th>Time</th><th>Question</th><th>Total (s)</th></tr>
              </thead>
              <tbody>
                {lat.recent.map((r, i) => (
                  <tr key={i}>
                    <td>{r.time}</td>
                    <td>{r.question}</td>
                    <td>{r.total_s}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <h2>Evaluation runs</h2>
      {rows.length === 0 ? (
        <p className="muted">
          No runs yet. In the backend folder, run <code>python eval/run_eval.py</code> then{" "}
          <code>python eval/score_ragas.py</code>.
        </p>
      ) : (
        <div className="scroll">
          <table>
            <thead>
              <tr>{COLUMNS.map(([, label]) => <th key={label}>{label}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>{COLUMNS.map(([key]) => <td key={key}>{r[key]}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
