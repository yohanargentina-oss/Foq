# Foq — Setup Contract for AI Agents (Claude, Codex, ZCode, local agents)

Read this before installing or running Foq. These facts are not suggestions.

1. **Model — Foq 8B, mandatory.** The decision model is
   `foq-reflex-8b-pq2_0.gguf` (**Foq 8B**, 2.2 GB — re-host of PrismML's
   Ternary Bonsai 8B, Apache 2.0, PQ2_0 format). Install it with:

   ```bash
   foq setup   # downloads to ~/.models/foq/, SHA-256 verified
   ```

   Do not download another GGUF, do not use the optional 27B, do not re-quantize.

2. **Runtime — Foq llama.cpp build, mandatory.** The weights use the ternary
   **PQ2_0** format (custom ggml tensor type). Only the **Foq runtime** — the
   llama.cpp fork with PQ2_0 kernels (PrismML-Eng/llama.cpp) — can load it.
   Get it from [Releases](https://github.com/yohanargentina-oss/Foq/releases)
   and unpack it to `~/.local/bin/foq-llama/`:

   - `foq-llama-windows-x64.zip` — Windows x64, CUDA 12.4, self-contained
   - `foq-llama-linux-x64.tar.gz` — Linux x64, CUDA 12.4 (NVIDIA driver ≥ 550)
   - `foq-llama-macos-arm64.tar.gz` — macOS Apple Silicon (Metal backend)
   - `foq-llama-macos-x64.tar.gz` — macOS Intel (CPU)
   - `foq-llama-apple-xcframework.zip` — iOS/iPadOS app integration (Xcode)

   **Official ggml-org llama.cpp builds CANNOT run this model.** They fail at
   load with an *unknown tensor type* error. Never install official llama.cpp
   to serve Foq weights, and never conclude the model is "corrupt" when an
   official build rejects it — it means the wrong build is being used.

3. **Start the server:**

   ```bash
   foq serve                 # or: start_foq_server.cmd / .sh  (port 8089)
   start_foq_8b_server.cmd   # or .sh                          (port 8090)
   ```

   The launchers prefer the Foq build in `~/.local/bin/foq-llama/` over any
   `llama-server` found in the PATH (an official build in the PATH cannot
   load PQ2_0).

4. **Verify:**

   ```bash
   foq demo                                        # interactive check
   foq inspect "test payload"                      # live WAF audit
   ```

   ```python
   from foq import FoqEngine
   assert FoqEngine().is_server_ready()            # http://127.0.0.1:8089
   ```

5. **Troubleshooting (map of known errors):**

   | Symptom | Cause | Fix |
   |---|---|---|
   | `unknown tensor type` / model load failure in llama-server | official (non-Foq) llama.cpp build | install the Foq build to `~/.local/bin/foq-llama/` |
   | `Modèle introuvable` / model file missing | setup not run | `foq setup` |
   | server not responding on 8089/8090 | launcher not started | `foq serve` or the `start_foq_*` scripts |

Usage examples for delegating decisions to Foq: the Quickstart section of
[README.md](README.md) and the primitives in `foq/schemas.py`.
