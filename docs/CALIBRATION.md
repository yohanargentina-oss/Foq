# Calibration and `needs_review`

## What calibration does

The model's raw confidence is too high: with the adapter, its mean confidence is
83.9 % for 68.0 % accuracy on the held-out exam. Foq corrects this with
**temperature scaling**: the scores of the possible answers are divided by a
single temperature T before the softmax. T > 1 flattens the probabilities, so
confidence drops to match how often the model is actually right.

T is fitted on `calib_val` (1,250 cases) and checked on `exam_test` (1,250 other
cases, never used for fitting). Numbers from [`eval/RESULTS.md`](../eval/RESULTS.md):

| Configuration | Fitted T | ECE on `exam_test`, raw | ECE on `exam_test`, fitted T |
|---|---|---|---|
| Foq 8B alone | 3.6381 | 22.75 % | 5.5 % |
| Foq 8B + adapter v1 | 2.6353 | 16.67 % | 4.77 % |

ECE (expected calibration error, 15 bins) is the average gap between stated
confidence and observed accuracy.

## Shipped profiles

- `foq/calibration_profile.json` — model + adapter v1 (T = 2.6353).
- `foq/calibration_profile_bare.json` — model alone (T = 3.6381).

The engine asks the server which LoRA adapters are loaded (`/lora-adapters`) and
picks the matching profile.

## Choosing the `needs_review` threshold

Decisions whose calibrated confidence is below `min_confidence` are flagged
`needs_review = True`. `decide()` uses 0.8 by default; `system_one()` flags only
when you pass `min_confidence`. With the adapter, on `exam_test`:

| Threshold | Sent to review | Accuracy on decisions kept | Errors caught |
|---|---|---|---|
| 0.6 | 39.7 % | 82.9 % | 67.8 % |
| 0.7 | 52.4 % | 90.3 % | 85.5 % |
| **0.8 (default)** | **62.8 %** | **94.6 %** | **93.8 %** |
| 0.9 | 76.3 % | 97.6 % | 98.2 % |

Lower the threshold if a human reviewer is expensive and some errors are
acceptable; raise it if errors are costly. A single temperature leaves the model
slightly under-confident on business tasks (ECE 7.98 %): on those, the default
threshold is on the cautious side.

## Refitting on your own data

The fitting code is `foq/calibration.py` (`TemperatureScaler`); the full pipeline
used for the published profiles is `eval/calibrate.py`, described in
[`eval/README.md`](../eval/README.md). Fit on cases that contain errors, and
measure on a separate set: a calibration set where the model is always right
pushes T to its lower bound and makes every confidence close to 100 %.
