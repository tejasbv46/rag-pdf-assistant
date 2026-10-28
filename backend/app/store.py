import json
import threading
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app import config

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


def embed(texts):
    v = get_model().encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    return np.asarray(v, dtype="float32")


class VectorStore:
    """FAISS index + chunk metadata. Vectors are saved too, so deleting a doc just rebuilds the index."""

    def __init__(self, index_dir=config.INDEX_DIR):
        self.dir = Path(index_dir)
        self.lock = threading.RLock()
        self.chunks, self.meta = [], {}
        self.vectors = np.zeros((0, 0), dtype="float32")
        self.index = None
        self._load()

    # ---------- persistence ----------
    def _load(self):
        cj, vn, mj = self.dir / "chunks.json", self.dir / "vectors.npy", self.dir / "meta.json"
        if cj.exists() and vn.exists():
            self.chunks = json.loads(cj.read_text(encoding="utf-8"))
            self.vectors = np.load(vn)
            if mj.exists():
                self.meta = json.loads(mj.read_text(encoding="utf-8"))
        self._rebuild()

    def _rebuild(self):
        if not self.chunks:
            self.index = None
            return
        self.index = faiss.IndexFlatIP(self.vectors.shape[1])  # inner product == cosine (normalized)
        self.index.add(self.vectors)

    def _save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "chunks.json").write_text(json.dumps(self.chunks), encoding="utf-8")
        (self.dir / "meta.json").write_text(json.dumps(self.meta), encoding="utf-8")
        np.save(self.dir / "vectors.npy", self.vectors)

    # ---------- operations ----------
    def _drop(self, doc):
        keep = [i for i, c in enumerate(self.chunks) if c["doc"] != doc]
        self.chunks = [self.chunks[i] for i in keep]
        self.vectors = self.vectors[keep] if keep else np.zeros((0, 0), dtype="float32")
        self.meta.pop(doc, None)

    def add_document(self, doc, pages, chunks):
        vecs = embed([c["text"] for c in chunks])
        with self.lock:
            self._drop(doc)  # re-uploading the same file replaces it
            self.vectors = vecs if self.vectors.size == 0 else np.vstack([self.vectors, vecs])
            self.chunks.extend(chunks)
            self.meta[doc] = {"pages": pages}
            self._rebuild()
            self._save()

    def remove_document(self, doc):
        with self.lock:
            if doc not in self.meta:
                return False
            self._drop(doc)
            self._rebuild()
            self._save()
            return True

    def documents(self):
        with self.lock:
            counts = {}
            for c in self.chunks:
                counts[c["doc"]] = counts.get(c["doc"], 0) + 1
            return [{"name": d, "pages": m["pages"], "chunks": counts.get(d, 0)} for d, m in self.meta.items()]

    def search(self, question, k=5, docs=None):
        with self.lock:
            if self.index is None:
                return []
            q = embed([question])
            n = self.index.ntotal if docs else min(k, self.index.ntotal)
            scores, ids = self.index.search(q, n)
            hits = []
            for s, i in zip(scores[0], ids[0]):
                if i == -1:
                    continue
                c = self.chunks[i]
                if docs and c["doc"] not in docs:
                    continue
                hits.append({**c, "score": float(s)})
                if len(hits) == k:
                    break
            return hits


default_store = VectorStore()
