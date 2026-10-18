# Benchmarks

Every accuracy and calibration number on this page is copied from
[`eval/RESULTS.md`](eval/RESULTS.md), and every latency number from
[`eval/LATENCY.md`](eval/LATENCY.md). RESULTS.md is
`python eval/report.py` generates from `eval/results/calibration_*.json`. The
pipeline that produces them is in [`eval/README.md`](eval/README.md) and can be
rerun on your own machine. What has not been measured is marked **[not yet
measured]** rather than estimated.

---

## 1. The exam

- **Source**: 2,500 generated multiple-choice cases (3 options, 13 categories).
  None of them is in the training set of the decision adapter v1 (checked by
  exact match and by near-duplicates; `eval/build_split.py` prints the report).
- **Split**, stratified by category:
  - `calib_val` — 1,250 cases, used only to fit the confidence temperature;
  - `exam_test` — 1,250 cases, never used to fit or choose anything.
- **Two task families**: business categories close to Foq's intended use
  (ticket routing, security, sentiment, triage — 325 exam cases) and
  reasoning puzzles, harder than typical production inputs (925 exam cases).
- **Two configurations**: Foq 8B alone (`NO_LORA=1`, or adapter not installed),
  and Foq 8B + LoRA decision adapter v1 (the default once `foq setup` has
  installed it).

Limits: the cases come from generators, not from real traffic; 21 % of them
were later rejected by the 27B judge when a later training set was built, and
are kept (removing them would flatter the score). See `eval/README.md`.

---

## 2. Accuracy on `exam_test`

| | Foq 8B alone | Foq 8B + adapter v1 |
|---|---|---|
| All cases (1,250) [95 % CI] | 64.8 % [62.1–67.4] | 68.0 % [65.4–70.5] |
| Business categories (325) [95 % CI] | 78.2 % [73.3–82.3] | 83.1 % [78.6–86.8] |
| Reasoning puzzles (925) [95 % CI] | 60.1 % [56.9–63.2] | 62.7 % [59.5–65.8] |

With the adapter, overall accuracy goes from 64.8 % to 68.0 % on this exam.

### When Foq is very sure (adapter v1, fitted temperature)

| Confidence at least | Decisions | Correct | Accuracy [95 % CI] |
|---|---|---|---|
| 0.9 | 296 | 289 | 97.6 % [95.2–98.8] |
| 0.95 | 152 | 150 | 98.7 % [95.3–99.6] |
| 0.97 | 79 | 79 | 100.0 % [95.4–100.0] |
| 0.98 | 38 | 38 | 100.0 % [90.8–100.0] |

### By category (adapter v1, fitted temperature; "kept" = confidence ≥ 0.8)

| Category | Cases | Accuracy | Kept | Correct among kept |
|---|---|---|---|---|
| Information security | 100 | 94.0 % | 61 | 61 |
| Ticket routing | 75 | 88.0 % | 44 | 43 |
| Sentiment | 75 | 86.7 % | 43 | 43 |
| Multiple negations | 100 | 85.0 % | 72 | 65 |
| Fallacious causality | 75 | 81.3 % | 39 | 39 |
| Counter-intuitive physiology | 100 | 75.0 % | 45 | 41 |
| Common sense | 100 | 66.0 % | 34 | 34 |
| Linguistic riddles | 100 | 65.0 % | 26 | 24 |
| Counter-intuitive maths | 125 | 63.2 % | 49 | 46 |
| Emergency triage | 75 | 60.0 % | 22 | 19 |
| Spatial reasoning | 100 | 47.0 % | 11 | 10 |
| Race positions | 150 | 45.3 % | 4 | 4 |
| Temporal reasoning | 75 | 45.3 % | 15 | 11 |

Emergency triage is a weak spot: 60.0 % overall, 86.4 % on the decisions kept.
The same tables for the model alone are in `eval/RESULTS.md`.

---

## 3. Calibration (temperature scaling)

Foq rescales its probabilities with a single temperature T, fitted on
`calib_val` and evaluated on `exam_test`. Expected calibration error (ECE,
15 bins) is the gap between stated confidence and observed accuracy; lower is
better.

| Temperature | Foq 8B alone: ECE [95 % CI] | Foq 8B + adapter v1: ECE [95 % CI] |
|---|---|---|
| 1 (raw model) | 22.75 % [20.33–25.42] | 16.67 % [14.25–19.06] |
| 0.1 (profile shipped in 1.0.5) | 33.55 % [31.0–36.24] | 30.09 % [27.58–32.81] |
| fitted on `calib_val` | **5.5 %** [4.16–8.4] (T = 3.6381) | **4.77 %** [3.4–7.29] (T = 2.6353) |

With the fitted temperature, mean confidence is 66.8 % for 64.8 % accuracy
(model alone) and 69.3 % for 68.0 % accuracy (with adapter). The profiles
shipped on this branch are these fitted temperatures:
`foq/calibration_profile.json` (with adapter) and
`foq/calibration_profile_bare.json` (model alone).

By family, a single temperature leaves the model slightly under-confident on
business tasks (ECE 10.08 % alone, 7.98 % with adapter) and well calibrated on
puzzles (7.05 % and 5.76 %).

---

## 4. What `needs_review` does

Decisions whose confidence is below the threshold are flagged
`needs_review = True` instead of being returned as certain. With the fitted
temperature and the adapter:

| Threshold | Sent to review | Accuracy on decisions kept [95 % CI] | Errors caught |
|---|---|---|---|
| 0.5 | 22.1 % | 74.9 % [72.1–77.6] (974 kept) | 39.0 % |
| 0.6 | 39.7 % | 82.9 % [80.0–85.4] (754 kept) | 67.8 % |
| 0.7 | 52.4 % | 90.3 % [87.6–92.4] (595 kept) | 85.5 % |
| **0.8 (default)** | **62.8 %** | **94.6 %** [92.2–96.3] (465 kept) | **93.8 %** |
| 0.9 | 76.3 % | 97.6 % [95.2–98.8] (296 kept) | 98.2 % |
| 0.95 | 87.8 % | 98.7 % [95.3–99.6] (152 kept) | 99.5 % |

For the model alone at 0.8: 70.2 % sent to review, 91.1 % [87.8–93.6] accuracy
on the 372 decisions kept.

The default threshold moved from 0.95 to 0.8: with an honest temperature, 0.95
sends 87.8 % of decisions to review. With the old profile (T = 0.1), 0.95 sent
only 9.3 % to review and caught 14.8 % of the errors.

The full threshold tables, for both configurations and both temperatures, are in
[`eval/RESULTS.md`](eval/RESULTS.md).

---

## 5. Latency

From [`eval/LATENCY.md`](eval/LATENCY.md), produced by `eval/latency.py`: the 1,250
`exam_test` cases, one llama-server at a time, 3 passes per configuration,
sequential requests, localhost, NVIDIA GeForce RTX 4080 SUPER, Windows 11.

| Configuration | Server median | Server P95 | HTTP median | HTTP P95 |
|---|---|---|---|---|
| Foq 8B, no adapter | 18.35 ms | 21.49 ms | 31.8 ms | 42.04 ms |
| Foq 8B + adapter v1 | 24.82 ms | 27.14 ms | 35.66 ms | 47.5 ms |

"Server" is the time llama-server reports; "HTTP" is what a Python client on the
same machine waits for. Your hardware will give different numbers:
`foq benchmark` measures them.

No comparison with cloud models is made: the advantages of running locally
(offline, nothing leaves the machine, no per-call cost, open weights) are facts,
not measurements.

---

## 6. Foq vs Laya: 9 illustrative examples

[`examples/benchmark_foq_vs_laya.py`](examples/benchmark_foq_vs_laya.py) runs 9
cases that we chose against [Laya](https://github.com/NandhaKishorM/laya)
(`laya 0.3.4`, ModernBERT-large 421M and mmBERT-base 322M). In those examples:

- a German cancellation request — Laya's script-based router sent it to its
  English model; Foq handled it;
- a negation (*"I am NOT having any billing problem, the website JS is broken"*)
  and a prompt injection — Laya's confidence dropped sharply; Foq kept the right
  route;
- an *"EMERGENCY: the main database cluster is down…"* ticket — Laya marked it
  non-urgent and Foq flagged it urgent. On our exam, though, emergency triage is
  one of Foq's weak categories (60.0 %, see §2), so this example says little.

Laya is far smaller and a reasonable choice for fixed-label classification on
short inputs (its context is 512 or 1,024 tokens; Foq's is 4,096, and Foq can
also extract Pydantic objects). These 9 cases illustrate behaviour; they were
picked by us and do not rank the two systems.

---

## 7. Withdrawn figures

Earlier versions of this page and of the site published figures that do not
hold up. They are withdrawn rather than repeated here:

- **The "production exam" score and the adapter gain measured on it.** Its
  "unseen" cases came from the same generators as the training data, and the
  others were used to choose between adapters. On the held-out exam the
  adapter takes accuracy from 64.8 % to 68.0 %.
- **The post-calibration ECE.** It was fitted and measured on a tiny calibration
  set that contained no errors; the optimizer stopped at its lower bound
  (T = 0.1). On held-out data that profile gives an ECE of 30.09 % (§3).
- **The former name of the calibration method.** It is temperature scaling, and is now called that.
- **Speed and cost comparisons with cloud models.** They were estimates against
  large models, not measurements. Foq now states only its own measured latency
  (§5).
- **The 0.95 default threshold.** It is now 0.8, set from the held-out exam (§4).
