#!/usr/bin/env bash
set -e

echo "====================================================================="
echo "⚡ Foq Engine : System 1 Decision Model (Foq 27B Ternary)"
echo "🚀 Moteur : llama.cpp"
echo "🎯 Port dédié : http://127.0.0.1:8089"
echo "🧠 Mode : Prise de décision instantanée (0 token texte, 1-pass logits)"
echo "====================================================================="

PORT="${PORT:-8089}"
MODEL_PATH="${MODEL_PATH:-${HOME}/.models/foq/foq-reflex-8b-pq2_0.gguf}"

# Foq 8B est LE modèle de référence obligatoire — pas de repli implicite.
if [ ! -f "$MODEL_PATH" ] && [ -f "./models/foq-reflex-8b-pq2_0.gguf" ]; then
    MODEL_PATH="./models/foq-reflex-8b-pq2_0.gguf"
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "[ERREUR] Fichier modèle introuvable : $MODEL_PATH"
    echo "Installez Foq 8B avec : foq setup"
    exit 1
fi

if [ -z "$LORA_PATH" ] && [ -f "$(dirname "$0")/../adapters/foq_decision_8b/foq_decision_8b.gguf" ]; then
  LORA_PATH="$(dirname "$0")/../adapters/foq_decision_8b/foq_decision_8b.gguf"
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
if [ -n "$LORA_PATH" ] && [ -f "$LORA_PATH" ]; then
    echo "[*] Adaptateur LoRA actif : $LORA_PATH"
    LORA_ARGS=(--lora "$LORA_PATH")
fi

echo "[*] Lancement de llama-server avec $MODEL_PATH sur le port $PORT..."
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
