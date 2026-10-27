import csv, os, time

def log_latency(question, retrieval_s, llm_s, total_s):
    os.makedirs("data", exist_ok=True)
    path = "data/latency.csv"
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "question", "retrieval_s", "llm_s", "total_s"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), question,
                    round(retrieval_s, 3), round(llm_s, 3), round(total_s, 3)])