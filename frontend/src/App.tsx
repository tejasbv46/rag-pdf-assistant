import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { DocInfo } from "./types";
import Library from "./components/Library";
import Chat from "./components/Chat";
import Stats from "./components/Stats";

type Tab = "ask" | "results";

export default function App() {
  const [docs, setDocs] = useState<DocInfo[]>([]);
  const [selected, setSelected] = useState<string[]>([]); // empty = search every document
  const [tab, setTab] = useState<Tab>("ask");
  const [backendError, setBackendError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const list = await api.documents();
      setDocs(list);
      setSelected((s) => s.filter((n) => list.some((d) => d.name === n)));
      setBackendError("");
    } catch {
      setBackendError("Can't reach the backend. Start it with: uvicorn app.main:app --reload");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="shell">
      <Library
        docs={docs}
        selected={selected}
        onSelect={setSelected}
        onChanged={refresh}
      />
      <main className="main">
        <header className="topbar">
          <h1>Ask your PDFs</h1>
          <nav className="tabs" role="tablist">
            <button role="tab" aria-selected={tab === "ask"} onClick={() => setTab("ask")}>
              Ask
            </button>
            <button role="tab" aria-selected={tab === "results"} onClick={() => setTab("results")}>
              Results
            </button>
          </nav>
        </header>
        {backendError && <p className="banner">{backendError}</p>}
        {tab === "ask" ? (
          <Chat docs={docs} selected={selected} />
        ) : (
          <Stats />
        )}
      </main>
    </div>
  );
}
