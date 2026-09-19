# 📦 Reference Models (technical note)

Foq is a **model-agnostic engine**: it works with any GGUF model served by
`llama-server` (llama.cpp) and exposes the same API regardless of model family.

Reference configurations used for the public benchmarks in the README:

| Config | Weights | Format | License |
|---|---|---|---|
| `foq-reflex-8b-pq2_0.gguf` | 2.2 GB | ternary PQ2_0 (2.13 bpw) | Apache 2.0 |
| `foq-judge-27b-pq2_0.gguf` | 7.2 GB | ternary PQ2_0 (2.13 bpw) | Apache 2.0 |

**Foq 8B is the required reference model**: `foq setup` installs exactly this
file (SHA-256 pinned). The 27B is an optional larger configuration, not a
substitute.

**Provenance**: the reference weights are ternary-quantized GGUF files derived
from Apache 2.0 open-weight families (see [THIRD-PARTY-LICENSES.md](../THIRD-PARTY-LICENSES.md)).
Foq re-hosts its verified reference copies; nothing is downloaded from third-party
model repositories. Every user places the files in `~/.models/foq/`
(see `start_foq_server.*` for the expected paths).

**Runtime**: PQ2_0 is a Foq-specific ternary format (custom ggml tensor type).
It requires the **Foq build of llama.cpp** (`llama-server`) published on
[Releases](https://github.com/yohanargentina-oss/Foq/releases) — official
ggml-org builds cannot load these files (`unknown tensor type`). Unpack the
build to `~/.local/bin/foq-llama/`; the Foq launchers pick it up automatically.

**LoRA adapter** (`adapters/`): trained locally via
[docs/FINETUNING.md](FINETUNING.md) on generated and verified data; it plugs
onto the reference model without modifying its weights. Not distributed with
the repository.

*This page exists for Apache 2.0 license compliance (notice retention) and
benchmark reproducibility. Foq stays vendor-independent: swapping models is a
one-line configuration change.*
