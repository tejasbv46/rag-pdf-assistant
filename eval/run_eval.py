"""Step 1 of evaluation: run every test question through the pipeline and save outputs.

Usage (from backend/):
  python eval/run_eval.py --k 5
  python eval/run_eval.py --k 5 --chunk-size 300 --label small-chunks   # re-indexes PDFs in a temp index
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, ingest, rag  # noqa: E402
from app.store import VectorStore, default_store  # noqa: E402


def build_store(chunk_size, overlap):
    store = VectorStore(config.DATA_DIR / "index_eval" / f"cs{chunk_size}_ov{overlap}")
    for pdf in sorted(config.PDF_DIR.glob("*.pdf")):
        pages = ingest.extract_pages(pdf)
        store.add_document(pdf.name, len(pages), ingest.chunk_pages(pages, pdf.name, chunk_size, overlap))
    return store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=config.TOP_K)
    ap.add_argument("--chunk-size", type=int, default=None)
    ap.add_argument("--overlap", type=int, default=config.CHUNK_OVERLAP)
    ap.add_argument("--label", default="baseline")
    ap.add_argument("--test-set", default=str(Path(__file__).parent / "test_set.json"))
    args = ap.parse_args()

    chunk_size = args.chunk_size or config.CHUNK_SIZE
    store = build_store(chunk_size, args.overlap) if args.chunk_size else default_store

    items = json.load(open(args.test_set, encoding="utf-8"))
    rows, hits_total, hits_ok, lat = [], 0, 0, []
    for n, item in enumerate(items, 1):
        r = rag.answer(item["question"], args.k, store=store, log=False)
        hit = None
        if "page" in item:  # retrieval hit-rate: did we retrieve the right page?
            hit = any(c["page"] == item["page"] and (not item.get("doc") or c["doc"] == item["doc"])
                      for c in r["citations"])
            hits_total += 1
            hits_ok += int(hit)
        lat.append(r["latency"]["total_s"])
        rows.append({"question": item["question"], "answer": r["answer"], "contexts": r["contexts"],
                     "ground_truth": item["ground_truth"], "retrieval_hit": hit,
                     "latency_s": r["latency"]["total_s"]})
        print(f"[{n}/{len(items)}] {item['question'][:60]}  hit={hit}  {r['latency']['total_s']}s")

    out = {
        "settings": {"label": args.label, "chunk_size": chunk_size, "overlap": args.overlap,
                     "k": args.k, "model": config.LLM_MODEL, "embed_model": config.EMBED_MODEL},
        "summary": {"n": len(rows),
                    "retrieval_hit_rate": round(hits_ok / hits_total, 3) if hits_total else "",
                    "avg_latency_s": round(sum(lat) / len(lat), 3) if lat else ""},
        "rows": rows,
    }
    path = Path(__file__).parent / "outputs.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nSaved", path, out["summary"])
    print("Next: python eval/score_ragas.py")


if __name__ == "__main__":
    main()
