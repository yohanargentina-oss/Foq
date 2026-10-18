"""
Run one held-out set against a running Foq server and save the raw results.

For every case it stores the raw log-probabilities of each option letter (no
calibration applied), so that calibration can be fitted and evaluated afterwards
without querying the model again. The prompt is built by Foq's own
ClassificationChoice.format_prompt and parsed like FoqEngine does (missing letter = -25).

    python eval/run_cases.py --set exam_test --base-url http://127.0.0.1:8090 --tag lora
    python eval/run_cases.py --set calib_val --base-url http://127.0.0.1:8089 --tag bare

Output: eval/results/raw_<tag>_<set>.jsonl, then prints accuracy (Wilson 95 % CI)
and median latency.
"""

import argparse
import json
import math
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import httpx  # noqa: E402

from foq.schemas import ClassificationChoice  # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def letter_logprobs(data, keys):
    out = {k: -25.0 for k in keys}
    probs = data.get("completion_probabilities", [])
    if probs:
        for it in probs[0].get("top_logprobs", []):
            tok = it.get("token", "").strip().strip("[]()").upper()
            if tok in out:
                out[tok] = max(out[tok], it.get("logprob", -25.0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=["calib_val", "exam_test"])
    ap.add_argument("--base-url", default="http://127.0.0.1:8089")
    ap.add_argument("--tag", required=True, help="configuration name, e.g. bare or lora")
    args = ap.parse_args()

    src = os.path.join(ROOT, "eval", "data", f"{args.set}.jsonl")
    cases = [json.loads(l) for l in open(src, encoding="utf-8") if l.strip()]
    out_dir = os.path.join(ROOT, "eval", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"raw_{args.tag}_{args.set}.jsonl")

    client = httpx.Client(base_url=args.base_url, timeout=60)
    client.get("/health").raise_for_status()

    ok, lat = 0, []
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for i, c in enumerate(cases, 1):
            schema = ClassificationChoice(f"case_{i}", c["question"], c["options"])
            keys = schema.get_keys()
            payload = {"prompt": schema.format_prompt(c["context"]), "n_predict": 1,
                       "n_probs": 25, "temperature": 0.0, "cache_prompt": True}
            t0 = time.perf_counter()
            r = client.post("/completion", json=payload)
            ms = (time.perf_counter() - t0) * 1000
            r.raise_for_status()
            lp = letter_logprobs(r.json(), keys)
            pred = max(keys, key=lambda k: lp[k])
            gold = keys[c["answer_idx"]]
            ok += pred == gold
            lat.append(ms)
            f.write(json.dumps({"id": c["id"], "category": c["category"], "gold": gold,
                                "pred": pred, "logprobs": lp, "latency_ms": round(ms, 2)}) + "\n")
            if i % 250 == 0:
                print(f"  {i}/{len(cases)}  accuracy so far {ok/i*100:.1f} %", flush=True)

    n = len(cases)
    lo, hi = wilson(ok, n)
    lat.sort()
    print(f"[{args.tag} / {args.set}] accuracy {ok}/{n} = {ok/n*100:.1f} % "
          f"(95 % CI {lo*100:.1f}-{hi*100:.1f}) | median latency {lat[n//2]:.1f} ms (HTTP round trip)")
    print(f"raw results: {os.path.relpath(out_path, ROOT)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
