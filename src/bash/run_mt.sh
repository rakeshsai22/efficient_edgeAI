#!/bin/bash

SAFE_TEMP=55 
MAX_TOKENS_LIST=(70 85 104 115 128 142 157 174 214 237 263 292 324 360 400 441 490 544 604 671 746 828 921 1024 1758 1758 2172 2417 2686 2985 3317 3686 4096)
# 70 85 104 115 128 142 157 174 214 921 4096 3686 3317 2985 2686 2417
OUTPUT_DIR="/home/rise/models/scripts/python/gguf/results/32_3b/max_token_variation_30"
PYTHON_SCRIPT="/home/rise/models/scripts/python/gguf/scripts/model/model_mt.py"
METRICS_SCRIPT="/home/rise/models/scripts/python/gguf/scripts/metrics/metrics_latency.sh"

mkdir -p $OUTPUT_DIR

cleanup() {
    echo " Killing running scripts..."
    kill $METRICS_PID 2>/dev/null
    kill $PYTHON_PID 2>/dev/null
    echo " Cleanup complete."
}
trap cleanup EXIT

cool_down() {
    current_temp=$(vcgencmd measure_temp | egrep -o '[0-9]*\.[0-9]*')
    echo " CPU Temp: ${current_temp}°C"
    while (( $(echo "$current_temp > $SAFE_TEMP" | bc -l) )); do
        echo "Cooling CPU. Waiting for temp to drop below $SAFE_TEMP°C..."
        sleep 30
        current_temp=$(vcgencmd measure_temp | egrep -o '[0-9]*\.[0-9]*')
    done
    echo "CPU cooled to $current_temp°C."
}

for mt in "${MAX_TOKENS_LIST[@]}"; do
    echo "Starting experiment for max_tokens=${mt}"
    cool_down

    timestamp=$(date +"%Y%m%d_%H%M%S")
    METRICS_FILE="$OUTPUT_DIR/metrics_${mt}_max_tokens_$timestamp.csv"
    OUTPUT_FILE="$OUTPUT_DIR/llama2_output_${mt}_max_tokens_$timestamp.json"

    bash $METRICS_SCRIPT > "$METRICS_FILE" 2>&1 &
    METRICS_PID=$!
    python3 $PYTHON_SCRIPT --max_tokens $mt > "$OUTPUT_FILE" 2>&1 &
    PYTHON_PID=$!
    wait $PYTHON_PID
    kill $METRICS_PID

    echo " Run complete for max_tokens=${mt}. Results saved."
done

echo "All max_tokens variation experiments completed successfully!"
