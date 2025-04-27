#!/usr/bin/env bash
set -euo pipefail
SAFE_TEMP=55
DATASET_JSON="/home/rise/models/scripts/python/exp0703/model/shuffled_squad.json"
OUTPUT_DIR="/home/rise/models/scripts/python/exp0703/results/single"
PY_SCRIPT="/home/rise/models/scripts/python/exp0703/model/model_single.py"
METRICS_SCRIPT="/home/rise/models/scripts/python/exp0703/metrics/metrics_single.sh"
MODEL_PATH="/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
# "/home/rise/Downloads/Llama-3.2-3B-Q4_0.gguf"

mkdir -p "$OUTPUT_DIR"

cool_down () {
  while :; do
    cur=$(vcgencmd measure_temp | awk -F= '{print $2+0}')
    (( $(echo "$cur > $SAFE_TEMP" | bc -l) )) && { echo "Cooling… $cur°C"; sleep 30; } || break
  done
}

total=$(jq '. | length' "$DATASET_JSON")
echo "== Running $total queries (one-by-one) =="

for ((idx=0; idx<total; idx++)); do
  cool_down
  ts=$(date +%Y%m%d_%H%M%S)

  CSV="$OUTPUT_DIR/metrics3b_${ts}.csv"
  JSON="$OUTPUT_DIR/output3b_${ts}.json"

  bash "$METRICS_SCRIPT" "$CSV" 1 &  MET_PID=$!
  python3 "$PY_SCRIPT" --index "$idx" \
                       --dataset "$DATASET_JSON" \
                       --model "$MODEL_PATH" \
                       --outfile "$JSON"      &  PY_PID=$!

  wait $PY_PID      # block until inference done
  kill $MET_PID     # stop sampling
  echo "✔︎ query $idx saved  →  $(basename "$CSV"), $(basename "$JSON")"
done
