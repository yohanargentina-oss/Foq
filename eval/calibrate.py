"""
Fit the temperature on calib_val, then measure calibration on exam_test (never used for fitting).

Reads the raw log-probabilities saved by eval/run_cases.py, so no model call is needed.
For each configuration (tag) it compares three temperatures on exam_test:
  - T = 1           (raw model probabilities)
  - T = old profile (foq/calibration_profile.json, 0.1, as shipped in foq 1.0.5)
  - T = fitted      (NLL minimised on calib_val; search bounds are wide and a fit
                     ending on a bound is reported as such)
and reports accuracy, ECE (15 equal-width bins, bootstrap 95 % CI), Brier score,
NLL, and what the needs_review threshold does (share sent to review, accuracy on
the decisions kept).

    python eval/calibrate.py --tag lora
Output: eval/results/calibration_<tag>.json (single source of truth for published numbers)
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import minimize_scalar

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BOUNDS = (0.02, 50.0)
N_BINS = 15
THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
SEED = 20261018
# Temperature of foq/calibration_profile.json as shipped in foq 1.0.5 (fitted on 10 cases)
OLD_PROFILE_T = 0.1000046791375977
# Categories closest to Foq's intended use (typed business decisions); the other nine
# are counter-intuitive reasoning puzzles.
BUSINESS = {"routage", "securite_info", "sentiment", "triage"}


def load(tag, name):
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "eval", "results", f"raw_{tag}_{name}.jsonl"),
                                         encoding="utf-8")]
    keys = sorted(rows[0]["logprobs"])
    L = np.array([[r["logprobs"][k] for k in keys] for r in rows])
    y = np.array([keys.index(r["gold"]) for r in rows])
    cats = np.array([r["category"] for r in rows])
    biz = np.isin(cats, list(BUSINESS))
    return L, y, biz, cats


def softmax(L, T):
    z = L / T
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def nll(L, y, T):
    p = softmax(L, T)[np.arange(len(y)), y]
    return float(-np.mean(np.log(np.clip(p, 1e-12, 1))))


def ece(conf, correct, n_bins=N_BINS):
    edges = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(conf, edges[1:-1], right=True), 0, n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(total)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round((c - h) * 100, 1), round((c + h) * 100, 1))


def evaluate(L, y, T):
    p = softmax(L, T)
    pred = p.argmax(axis=1)
    conf = p.max(axis=1)
    correct = (pred == y).astype(float)
    n = len(y)
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(1000):
        s = rng.integers(0, n, n)
        boots.append(ece(conf[s], correct[s]))
    onehot = np.eye(p.shape[1])[y]
    out = {
        "temperature": round(float(T), 4),
        "n": n,
        "accuracy_pct": round(correct.mean() * 100, 1),
        "accuracy_ci95_pct": wilson(int(correct.sum()), n),
        "mean_confidence_pct": round(conf.mean() * 100, 1),
        "ece_pct": round(ece(conf, correct) * 100, 2),
        "ece_ci95_pct": [round(float(np.percentile(boots, 2.5)) * 100, 2),
                         round(float(np.percentile(boots, 97.5)) * 100, 2)],
        "brier": round(float(np.mean(np.sum((p - onehot) ** 2, axis=1))), 4),
        "nll": round(nll(L, y, T), 4),
        "needs_review": [],
    }
    for t in THRESHOLDS:
        kept = conf >= t
        k = int(kept.sum())
        ok = int(correct[kept].sum())
        out["needs_review"].append({
            "threshold": t,
            "review_share_pct": round((1 - kept.mean()) * 100, 1),
            "kept": k,
            "accuracy_on_kept_pct": round(ok / k * 100, 1) if k else None,
            "accuracy_on_kept_ci95_pct": wilson(ok, k),
            "errors_kept": k - ok,
            "errors_caught_pct": round(float(((~kept) & (correct == 0)).sum() / max(1, (correct == 0).sum()) * 100), 1),
        })
    return out


HIGH_CONFIDENCE = [0.9, 0.95, 0.97, 0.98, 0.99]
DEFAULT_THRESHOLD = 0.8  # foq.engine.SEUIL_REVIEW_MESURE


def detail(L, y, cats, T):
    """Per-category accuracy (overall and on decisions kept at the default threshold),
    and accuracy above high confidence levels."""
    p = softmax(L, T)
    conf = p.max(axis=1)
    correct = p.argmax(axis=1) == y
    per_cat = {}
    for c in sorted(set(cats)):
        m = cats == c
        kept = m & (conf >= DEFAULT_THRESHOLD)
        per_cat[c] = {
            "n": int(m.sum()), "correct": int(correct[m].sum()),
            "accuracy_pct": round(float(correct[m].mean() * 100), 1),
            "kept_at_default_threshold": int(kept.sum()),
            "correct_kept": int(correct[kept].sum()),
            "accuracy_on_kept_pct": round(float(correct[kept].mean() * 100), 1) if kept.any() else None,
        }
    high = []
    for t in HIGH_CONFIDENCE:
        m = conf >= t
        k, ok = int(m.sum()), int(correct[m].sum())
        high.append({"min_confidence": t, "decisions": k, "correct": ok,
                     "accuracy_ci95_pct": wilson(ok, k)})
    return {"default_threshold": DEFAULT_THRESHOLD, "per_category": per_cat, "high_confidence": high}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--write-profile", help="also write a Foq calibration profile, e.g. foq/calibration_profile.json")
    args = ap.parse_args()

    Lv, yv, _, _ = load(args.tag, "calib_val")
    Lt, yt, bt, ct = load(args.tag, "exam_test")

    res = minimize_scalar(lambda T: nll(Lv, yv, T), bounds=BOUNDS, method="bounded",
                          options={"xatol": 1e-4})
    T_fit = float(res.x)
    at_bound = min(abs(T_fit - BOUNDS[0]), abs(T_fit - BOUNDS[1])) < 1e-2

    old_T = OLD_PROFILE_T

    report = {
        "config": args.tag,
        "fit_set": {"name": "calib_val", "n": int(len(yv)),
                    "accuracy_pct": round(float((Lv.argmax(1) == yv).mean() * 100), 1)},
        "eval_set": {"name": "exam_test", "n": int(len(yt))},
        "temperature_fitted": round(T_fit, 4),
        "temperature_fit_at_search_bound": at_bound,
        "search_bounds": BOUNDS,
        "ece_bins": N_BINS,
        "on_exam_test": {
            "raw_T1": evaluate(Lt, yt, 1.0),
            "old_profile": evaluate(Lt, yt, old_T),
            "fitted": evaluate(Lt, yt, T_fit),
        },
        "on_exam_test_detail_fitted_T": detail(Lt, yt, ct, T_fit),
        "on_exam_test_by_group_fitted_T": {
            "business_categories": evaluate(Lt[bt], yt[bt], T_fit),
            "reasoning_puzzles": evaluate(Lt[~bt], yt[~bt], T_fit),
        },
    }
    out = os.path.join(ROOT, "eval", "results", f"calibration_{args.tag}.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2)

    print(f"=== {args.tag}: T fitted on calib_val ({len(yv)} cases, accuracy "
          f"{report['fit_set']['accuracy_pct']} %) = {T_fit:.3f}"
          f"{'  [AT SEARCH BOUND]' if at_bound else ''}")
    print(f"    measured on exam_test ({len(yt)} cases, never used for fitting)")
    rows = list(report["on_exam_test"].items()) +         [(f"fitted/{k[:8]}", v) for k, v in report["on_exam_test_by_group_fitted_T"].items()]
    for name, r in rows:
        nr = next(x for x in r["needs_review"] if x["threshold"] == 0.95)
        print(f"  {name:<16} T={r['temperature']:<7} acc {r['accuracy_pct']} % {r['accuracy_ci95_pct']} | "
              f"mean conf {r['mean_confidence_pct']} % | ECE {r['ece_pct']} % {r['ece_ci95_pct']} | "
              f"Brier {r['brier']} | NLL {r['nll']}")
        print(f"  {'':<16} needs_review@0.95: {nr['review_share_pct']} % sent to review, "
              f"accuracy on kept {nr['accuracy_on_kept_pct']} % {nr['accuracy_on_kept_ci95_pct']}, "
              f"{nr['errors_caught_pct']} % of errors caught")
    print(f"-> {os.path.relpath(out, ROOT)}")

    if args.write_profile:
        fitted = report["on_exam_test"]["fitted"]
        profile = {
            "model_alias": {"lora": "foq-8b-lora", "bare": "foq-8b"}.get(args.tag, args.tag),
            "temperature": report["temperature_fitted"],
            "ece": round(fitted["ece_pct"] / 100, 4),
            "brier_score": fitted["brier"],
            "fitted_on": f"eval/data/calib_val.jsonl ({report['fit_set']['n']} cases)",
            "measured_on": f"eval/data/exam_test.jsonl ({report['eval_set']['n']} cases, held out)",
            "source": f"eval/results/calibration_{args.tag}.json",
        }
        path = os.path.join(ROOT, args.write_profile)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(profile, f, indent=2)
        print(f"-> {args.write_profile}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
