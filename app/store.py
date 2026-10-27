import json, os
import faiss, numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = "data/index"
model = SentenceTransformer("all-MiniLM-L6-v2")
index = None
chunks = []

def load():
    global index, chunks
    if os.path.exists(f"{INDEX_DIR}/faiss.index"):
        index = faiss.read_index(f"{INDEX_DIR}/faiss.index")
        chunks = json.load(open(f"{INDEX_DIR}/chunks.json", encoding="utf-8"))

def save():
    os.makedirs(INDEX_DIR, exist_ok=True)
    faiss.write_index(index, f"{INDEX_DIR}/faiss.index")
    json.dump(chunks, open(f"{INDEX_DIR}/chunks.json", "w", encoding="utf-8"))

def add_chunks(new_chunks):
    global index
    vecs = model.encode([c["text"] for c in new_chunks], normalize_embeddings=True)
    vecs = np.array(vecs, dtype="float32")
    if index is None:
        index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    chunks.extend(new_chunks)
    save()

def search(question, k=5):
    if index is None:
        return []
    q = np.array(model.encode([question], normalize_embeddings=True), dtype="float32")
    scores, ids = index.search(q, k)
    return [{**chunks[i], "score": float(s)} for s, i in zip(scores[0], ids[0]) if i != -1]