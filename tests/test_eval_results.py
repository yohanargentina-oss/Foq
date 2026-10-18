"""
The published numbers must be the numbers the shipped package produces.

Offline (always): recompute the exam results from the raw log-probabilities in
eval/results/ with the temperature of each shipped profile and the engine's default
needs_review threshold, and compare with eval/results/calibration_*.json, the single
source of every published figure (eval/RESULTS.md, README, BENCHMARKS, site).

Live (only when a Foq server runs on 127.0.0.1:8089): FoqEngine, with its default
profile choice, replays the first exam cases and must give the recorded decisions and
confidences.
"""

import json
import math
import unittest
from pathlib import Path

from foq import FoqEngine
from foq.engine import SEUIL_REVIEW_MESURE
from foq.schemas import ClassificationChoice

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
PROFILES = {"lora": "calibration_profile.json", "bare": "calibration_profile_bare.json"}
LIVE_CASES = 60


def load_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def calibrated(logprobs, T):
    keys = sorted(logprobs)
    z = [logprobs[k] / T for k in keys]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return {k: v / s for k, v in zip(keys, e)}


def ece(conf, correct, n_bins=15):
    bins = [[] for _ in range(n_bins)]
    for c, ok in zip(conf, correct):
        b = min(n_bins - 1, max(0, math.ceil(c * n_bins) - 1))
        bins[b].append((c, ok))
    n = len(conf)
    return sum(len(b) / n * abs(sum(o for _, o in b) / len(b) - sum(c for c, _ in b) / len(b))
               for b in bins if b)


class TestPublishedNumbers(unittest.TestCase):
    def check(self, tag):
        profile = json.loads((ROOT / "foq" / PROFILES[tag]).read_text(encoding="utf-8"))
        report = json.loads((RESULTS / f"calibration_{tag}.json").read_text(encoding="utf-8"))
        T = profile["temperature"]
        self.assertAlmostEqual(T, report["temperature_fitted"], places=4)

        rows = load_jsonl(RESULTS / f"raw_{tag}_exam_test.jsonl")
        conf, correct = [], []
        for r in rows:
            p = calibrated(r["logprobs"], T)
            best = max(p, key=p.get)
            conf.append(p[best])
            correct.append(best == r["gold"])
        n = len(rows)
        fitted = report["on_exam_test"]["fitted"]
        self.assertEqual(n, fitted["n"])
        self.assertAlmostEqual(sum(correct) / n * 100, fitted["accuracy_pct"], delta=0.05)
        self.assertAlmostEqual(ece(conf, correct) * 100, fitted["ece_pct"], delta=0.05)

        kept = [ok for c, ok in zip(conf, correct) if c >= SEUIL_REVIEW_MESURE]
        at_default = next(x for x in fitted["needs_review"] if x["threshold"] == SEUIL_REVIEW_MESURE)
        self.assertAlmostEqual((1 - len(kept) / n) * 100, at_default["review_share_pct"], delta=0.05)
        self.assertAlmostEqual(sum(kept) / len(kept) * 100, at_default["accuracy_on_kept_pct"], delta=0.05)

        detail = report["on_exam_test_detail_fitted_T"]
        self.assertEqual(detail["default_threshold"], SEUIL_REVIEW_MESURE)
        for h in detail["high_confidence"]:
            sel = [ok for c, ok in zip(conf, correct) if c >= h["min_confidence"]]
            self.assertEqual((len(sel), sum(sel)), (h["decisions"], h["correct"]), h["min_confidence"])
        for cat, x in detail["per_category"].items():
            sel = [(c, ok) for c, ok, r in zip(conf, correct, rows) if r["category"] == cat]
            k = [ok for c, ok in sel if c >= SEUIL_REVIEW_MESURE]
            self.assertEqual((len(sel), sum(ok for _, ok in sel), len(k), sum(k)),
                             (x["n"], x["correct"], x["kept_at_default_threshold"], x["correct_kept"]), cat)

    def test_model_with_adapter(self):
        self.check("lora")

    def test_model_alone(self):
        self.check("bare")


class TestLiveServerMatchesExam(unittest.TestCase):
    def test_engine_replays_recorded_decisions(self):
        engine = FoqEngine()
        try:
            if not engine.is_server_ready():
                self.skipTest("Foq server not running on port 8089")
            tag = "lora" if engine._adapters else "bare"
            T = engine.profile.temperature
            raw = {r["id"]: r for r in load_jsonl(RESULTS / f"raw_{tag}_exam_test.jsonl")}
            cases = load_jsonl(ROOT / "eval" / "data" / "exam_test.jsonl")[:LIVE_CASES]
            same = 0
            for c in cases:
                res = engine.decide(c["context"], ClassificationChoice("x", c["question"], c["options"]))
                expected = calibrated(raw[c["id"]]["logprobs"], T)
                best = max(expected, key=expected.get)
                if res["decision_key"] == best:
                    same += 1
                    self.assertAlmostEqual(res["confidence"], expected[best], delta=0.03)
            # GPU kernels are not bit-exact between runs: allow one near-tie flip
            self.assertGreaterEqual(same, LIVE_CASES - 1, f"{tag}: {same}/{LIVE_CASES} identical")
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
