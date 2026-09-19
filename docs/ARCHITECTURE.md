# 🏗️ Detailed Technical Architecture of Foq

This document details the internal architecture, hardware behavior and design choices of the **Foq** System 1 decision engine.

---

## 1. Kahneman's Dichotomy Applied to AI

Daniel Kahneman modeled human cognition along two operating modes:
* **System 1**: fast, automatic, reflexive, with no conscious effort or inner monologue.
* **System 2**: slow, analytical, sequential, requiring step-by-step deliberation.

Classic LLM architectures (GPT-4, Claude, standard Llama) operate exclusively in System 2 mode: even to answer a simple binary question (*"Is this spam?"*), the model generates text autoregressively, token after token.

| Characteristic | Traditional Generative LLM (System 2) | Foq (System 1) |
|---|---|---|
| **Execution mode** | Autoregressive decoding loop ($N$ passes) | Single feed-forward inference ($1$ pass) |
| **Tokens generated** | 20 to 500 tokens of prose | 0 written text tokens (or 1 target token) |
| **Output produced** | Unconstrained free text | Strict types (`bool`, `enum`, continuous score, Pydantic) |
| **Average latency** | 1,000 ms to 5,000 ms | 40 ms to 150 ms |
| **Network complexity** | $O(N)$ neural network passes | $O(1)$ neural network pass |
| **Hallucination risk** | High (syntax, rambling, evasion) | None (distribution constraint or GBNF grammar) |

---

## 2. Autoregression Short-Circuit & Logit Extraction

In a conversational LLM, producing the sentence *"Yes, this message is urgent"* requires:
1. Encoding the prompt (`prefill`).
2. Computing token 1 $\rightarrow$ feeding it back into the context.
3. Computing token 2 $\rightarrow$ feeding it back into the context.
4. Repeating $N$ times until the `<|im_end|>` token.

In **Foq**, the decoding loop is **entirely short-circuited**:
```
[ User Context + Options [A], [B], [C] ]
                      │
                      ▼ (single parallel feed-forward pass / prefill)
     [ Foq 8B Ternary Neural Network ]
                      │
                      ▼
     [ First output token logits ]
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
 Logprob('A')                Logprob('B')
        │                           │
        └─────────────┬─────────────┘
                      ▼
          [ Temperature Scaling T* ]
                      ▼
        Calibrated RLCD Probabilities
```

### Inference Parameters
On every call to `llama-server.exe`, Foq enforces the following parameters:
* `n_predict: 1`: stop immediately after the first evaluated token.
* `n_probs: 25`: extract the top 25 logprobs to cover all target letters (`A`, `B`, `C`...).
* `temperature: 0.0`: absolute determinism at the raw logit level.
* `cache_prompt: True`: KV-caches the recurring context to minimize prefill time across successive requests.

---

## 3. Hardware Infrastructure & the Foq 8B Model

Foq builds on a software and hardware stack optimized for NVIDIA GPUs:

* **Model**: `foq-reflex-8b-pq2_0.gguf` — **Foq 8B, the required reference
  decision model** (installed by `foq setup`).
* **PQ2_0 Ternary Quantization**: extreme 2-bit-per-weight compression. This quantization preserves the latent-space structure required for classification while shrinking the footprint to **2.2 GB** (~3 GB VRAM with KV-cache), enabling ultra-fast execution on an NVIDIA RTX 4080 / 4090.
* **Execution Engine**: the **Foq build of llama.cpp** (`llama-server`, PQ2_0
  tensor support — official ggml-org builds cannot load the model) with native **Flash Attention**.
* **Full GPU Offload (`-ngl 99`)**: the entire stack of model layers resides in GPU video memory.
* **Multi-Slot Architecture (`-np 4`)**: the server manages 4 independent concurrent inference slots, processing 4 questions in parallel without a bottleneck.

---

## 4. Prompt Security & ChatML Neutralization

To prevent any prompt manipulation (*prompt injection*, role evasion or schema tampering), Foq applies a rigorous prompt format:

1. **Strict sanitization**: all control tags (`<|im_start|>`, `<|im_end|>`, `<think>`, `</think>`) are systematically stripped from the input text.
2. **Passive `<donnees>` encapsulation**: the context to analyze is isolated inside a passive XML tag. The system instructions explicitly tell the model that this content is passive and never contains executable instructions. (The runtime prompt template uses the French word for "data" as the tag name.)
3. **Forced priming**: the assistant prompt is pre-filled with `Réponse : [` (French for "Answer: [") to force the network to emit the chosen option letter directly.

---

## 5. Concurrency: Sync vs Async

Foq offers two ways to query the model:

### Synchronous Mode (`ThreadPoolExecutor`)
Used by `engine.system_one()` and `engine.decide_multi()`. Distributes the questions of a dictionary over a thread pool (4 workers by default), leveraging the 4 inference slots configured on the server (`-np 4`).

### Native Asynchronous Mode (`asyncio.gather`)
Used by `engine.system_one_async()`, `engine.extract_async()` and `engine.decide_async()`. Relies on non-blocking asynchronous HTTP requests (`httpx.AsyncClient`). Recommended for all FastAPI microservices, concurrent agents and automation servers.

---

## 6. Subsystem Architecture

### 6.1 AI WAF Firewall (`foq.security`)
The `FoqSecurityGuard` module classifies text requests in ~100 ms into 3 states:
* `CLEAN`: harmless request.
* `PROMPT_INJECTION`: attempt to subvert or evade instructions.
* `MALICIOUS_PAYLOAD`: SQL injection, shell execution attempt, malicious code.

The ASGI middleware intercepts web requests upstream of the application routes and returns an immediate `HTTP 403 Forbidden` without waking the downstream generative models.

### 6.2 Browser Agent & DOM Pruner (`foq.browser`)
Traditional LLM web navigation is often slowed down by massive DOMs (tens of thousands of tokens).
* `DOMPruner` injects a fast JavaScript script into the Playwright page to keep only the visible interactive components (forms, content links, buttons) and summarizes them into a compact textual format of **200 to 400 tokens**.
* `FoqEngine` selects the action in a **single pass** (~300 ms per step), delivering an automation rate 10 times higher than conventional web agents.
