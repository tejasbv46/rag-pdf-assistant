import { useRef, useState } from "react";
import { api } from "../api";
import type { DocInfo } from "../types";

interface Props {
  docs: DocInfo[];
  selected: string[];
  onSelect: (names: string[]) => void;
  onChanged: () => void;
}

export default function Library({ docs, selected, onSelect, onChanged }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [drag, setDrag] = useState(false);

  async function upload(files: File[]) {
    const pdfs = files.filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (!pdfs.length) {
      setNotice("Only PDF files can be added.");
      return;
    }
    setBusy(true);
    setNotice("");
    try {
      const { results } = await api.upload(pdfs);
      const failed = results.filter((r) => !r.ok);
      setNotice(failed.length ? failed.map((r) => `${r.file}: ${r.error}`).join("\n") : "");
      onChanged();
    } catch (e) {
      setNotice((e as Error).message);
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  async function remove(name: string) {
    if (!window.confirm(`Remove ${name} from the library?`)) return;
    try {
      await api.remove(name);
      onChanged();
    } catch (e) {
      setNotice((e as Error).message);
    }
  }

  function toggle(name: string) {
    onSelect(selected.includes(name) ? selected.filter((n) => n !== name) : [...selected, name]);
  }

  return (
    <aside className="library">
      <h2>Library</h2>

      <div
        className={`drop ${drag ? "over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          upload(Array.from(e.dataTransfer.files));
        }}
      >
        <input
          ref={input}
          type="file"
          accept="application/pdf"
          multiple
          hidden
          onChange={(e) => upload(Array.from(e.target.files ?? []))}
        />
        <button className="primary" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Reading PDFs…" : "Add PDFs"}
        </button>
        <p>or drop files here</p>
      </div>

      {notice && <p className="notice">{notice}</p>}

      {docs.length === 0 ? (
        <p className="muted">No documents yet. Add a PDF to start asking questions.</p>
      ) : (
        <>
          <p className="muted small">
            {selected.length === 0
              ? "Searching all documents"
              : `Searching ${selected.length} of ${docs.length}`}
            {selected.length > 0 && (
              <button className="link" onClick={() => onSelect([])}>
                Search all
              </button>
            )}
          </p>
          <ul className="doclist">
            {docs.map((d) => (
              <li key={d.name}>
                <label>
                  <input
                    type="checkbox"
                    checked={selected.includes(d.name)}
                    onChange={() => toggle(d.name)}
                  />
                  <span className="docname" title={d.name}>
                    {d.name}
                  </span>
                </label>
                <span className="small muted">
                  {d.pages} pages
                </span>
                <button className="icon" aria-label={`Remove ${d.name}`} onClick={() => remove(d.name)}>
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </aside>
  );
}
