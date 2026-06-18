#!/usr/bin/env python3
"""
ollama_benchmark.py
Quick benchmark: measures latency and basic JSON-output quality for a list of models
Usage:
  1) pip install ollama pandas
  2) ollama serve
  3) ollama pull gemma3
     ollama pull mistral:7b-instruct
     ollama pull llama3.1:8b-instruct
  4) python ollama_benchmark.py
Outputs: results.csv (per-request rows) and summary printed.
"""

import time, json, re, csv
import ollama

# ===== CONFIG =====
MODELS = ["gemma3", "mistral:7b-instruct", "llama3.1:8b"]
RUNS_PER_MODEL = 3  # Increased to 3 runs for better average
TIMEOUT_SECONDS = 120
OUTPUT_CSV = "results.csv"

# sample feedbacks (3 samples for quick testing). Replace/add your own domain-specific lines.
SAMPLES = [
    "The onboarding was confusing and my manager didn't explain expectations.",
    "Great mentoring from senior devs — I'm learning a lot!",
    "Work-life balance is good but weekends are often required unexpectedly.",
]

# Prompts: classifier (fast small output) and full structured prompt for final output
STRUCTURED_PROMPT = """
SYSTEM: Return ONLY a single JSON object with the schema:
{{
 "sentiment":{{"label":"positive|neutral|negative","score":0.0-1.0}},
 "aspects":[{{"name": "onboarding|pay|communication|workload|manager|training","confidence":0.0-1.0}}],
 "emotion":"anger|sadness|joy|fear|neutral",
 "suggestions":[{{"action":"short","reason":"short","priority":1-3}}],
 "personalized_reply":"short 1-2 sentence reply"
}}

INPUT: "{feedback}"
"""


# ===== HELPERS =====
def extract_json(text):
    # Try direct parse then fallback to first {...} group
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def run_single(client, model, prompt, max_tokens=200, temperature=0):
    t0 = time.perf_counter()
    try:
        # Use ollama.generate() directly - new API
        resp = ollama.generate(
            model=model,
            prompt=prompt,
            options={"num_predict": max_tokens, "temperature": temperature},
        )
    except Exception as e:
        return None, None, time.perf_counter() - t0, str(e)
    t_elapsed = time.perf_counter() - t0

    # Extract text from response
    text = None
    if isinstance(resp, dict):
        # New ollama package returns response in 'response' key
        text = resp.get("response", "")
        if not text:
            # Fallback to other possible keys
            if "choices" in resp and resp["choices"]:
                text = (
                    resp["choices"][0].get("message", {}).get("content")
                    or resp["choices"][0].get("content")
                    or resp["choices"][0].get("text")
                )
            if not text:
                text = resp.get("output") or resp.get("text") or str(resp)
    else:
        text = str(resp)
    return text, resp, t_elapsed, None


# ===== RUN BENCHMARK =====
def main():
    # No client needed with new ollama package - use ollama module directly
    rows = []
    for model in MODELS:
        for run in range(RUNS_PER_MODEL):
            for idx, sample in enumerate(SAMPLES):
                prompt = STRUCTURED_PROMPT.format(feedback=sample)
                text, raw_resp, latency, error = run_single(
                    None, model, prompt, max_tokens=180, temperature=0
                )
                parsed = None
                parse_ok = False
                suggestions_count = 0
                has_reply = False
                if text and not error:
                    parsed = extract_json(text)
                    parse_ok = parsed is not None
                    if parse_ok:
                        suggestions = parsed.get("suggestions", [])
                        suggestions_count = (
                            len(suggestions) if isinstance(suggestions, list) else 0
                        )
                        has_reply = bool(parsed.get("personalized_reply"))
                row = {
                    "model": model,
                    "run": run + 1,
                    "sample_idx": idx,
                    "sample_text": sample,
                    "latency_s": round(latency, 3),
                    "parse_ok": bool(parse_ok),
                    "suggestions_count": suggestions_count,
                    "has_personalized_reply": bool(has_reply),
                    "raw_text_snippet": (text or "")[:300].replace("\n", " "),
                    "error": error or "",
                }
                print(
                    f"[{model}] run {run+1} sample {idx} latency {row['latency_s']}s parse_ok={row['parse_ok']} suggestions={row['suggestions_count']}"
                )
                rows.append(row)

    # write CSV
    keys = [
        "model",
        "run",
        "sample_idx",
        "sample_text",
        "latency_s",
        "parse_ok",
        "suggestions_count",
        "has_personalized_reply",
        "raw_text_snippet",
        "error",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # summary
    import statistics

    print("\nSUMMARY")
    for model in MODELS:
        model_rows = [r for r in rows if r["model"] == model]
        latencies = [r["latency_s"] for r in model_rows]
        parse_rate = sum(1 for r in model_rows if r["parse_ok"]) / len(model_rows)
        avg_lat = statistics.mean(latencies) if latencies else None
        median_lat = statistics.median(latencies) if latencies else None
        avg_sugg = (
            statistics.mean([r["suggestions_count"] for r in model_rows])
            if model_rows
            else 0
        )
        print(
            f"- {model}: runs={len(model_rows)} avg_lat={avg_lat:.2f}s median={median_lat:.2f}s parse_rate={parse_rate:.2%} avg_suggestions={avg_sugg:.2f}"
        )

    print(f"\nResults written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
