import time
import json
import subprocess
import psutil
import joblib
import os

# === CONFIG ===
OUTPUT_FILE = "/home/rise/models/scripts/python/exp0703/results/shuffled/your_output_file.json"  # Update this
MODEL_PATH = "cpu_predictor.pkl"  # Trained model path
TEMP_SENSOR = "/sys/class/thermal/thermal_zone0/temp"
PREDICTION_INTERVAL = 1.0  # seconds between predictions

# === FREQUENCY CONTROL ===
FREQ_HIGH = 1500  # in MHz
FREQ_LOW = 1000
CORE_FULL = 4
CORE_REDUCED = 2

# === LOAD MODEL ===
try:
    predictor = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Failed to load model: {e}")
    exit(1)

# === UTILITY FUNCTIONS ===
def get_cpu_temp():
    try:
        with open(TEMP_SENSOR, 'r') as f:
            return int(f.read()) / 1000.0
    except:
        return 0.0

def set_frequency(freq):
    for i in range(psutil.cpu_count()):
        subprocess.run(["cpufreq-set", "-c", str(i), "-u", f"{freq}MHz", "-d", f"{freq}MHz"])

def set_cores(n_cores):
    total = psutil.cpu_count()
    for i in range(1, total):
        online_file = f"/sys/devices/system/cpu/cpu{i}/online"
        if os.path.exists(online_file):
            val = '1' if i < n_cores else '0'
            try:
                with open(online_file, 'w') as f:
                    f.write(val)
            except:
                continue

def parse_features(line):
    # Dummy logic: extract from llama.cpp log
    prefix_hit = int(line.split("Llama.generate: ")[1].split()[0]) if "prefix-match" in line else 0
    position = int(line.split("ctx ")[1].split()[0]) if "ctx" in line else 0
    prompt_length = position  # crude fallback
    token_time = 0.025  # placeholder, update if known
    temperature = get_cpu_temp()
    freq = psutil.cpu_freq().current
    cores = psutil.cpu_count(logical=False)
    return [token_time, position, prompt_length, prefix_hit, temperature, freq, cores]

# === MAIN MONITOR LOOP ===
with open(OUTPUT_FILE, 'r') as f:
    f.seek(0, 2)  # move to end for tailing
    while True:
        line = f.readline()
        if not line:
            time.sleep(PREDICTION_INTERVAL)
            continue

        if "prefix-match" in line:
            try:
                features = parse_features(line)
                prediction = predictor.predict([features])[0]  # predicted token latency
                temp = features[4]

                print(f"[INFO] Predicted latency: {prediction:.3f}s | Temp: {temp}C")

                # Decision logic
                if prediction > 0.045 or temp > 75:
                    print("[CONTROL] High load predicted. Lowering frequency and cores.")
                    set_frequency(FREQ_LOW)
                    set_cores(CORE_REDUCED)
                elif prediction < 0.035 and temp < 70:
                    print("[CONTROL] Load is light. Restoring full performance.")
                    set_frequency(FREQ_HIGH)
                    set_cores(CORE_FULL)

            except Exception as e:
                print(f"[ERROR] Failed to parse or predict: {e}")
                continue
