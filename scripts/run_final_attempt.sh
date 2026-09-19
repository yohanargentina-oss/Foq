#!/usr/bin/env bash
# Tentative finale ciblée : mega-jeu externe (2500) → vérification juge → entraînement → examen
set -u
cd "$(dirname "$0")/.."
LOG=training_final.log
PY=py
VENV_PY=.venv-train/Scripts/python
LLAMA="$HOME/.local/bin/foq-llama/llama-server.exe"
MODEL_27B="$HOME/.models/foq/foq-juge-27b.gguf"
MODEL_8B="$HOME/.models/foq/foq-reflex-8b-pq2_0.gguf"
ADAPTER="adapters/foq_decision_8b/foq_decision_8b.gguf"

echo "[$(date +%H:%M:%S)] === PHASE 1 : fusion + dédoublonnage des 13 fichiers (2500 items) ===" >> "$LOG"
$PY - <<'PYEOF' >> "$LOG" 2>&1
import json, hashlib, glob, os
os.makedirs("data", exist_ok=True)
seen, kept = set(), []
for path in sorted(glob.glob(r"data/_mega_raw/files/*.jsonl")):
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        h = hashlib.md5((d["contexte"] + "|" + d["question"]).encode("utf-8")).hexdigest()
        if h in seen: continue
        seen.add(h)
        kept.append(d)
with open(r"data/_mega_merged.jsonl", "w", encoding="utf-8") as f:
    for d in kept:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
print(f"fusion : {len(kept)} items uniques conservés")
PYEOF

echo "[$(date +%H:%M:%S)] === PHASE 2 : vérification à l'aveugle par le juge 27B ===" >> "$LOG"
PYTHONUNBUFFERED=1 $PY scripts/import_external_riddles.py data/_mega_merged.jsonl --verify-url http://127.0.0.1:8089 >> "$LOG" 2>&1

echo "[$(date +%H:%M:%S)] === PHASE 3 : arrêt du 27B (libération GPU) ===" >> "$LOG"
PID=$(netstat -ano | grep ":8089" | grep "LISTENING" | head -1 | awk '{print $NF}')
if [ -n "$PID" ]; then taskkill //PID "$PID" //F >> "$LOG" 2>&1; fi
sleep 5

echo "[$(date +%H:%M:%S)] === PHASE 4 : entraînement final (rang 16, 3 époques) ===" >> "$LOG"
PYTHONUNBUFFERED=1 $VENV_PY scripts/train_lora_8b.py --epochs 3 --rank 16 --lr 1e-4 >> "$LOG" 2>&1
echo "[$(date +%H:%M:%S)] TRAIN_EXIT=$?" >> "$LOG"

echo "[$(date +%H:%M:%S)] === PHASE 5 : conversion GGUF ===" >> "$LOG"
$VENV_PY scripts/convert_lora_to_gguf.py adapters/foq_decision_8b \
  --base "$HOME/.models/foq/foq-reflex-8b-unpacked" \
  --outfile "$ADAPTER" >> "$LOG" 2>&1
echo "[$(date +%H:%M:%S)] CONVERT_EXIT=$?" >> "$LOG"

echo "[$(date +%H:%M:%S)] === PHASE 6 : relance du 27B + serveur 8B adapté sur 8090 ===" >> "$LOG"
"$LLAMA" -m "$MODEL_27B" -ngl 99 -c 4096 -b 2048 -ub 512 -np 4 --flash-attn on \
  --port 8089 --host 127.0.0.1 --alias foq --alias foq-system1 >> "$LOG" 2>&1 &
sleep 25
"$LLAMA" -m "$MODEL_8B" --lora "$(pwd)/$ADAPTER" -ngl 99 -c 4096 -b 2048 -ub 512 -np 4 --flash-attn on \
  --port 8090 --host 127.0.0.1 --alias foq-8b-lora >> "$LOG" 2>&1 &
sleep 20

echo "[$(date +%H:%M:%S)] === PHASE 7 : examen complet ===" >> "$LOG"
for i in $(seq 1 30); do
  r=$(curl -s -m 2 http://127.0.0.1:8090/health 2>/dev/null)
  if [ "$r" = '{"status":"ok"}' ]; then break; fi; sleep 2
done
FOQ_BASE_URL=http://127.0.0.1:8090 $PY scripts/precision_benchmark.py >> "$LOG" 2>&1
FOQ_BASE_URL=http://127.0.0.1:8090 $PY scripts/hardcore_benchmark.py >> "$LOG" 2>&1
$PY scripts/run_calibration.py --base-url http://127.0.0.1:8090 --output calibration_profile_8b_lora.json --alias foq-8b-lora >> "$LOG" 2>&1
echo "[$(date +%H:%M:%S)] === TERMINÉ ===" >> "$LOG"
