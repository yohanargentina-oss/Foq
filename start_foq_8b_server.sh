#!/usr/bin/env bash
set -e

echo "====================================================================="
echo "⚡ Foq 8B Reflex : serveur de décision rapide (modèle de référence Foq 8B)"
echo "🎯 Port dédié : http://127.0.0.1:8090"
echo "🧠 Optionnel : adaptateur LoRA décision via la variable LORA_PATH"
echo "====================================================================="

PORT="${PORT:-8090}"
MODEL_PATH="${MODEL_PATH:-${HOME}/.models/foq/foq-reflex-8b-pq2_0.gguf}"

if [ ! -f "$MODEL_PATH" ]; then
    echo "[ERREUR] Modèle introuvable : $MODEL_PATH"
    exit 1
fi

LLAMA_SERVER="${LLAMA_SERVER:-$(command -v llama-server || true)}"
if [ -z "$LLAMA_SERVER" ] && [ -x "${HOME}/.local/bin/foq-llama/llama-server" ]; then
    LLAMA_SERVER="${HOME}/.local/bin/foq-llama/llama-server"
fi
if [ -z "$LLAMA_SERVER" ]; then
    echo "[ERREUR] llama-server introuvable dans le PATH."
    exit 1
fi

LORA_ARGS=()
if [ -n "$LORA_PATH" ]; then
    if [ -f "$LORA_PATH" ]; then
        echo "[*] Adaptateur LoRA actif : $LORA_PATH"
        LORA_ARGS=(--lora "$LORA_PATH")
    else
        echo "[!] LORA_PATH défini mais introuvable : $LORA_PATH — démarrage sans adaptateur."
    fi
fi

echo "[*] Lancement de llama-server avec $MODEL_PATH sur le port $PORT..."
"$LLAMA_SERVER" \
    -m "$MODEL_PATH" \
    -ngl 99 \
    -c 4096 \
    -b 2048 \
    -ub 512 \
    -np 4 \
    --flash-attn on \
    --port "$PORT" \
    --host 127.0.0.1 \
    --alias foq-8b \
    "${LORA_ARGS[@]}"
