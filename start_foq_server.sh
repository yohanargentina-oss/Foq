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

if [ ! -f "$MODEL_PATH" ] && [ -f "./models/foq-juge-27b.gguf" ]; then
    MODEL_PATH="./models/foq-juge-27b.gguf"
elif [ ! -f "$MODEL_PATH" ] && [ -f "./foq-juge-27b.gguf" ]; then
    MODEL_PATH="./foq-juge-27b.gguf"
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "[ERREUR] Fichier modèle introuvable : $MODEL_PATH"
    echo "Veuillez télécharger le modèle GGUF et spécifier MODEL_PATH=/chemin/vers/modele.gguf"
    exit 1
fi

if [ -z "$LORA_PATH" ] && [ -f "$(dirname "$0")/../adapters/foq_decision_8b/foq_decision_8b.gguf" ]; then
  LORA_PATH="$(dirname "$0")/../adapters/foq_decision_8b/foq_decision_8b.gguf"
fi
LLAMA_SERVER="${LLAMA_SERVER:-$(command -v llama-server || true)}"
if [ -z "$LLAMA_SERVER" ]; then
    echo "[ERREUR] llama-server est introuvable dans le PATH."
    echo "Installez llama.cpp ou définissez LLAMA_SERVER=/chemin/vers/llama-server"
    exit 1
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
    --alias foq \
    --alias foq-system1

if [ -n "$LORA_PATH" ] && [ -f "$LORA_PATH" ]; then
    echo "[*] Adaptateur LoRA actif : $LORA_PATH"
    set -- "$@" --lora "$LORA_PATH"
fi
"$@"
