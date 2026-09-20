#!/usr/bin/env bash
set -e

echo "====================================================================="
echo "⚡ Foq Engine : System 1 Decision Model (Foq 8B Ternary PQ2_0)"
echo "🚀 Runtime : Foq llama.cpp (PQ2_0 kernels)"
echo "🎯 Port    : http://127.0.0.1:8089"
echo "🧠 Mode    : Instant typed decision (0 tokens generated, 1-pass logits)"
echo "====================================================================="

PORT="${PORT:-8089}"
MODEL_PATH="${MODEL_PATH:-${HOME}/.models/foq/foq-reflex-8b-pq2_0.gguf}"

if [ ! -f "$MODEL_PATH" ] && [ -f "./models/foq-reflex-8b-pq2_0.gguf" ]; then
    MODEL_PATH="./models/foq-reflex-8b-pq2_0.gguf"
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "[ERROR] Model file not found: $MODEL_PATH"
    echo "Install Foq 8B with: foq setup"
    exit 1
fi

# Look for custom llama-server with PQ2_0 support
LLAMA_SERVER="${LLAMA_SERVER:-}"
if [ -z "$LLAMA_SERVER" ]; then
    for _cand in "${HOME}/.local/bin/foq-llama/llama-server.exe" "${HOME}/.local/bin/foq-llama/llama-server"; do
        if [ -x "$_cand" ]; then LLAMA_SERVER="$_cand"; break; fi
    done
fi
if [ -z "$LLAMA_SERVER" ]; then
    LLAMA_SERVER="$(command -v llama-server || command -v llama-server.exe || true)"
fi
if [ -z "$LLAMA_SERVER" ]; then
    echo "[ERROR] llama-server not found (checked LLAMA_SERVER, ~/.local/bin/foq-llama, PATH)."
    echo "The Foq model requires the PQ2_0 llama.cpp build:"
    echo "https://github.com/yohanargentina-oss/Foq/releases"
    exit 1
fi

LORA_ARGS=()
if [ -n "$LORA_PATH" ] && [ -f "$LORA_PATH" ]; then
    echo "[*] Active LoRA adapter: $LORA_PATH"
    LORA_ARGS=(--lora "$LORA_PATH")
fi

echo "[*] Starting llama-server with $MODEL_PATH on port $PORT..."
exec "$LLAMA_SERVER" \
    -m "$MODEL_PATH" \
    -ngl 99 \
    -c 4096 \
    -b 2048 \
    -ub 512 \
    -np 4 \
    --flash-attn on \
    --port "$PORT" \
    --host 127.0.0.1 \
    --alias foq \
    --alias foq-system1 \
    "${LORA_ARGS[@]}"
