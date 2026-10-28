"""Step 2 of evaluation: score outputs.json with RAGAS and append a row to data/eval_results.csv.

Needs: pip install ragas langchain-openai langchain-huggingface pandas
RAGAS changes its API often. This targets ragas 0.2/0.3. If imports fail, check the current docs:
https://docs.ragas.io
"""
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from ragas import EvaluationDataset, evaluate  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import (Faithfulness, LLMContextPrecisionWithReference,  # noqa: E402
                           LLMContextRecall, ResponseRelevancy)

from app import config  # noqa: E402

FIELDS = ["time", "label", "chunk_size", "overlap", "k", "model", "n", "retrieval_hit_rate",
          "context_precision", "context_recall", "answer_relevancy", "faithfulness", "avg_latency_s"]


def pick(df, key):
    cols = [c for c in df.columns if key in c]
    return round(float(df[cols[0]].mean()), 3) if cols else ""


def main():
    data = json.load(open(Path(__file__).parent / "outputs.json", encoding="utf-8"))
    ds = EvaluationDataset.from_list([
        {"user_input": r["question"], "retrieved_contexts": r["contexts"],
         "response": r["answer"], "reference": r["ground_truth"]}
        for r in data["rows"]
    ])
    llm = LangchainLLMWrapper(ChatOpenAI(model=config.LLM_MODEL, api_key=config.LLM_API_KEY,
                                         base_url=config.LLM_BASE_URL, temperature=0))
    emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=config.EMBED_MODEL))

    # strictness=1: some providers (e.g. Groq) reject n>1 completions
    result = evaluate(ds, metrics=[LLMContextPrecisionWithReference(), LLMContextRecall(),
                                   ResponseRelevancy(strictness=1), Faithfulness()],
                      llm=llm, embeddings=emb)
    df = result.to_pandas()
    print(df.mean(numeric_only=True))

    s, summ = data["settings"], data["summary"]
    row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "label": s["label"], "chunk_size": s["chunk_size"],
           "overlap": s["overlap"], "k": s["k"], "model": s["model"], "n": summ["n"],
           "retrieval_hit_rate": summ["retrieval_hit_rate"],
           "context_precision": pick(df, "precision"), "context_recall": pick(df, "recall"),
           "answer_relevancy": pick(df, "relevancy"), "faithfulness": pick(df, "faithfulness"),
           "avg_latency_s": summ["avg_latency_s"]}
    new = not config.EVAL_CSV.exists()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.EVAL_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print("Appended to", config.EVAL_CSV)


if __name__ == "__main__":
    main()
