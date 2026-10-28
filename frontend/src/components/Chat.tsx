import { Fragment, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Citation, DocInfo, Message } from "../types";

interface Props {
  docs: DocInfo[];
  selected: string[];
}

let nextId = 1;

export default function Chat({ docs, selected }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [k, setK] = useState(5);
  const [loading, setLoading] = useState(false);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function send() {
    const q = question.trim();
    if (!q || loading) return;
    const id = nextId++;
    setQuestion("");
    setLoading(true);
    setMessages((m) => [...m, { id, question: q }]);
    try {
      const response = await api.ask(q, k, selected);
      setMessages((m) => m.map((x) => (x.id === id ? { ...x, response } : x)));
    } catch (e) {
      setMessages((m) => m.map((x) => (x.id === id ? { ...x, error: (e as Error).message } : x)));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chat">
      <div className="thread">
        {messages.length === 0 && (
          <div className="empty">
            <p className="empty-title">
              {docs.length ? "Ask a question about your documents." : "Add a PDF to get started."}
            </p>
            <p className="muted">
              Every answer links back to the document and page it came from.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <Exchange key={m.id} message={m} pending={loading && !m.response && !m.error} />
        ))}
        <div ref={end} />
      </div>

      <div className="composer">
        <textarea
          value={question}
          placeholder={docs.length ? "Type your question" : "Add a PDF first"}
          disabled={docs.length === 0}
          rows={2}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <div className="composer-row">
          <label className="small muted">
            Passages to retrieve{" "}
            <select value={k} onChange={(e) => setK(Number(e.target.value))}>
              {[3, 5, 8, 12].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <button className="primary" disabled={loading || !question.trim() || !docs.length} onClick={send}>
            {loading ? "Searching…" : "Ask"}
          </button>
        </div>
      </div>
    </section>
  );
}

function Exchange({ message, pending }: { message: Message; pending: boolean }) {
  const [open, setOpen] = useState<number | null>(null);
  const r = message.response;

  return (
    <article className="exchange">
      <p className="question">{message.question}</p>

      {pending && <p className="muted">Reading the documents…</p>}
      {message.error && <p className="error">{message.error}</p>}

      {r && (
        <>
          <p className={`answer ${r.found ? "" : "notfound"}`}>
            <AnswerText text={r.answer} citations={r.citations} onCite={(id) => setOpen(open === id ? null : id)} />
          </p>

          <p className="timing small muted">
            Retrieval {r.latency.retrieval_s}s · Model {r.latency.llm_s}s · Total {r.latency.total_s}s
          </p>

          {r.found && r.citations.length > 0 && (
            <div className="sources">
              <h3>Sources</h3>
              <ul>
                {[...r.citations]
                  .sort((a, b) => Number(b.used) - Number(a.used))
                  .map((c) => (
                    <Source key={c.id} c={c} open={open === c.id} onToggle={() => setOpen(open === c.id ? null : c.id)} />
                  ))}
              </ul>
            </div>
          )}
        </>
      )}
    </article>
  );
}

/** Turns [1] markers inside the answer into clickable citation chips. */
function AnswerText({
  text,
  citations,
  onCite,
}: {
  text: string;
  citations: Citation[];
  onCite: (id: number) => void;
}) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        const c = match && citations.find((x) => x.id === Number(match[1]));
        if (!c) return <Fragment key={i}>{part}</Fragment>;
        return (
          <button key={i} className="chip" onClick={() => onCite(c.id)} title={`${c.doc}, page ${c.page}`}>
            {c.doc.replace(/\.pdf$/i, "")} p.{c.page}
          </button>
        );
      })}
    </>
  );
}

function Source({ c, open, onToggle }: { c: Citation; open: boolean; onToggle: () => void }) {
  return (
    <li className={`source ${c.used ? "used" : "unused"} ${open ? "open" : ""}`}>
      <button className="source-head" aria-expanded={open} onClick={onToggle}>
        <span className="page">p.{c.page}</span>
        <span className="doc">{c.doc}</span>
        <span className="small muted">
          {c.used ? "cited" : "retrieved"} · match {c.score.toFixed(2)}
        </span>
      </button>
      {open && <blockquote>{c.snippet}</blockquote>}
    </li>
  );
}
