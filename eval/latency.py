"""
Measure Foq 8B decision latency on eval/data/exam_test.jsonl, with and without the adapter.

For each configuration the script starts ONE llama-server (Foq build), waits for it,
sends a few warm-up requests (not counted), replays the 1,250 exam cases one at a time
exactly like FoqEngine does (/completion, n_predict 1, n_probs 25, cache_prompt), then
stops the server before starting the next one. Two clocks are recorded per case:

- server time: `timings.prompt_ms + timings.predicted_ms` reported by llama-server
  (prompt evaluation + the one generated token), plus `timings.prompt_n` (tokens evaluated
  after the cached prefix);
- HTTP round trip: wall time of the POST seen by the Python client on localhost.

    python eval/latency.py                       # both configurations
    python eval/latency.py --configs lora        # one only

Output: eval/results/latency.json (median, P95, mean, min, max per clock and
configuration, plus the GPU state before each run). Check `nvidia-smi` first: nothing
else heavy should be on the GPU while it runs.
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import httpx  # noqa: E402

from foq.schemas import ClassificationChoice  # noqa: E402

HOME = os.path.expanduser("~")
EXE = os.environ.get("LLAMA_EXE") or os.path.join(HOME, ".local", "bin", "foq-llama",
                                                  "llama-server.exe" if os.name == "nt" else "llama-server")
MODEL = os.path.join(HOME, ".models", "foq", "foq-reflex-8b-pq2_0.gguf")
ADAPTER = os.path.join(ROOT, "adapters", "foq_decision_8b", "foq_decision_8b.gguf")
PORT = 8091
WARMUP = 10
CONFIGS = {"bare": [], "lora": ["--lora", ADAPTER]}


def pct(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def summary(xs):
    return {"n": len(xs), "median": round(statistics.median(xs), 2), "p95": round(pct(xs, 0.95), 2),
            "mean": round(statistics.fmean(xs), 2), "min": round(min(xs), 2), "max": round(max(xs), 2)}


def gpu_state():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.used,memory.total,utilization.gpu",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=20).stdout.strip()
        name, drv, used, total, util = [x.strip() for x in out.split(",")]
        return {"name": name, "driver": drv, "memory_used": used, "memory_total": total, "utilization": util}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def run_config(tag, cases, port):
    cmd = [EXE, "-m", MODEL, *CONFIGS[tag], "-ngl", "99", "-c", "4096", "-np", "1", "--port", str(port)]
    gpu_before = gpu_state()
    log_path = os.path.join(tempfile.gettempdir(), f"foq_latency_server_{tag}.log")
    log = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    try:
        client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=60)
        for _ in range(240):
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if proc.poll() is not None:
                raise RuntimeError(f"llama-server exited, see {log_path}")
            time.sleep(0.5)
        else:
            raise RuntimeError("llama-server did not become ready")

        def ask(c):
            schema = ClassificationChoice("case", c["question"], c["options"])
            payload = {"prompt": schema.format_prompt(c["context"]), "n_predict": 1,
                       "n_probs": 25, "temperature": 0.0, "cache_prompt": True}
            t0 = time.perf_counter()
            r = client.post("/completion", json=payload)
            ms = (time.perf_counter() - t0) * 1000
            r.raise_for_status()
            d = r.json()
            probs = d.get("completion_probabilities", [])
            lp = {k: -25.0 for k in schema.get_keys()}
            for it in (probs[0].get("top_logprobs", []) if probs else []):
                tok = it.get("token", "").strip().strip("[]()").upper()
                if tok in lp:
                    lp[tok] = max(lp[tok], it.get("logprob", -25.0))
            pred = max(lp, key=lp.get)
            return ms, d.get("timings", {}), pred == schema.get_keys()[c["answer_idx"]]

        adapters = client.get("/lora-adapters").json()
        for c in cases[:WARMUP]:
            ask(c)
        http, server, prompt_n, correct = [], [], [], 0
        for i, c in enumerate(cases, 1):
            ms, t, ok = ask(c)
            correct += ok
            http.append(ms)
            server.append(t["prompt_ms"] + t["predicted_ms"])
            prompt_n.append(t["prompt_n"])
            if i % 250 == 0:
                print(f"  [{tag}] {i}/{len(cases)}  median HTTP {statistics.median(http):.1f} ms", flush=True)
        return {"server_command": " ".join(os.path.basename(x) if x in (EXE, MODEL, ADAPTER) else x for x in cmd),
                "lora_adapters_loaded": [{"path": os.path.basename(a.get("path", "")), "scale": a.get("scale")}
                                         for a in adapters],
                "accuracy_check_pct": round(correct / len(cases) * 100, 1),
                "gpu_before_start": gpu_before, "gpu_during_run": gpu_state(),
                "warmup_requests_not_counted": WARMUP,
                "server_ms": summary(server), "http_round_trip_ms": summary(http),
                "prompt_tokens_evaluated": summary(prompt_n), "_server": server, "_http": http}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", default=["bare", "lora"], choices=list(CONFIGS))
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--runs", type=int, default=3, help="passes over the exam per configuration (alternated)")
    args = ap.parse_args()

    src = os.path.join(ROOT, "eval", "data", "exam_test.jsonl")
    cases = [json.loads(l) for l in open(src, encoding="utf-8") if l.strip()]
    out_path = os.path.join(ROOT, "eval", "results", "latency.json")
    prev = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
    res = {"measured_at": time.strftime("%Y-%m-%d %H:%M:%S"), "set": "exam_test", "cases": len(cases),
           "machine": {"os": platform.platform(), "cpu": platform.processor()},
           "method": f"one llama-server at a time (restarted for each pass), {args.runs} passes per configuration "
                     "alternated bare/lora, sequential requests (concurrency 1), localhost; "
                     "server_ms = timings.prompt_ms + timings.predicted_ms; pooled = all passes together",
           "configs": prev.get("configs", {})}
    runs = {tag: [] for tag in args.configs}
    for k in range(args.runs):
        for tag in args.configs:
            r = run_config(tag, cases, args.port)
            runs[tag].append(r)
            print(f"[{tag} pass {k + 1}] server median {r['server_ms']['median']} ms, P95 {r['server_ms']['p95']} ms | "
                  f"HTTP median {r['http_round_trip_ms']['median']} ms, P95 {r['http_round_trip_ms']['p95']} ms")
    for tag, rs in runs.items():
        server = [x for r in rs for x in r.pop("_server")]
        http = [x for r in rs for x in r.pop("_http")]
        res["configs"][tag] = {"passes": rs, "pooled_server_ms": summary(server),
                               "pooled_http_round_trip_ms": summary(http)}
        c = res["configs"][tag]
        print(f"[{tag} pooled] server median {c['pooled_server_ms']['median']} ms, P95 {c['pooled_server_ms']['p95']} ms | "
              f"HTTP median {c['pooled_http_round_trip_ms']['median']} ms, P95 {c['pooled_http_round_trip_ms']['p95']} ms")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"-> {os.path.relpath(out_path, ROOT)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
