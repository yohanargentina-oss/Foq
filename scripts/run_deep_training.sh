#!/usr/bin/env bash
# Chaîne d'entraînement approfondi du 8B (génération de données → entraînement 2h+ → conversion → relance 27B)
set -u
cd "$(dirname "$0")/.."
LOG=training_deep.log
PY=py
VENV_PY=.venv-train/Scripts/python
LLAMA="$HOME/.local/bin/foq-llama/llama-server.exe"
MODEL_27B="$HOME/.models/foq/foq-juge-27b.gguf"
EXTERNAL="data/_external/dataset_avance.jsonl"

echo "[$(date +%H:%M:%S)] === PHASE 1 : génération de données (700 pièges par le 27B professeur) ===" >> "$LOG"
PYTHONUNBUFFERED=1 $PY scripts/generate_training_data.py --count-business 1400 --count-riddles 700 >> "$LOG" 2>&1

echo "[$(date +%H:%M:%S)] === PHASE 2 : fusion + re-vérification des 300 items externes ===" >> "$LOG"
PYTHONUNBUFFERED=1 $PY scripts/import_external_riddles.py "$EXTERNAL" --verify-url http://127.0.0.1:8089 >> "$LOG" 2>&1

echo "[$(date +%H:%M:%S)] === PHASE 3 : arrêt du serveur 27B (libération GPU) ===" >> "$LOG"
PID=$(netstat -ano | grep ":8089" | grep "LISTENING" | head -1 | awk '{print $NF}')
if [ -n "$PID" ]; then taskkill //PID "$PID" //F >> "$LOG" 2>&1; fi
sleep 5

echo "[$(date +%H:%M:%S)] === PHASE 4 : entraînement approfondi (rang 32, 12 époques, ~2h) ===" >> "$LOG"
PYTHONUNBUFFERED=1 $VENV_PY scripts/train_lora_8b.py --epochs 12 --rank 32 --lr 6e-5 >> "$LOG" 2>&1
echo "[$(date +%H:%M:%S)] TRAIN_EXIT=$?" >> "$LOG"

echo "[$(date +%H:%M:%S)] === PHASE 5 : conversion GGUF de l'adaptateur ===" >> "$LOG"
$VENV_PY scripts/convert_lora_to_gguf.py adapters/foq_decision_8b \
  --base "$HOME/.models/foq/foq-reflex-8b-unpacked" \
  --outfile adapters/foq_decision_8b/foq_decision_8b.gguf >> "$LOG" 2>&1
echo "[$(date +%H:%M:%S)] CONVERT_EXIT=$?" >> "$LOG"

echo "[$(date +%H:%M:%S)] === PHASE 6 : relance du serveur 27B sur 8089 ===" >> "$LOG"
"$LLAMA" -m "$MODEL_27B" -ngl 99 -c 4096 -b 2048 -ub 512 -np 4 --flash-attn on \
  --port 8089 --host 127.0.0.1 --alias foq --alias foq-system1 >> "$LOG" 2>&1
