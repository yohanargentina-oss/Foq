# 🗺️ Foq Roadmap

This document summarizes completed features and future development directions for the **Foq** project.

---

## ✅ Completed & Validated Features

| Module | Feature | Status |
|---|---|:---:|
| **System 1 Engine** | Single feed-forward pass inference, logprob extraction without text decoding | ✅ **Done** |
| **1:1 Primitives** | Official `Boolean` (alias `Noul`), `Choice` (typed options), `Score` (ordered/continuous) primitives | ✅ **Done** |
| **Hierarchical Extraction** | `Structure` primitive & `extract()` method with Pydantic v2 validation and GBNF grammar | ✅ **Done** |
| **Async Concurrency** | Non-blocking `system_one_async()`, `decide_async()`, `extract_async()` methods | ✅ **Done** |
| **RLCD Calibration** | `TemperatureScaler` math layer with ECE and Brier Score computation, JSON profile | ✅ **Done** |
| **Application Security** | Anti prompt-injection / jailbreak `FoqSecurityGuard` and FastAPI ASGI middleware | ✅ **Done** |
| **Reflex Web Navigation** | High-rate `FoqBrowserAgent` with `DOMPruner` (200-400 token DOM compression) | ✅ **Done** |
| **Reflex DOOM Pilot** | Real-time control of Chocolate Doom 1993, raycasting 3D engine and OpenCV vision | 🧪 Internal prototype (not included in the public release) |
| **Official CLI** | `foq serve`, `foq demo`, `foq benchmark`, `foq inspect` commands | ✅ **Done** |
| **Ternary Model Lineup** | 27B / 8B / 4B / 1.7B ladder tested on the internal exam bench (business, traps, sensitive) with measured latencies | ✅ **Done** |
| **Internal Exam Bench** | 29 business cases + 10 cognitive traps + 6 sensitive-content cases, replayable by script | ✅ **Done** |
| **Decision LoRA Adapter** | Full QLoRA pipeline: data generation (templates + blind-verified external/27B teacher), training, GGUF conversion, hot `--lora` deployment | ✅ **Done** |
| **Multi-Model Calibration** | One RLCD profile per model (`--base-url`/`--output`), recalibration mandatory after any weight change | ✅ **Done** |
| **Deterministic Patches (neuro-symbolic)** | `foq/patches.py`: registry of known computable defects (KI-001 overshoot riddle), transparent correction (`patched_by`, raw answer preserved), disableable — 8B+LoRA+patches passes the full exam 10/10 at ~25 ms | ✅ **Done** |

---

## 🚀 Planned Future Work

> **Profitability order decided on 2026-09-19** (retained architecture: the honest
> 8B alone with `min_confidence` abstention — the 27B cascade remains an option for
> large GPUs, not a priority):
> 1. **RLCD recalibration on the large verified set** (~2,000 blind-validated examples) —
>    statistically solid T* temperature + threshold → accuracy curve to set a proven
>    `min_confidence` (~1 h).
> 2. **RLCD LoRA** — replace the one-hot loss with the Brier Score on soft targets and
>    retrain with the existing pipeline: the real step towards a "dedicated model".
> 3. **Standard public benchmark** — measure Foq on recognized datasets and publish the
>    raw results, even unfavorable ones: external credibility.
> 4. **Millisecond hunt** (short prompts, in-process bindings) — after 1 and 2;
>    that is speed, not quality.

### 1. ~~Reflex 8B → Judge 27B Cascade~~ — **abandonnée (décision produit 2026-09-19)**

*Le positionnement est un modèle léger unique qui fait tout, vite et en local. L'abstention `needs_review` couvre les cas douteux ; le 27B reste utilisable manuellement mais n'est plus une brique du produit.*
* **Current state**: the 8B answers in ~25 ms but still fails pure-reasoning riddles (9/10 hardcore); the 27B is perfect but 6 to 12 times slower. Abstention (`needs_review`) covers small machines without a 27B.
* **Goal**: for machines ≥ 16 GB, integrate the cascade natively into `system_one()` — 8B decision by default, automatic escalation to the 27B when calibrated confidence drops below the threshold. Both servers coexist in VRAM (verified).

### 2. In-Process Integration (Native Python Bindings)
* **Current state**: Foq talks to `llama-server.exe` over local HTTP requests (< 15 ms network overhead).
* **Goal**: bind the C++ `llama.cpp` library directly into the Python process via `ctypes` or native C++ bindings.
* **Measured prerequisite**: prefill dominates latency (~20 ms on 8B); bindings alone are not enough — combine shorter prompts, a smaller model and in-process execution to target < 5 ms.
* **Expected benefit**: eliminating the HTTP socket hop to bring total latency below the **5 millisecond** bar.

### 3. Dedicated RLCD LoRA Adapter Training
* **Current state**: the LoRA pipeline works (see above); calibration remains a post-hoc Temperature Scaling on a small validation set.
* **Immediate first step**: recalibrate T* on the ~2,000 blind-verified examples (the training set itself), then plot the threshold → accuracy curve of autonomous answers to set the production `min_confidence`.
* **Goal**: build a calibration corpus of several thousand examples and train an adapter optimized on the Brier loss (calibrated soft targets instead of one-hot).

### 4. Public Benchmark on Standard Datasets
* **Goal**: measure Foq on recognized public datasets (intent classification, injection detection, NLI) and publish the raw results for external credibility — beyond the current internal bench.

### 5. Integration as Reflex Router in `LocalCopilot`
* **Goal**: position Foq as a first-line sentinel in front of the machine's main conversational agent:
  * Assess in 15 ms whether a request needs system tools.
  * Filter context-injection attacks before waking the System 2 model.
