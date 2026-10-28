import sqlite3
import time

import numpy as np

from app import config


def _conn():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(config.LATENCY_DB)
    c.execute(
        """CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, question TEXT,
            retrieval_s REAL, llm_s REAL, total_s REAL, found INTEGER)"""
    )
    return c


def log_query(question, retrieval_s, llm_s, total_s, found):
    with _conn() as c:
        c.execute(
            "INSERT INTO queries (time, question, retrieval_s, llm_s, total_s, found) VALUES (?,?,?,?,?,?)",
            (time.strftime("%Y-%m-%d %H:%M:%S"), question, retrieval_s, llm_s, total_s, int(found)),
        )


def latency_stats(recent=20):
    with _conn() as c:
        rows = c.execute("SELECT time, question, retrieval_s, llm_s, total_s FROM queries ORDER BY id DESC").fetchall()
    if not rows:
        return {"count": 0, "avg_total_s": 0, "p50_total_s": 0, "p95_total_s": 0,
                "avg_retrieval_s": 0, "avg_llm_s": 0, "recent": []}
    total = np.array([r[4] for r in rows])
    return {
        "count": len(rows),
        "avg_total_s": round(float(total.mean()), 3),
        "p50_total_s": round(float(np.percentile(total, 50)), 3),
        "p95_total_s": round(float(np.percentile(total, 95)), 3),
        "avg_retrieval_s": round(float(np.mean([r[2] for r in rows])), 3),
        "avg_llm_s": round(float(np.mean([r[3] for r in rows])), 3),
        "recent": [{"time": r[0], "question": r[1], "total_s": round(r[4], 3)} for r in rows[:recent]],
    }
