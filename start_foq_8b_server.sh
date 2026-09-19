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

# La build Foq (PQ2_0) est prioritaire sur le PATH : un llama.cpp officiel
# ne peut pas charger ce modèle.
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
    echo "[ERREUR] llama-server introuvable — LLAMA_SERVER, ~/.local/bin/foq-llama, PATH."
    echo "Le modèle Foq utilise le format PQ2_0 : il faut la build llama.cpp Foq"
    echo "https://github.com/yohanargentina-oss/Foq/releases"
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
