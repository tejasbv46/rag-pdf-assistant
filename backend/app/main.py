import csv
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import config, ingest, metrics, rag
from app.store import default_store as store

app = FastAPI(title="PDF RAG with citations")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=config.TOP_K, ge=1, le=20)
    docs: Optional[List[str]] = None  # restrict search to these document names


@app.get("/health")
def health():
    return {"ok": True, "model": config.LLM_MODEL, "documents": len(store.documents())}


@app.post("/upload")
def upload(files: List[UploadFile] = File(...)):
    config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for f in files:
        name = Path(f.filename or "").name
        if not name.lower().endswith(".pdf"):
            results.append({"file": name, "ok": False, "error": "Only PDF files are supported."})
            continue
        path = config.PDF_DIR / name
        path.write_bytes(f.file.read())
        try:
            pages = ingest.extract_pages(path)
            chunks = ingest.chunk_pages(pages, name)
            if not chunks:
                raise ValueError("No text found. Scanned PDFs need OCR first.")
            store.add_document(name, len(pages), chunks)
            results.append({"file": name, "ok": True, "pages": len(pages), "chunks": len(chunks)})
        except Exception as e:  # corrupt PDF, no text, etc.
            path.unlink(missing_ok=True)
            results.append({"file": name, "ok": False, "error": str(e)})
    return {"results": results}


@app.get("/documents")
def documents():
    return store.documents()


@app.delete("/documents/{name}")
def delete_document(name: str):
    if not store.remove_document(name):
        raise HTTPException(404, "Document not found")
    (config.PDF_DIR / Path(name).name).unlink(missing_ok=True)
    return {"deleted": name}


@app.post("/ask")
def ask(req: AskRequest):
    if not store.documents():
        raise HTTPException(400, "Upload a PDF first.")
    try:
        return rag.answer(req.question, req.k, req.docs)
    except RuntimeError as e:  # missing API key
        raise HTTPException(500, str(e))
    except Exception as e:  # LLM provider error
        raise HTTPException(502, f"LLM request failed: {e}")


@app.get("/metrics/latency")
def latency():
    return metrics.latency_stats()


@app.get("/eval/results")
def eval_results():
    if not config.EVAL_CSV.exists():
        return []
    with open(config.EVAL_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
