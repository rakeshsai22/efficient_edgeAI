#!/usr/bin/env python3
import json
import time
import os
import subprocess
from llama_cpp import Llama
import psutil
from datetime import datetime 

# === Configuration ===
MODEL_PATH = "/home/rise/Downloads/Llama-3.2-3B-Q4_0.gguf"
# "/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
# 
# "/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
DATASET_PATH = "/home/rise/models/scripts/python/exp0703/model/boolq_multi_contexts.json"
# "/home/rise/models/scripts/python/exp0703/model/shuffled_squad.json"
# "/home/rise/models/scripts/python/exp0703/model/squad_val_100.json"
# RESULTS_DIR = "exp_results"
MAX_RUNTIME_OVERSHOOT = 0.10  # 10% acceptable latency increase
SAFE_TEMP_C = 77.0
DEFAULT_FREQ = 1500  # in MHz
DEFAULT_CORES = 4

# Define available configurations (cores, freq in MHz)
CORES_LIST = [4, 3, 2, 1]
FREQ_LIST = [1500, 1400, 1300, 1200, 1100, 1000, 900, 800, 700, 600]

# Utility to measure CPU temperature
def get_cpu_temp():
    try:
        return psutil.sensors_temperatures()["cpu_thermal"][0].current
    except:
        return None

# Set CPU frequency
def set_cpu_freq(freq_mhz):
    freq_khz = str(freq_mhz * 1000)
    for cpu in os.listdir("/sys/devices/system/cpu/"):
        if cpu.startswith("cpu") and cpu[3:].isdigit():
            path = f"/sys/devices/system/cpu/{cpu}/cpufreq"
            try:
                with open(f"{path}/scaling_max_freq", "w") as f:
                    f.write(freq_khz)
                with open(f"{path}/scaling_min_freq", "w") as f:
                    f.write(freq_khz)
            except:
                pass

# Set active core count (via taskset mask)
def set_core_affinity(pid, cores):
    mask = (1 << cores) - 1
    subprocess.run(["taskset", "-p", hex(mask), str(pid)], stdout=subprocess.DEVNULL)

# Surrogate model for latency and temp
def surrogate_runtime(K, freq_ghz, cores):
    return K * (30.0 / (freq_ghz * cores))  # Arbitrary scaling

def surrogate_temp(base_temp, K, freq_ghz, cores):
    return base_temp + K * (freq_ghz * cores) * 0.05

# Decision function
def select_config(K, ambient_temp):
    base_L = surrogate_runtime(K, 1.5, 4)
    for cores in CORES_LIST:
        for freq in FREQ_LIST:
            f_ghz = freq / 1000
            L = surrogate_runtime(K, f_ghz, cores)
            T = surrogate_temp(ambient_temp, K, f_ghz, cores)
            if T <= SAFE_TEMP_C and L <= base_L * (1 + MAX_RUNTIME_OVERSHOOT):
                return cores, freq, L, T
    return 2, 1000, base_L * 10, 85.0  # fallback

# Main test loop
def run_test():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    RESULTS_DIR = f"exp_results_{timestamp}"
    # os.makedirs(RESULTS_DIR, exist_ok=True)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(DATASET_PATH) as f:
        data = json.load(f)
        # [:40]

    llm = Llama(model_path=MODEL_PATH)

    for i, item in enumerate(data):
        text = item["context"] + " " + item["question"]
        K = (len(text.strip().split()) + 128) // 16
        ambient = get_cpu_temp() or 40.0
        cores, freq, L, T = select_config(K, ambient)

        print(f"→ Query {i+1}: K={K}, {cores} cores @ {freq} MHz | Est. L={L:.1f}s, T={T:.1f}°C")

        # Set hardware
        set_cpu_freq(freq)

        t0 = time.time()
        output = llm(f"Context: {item['context']}\nQuestion: {item['question']}\nAnswer:")#, max_tokens=128)
        elapsed = time.time() - t0

        result = {
            "question": item["question"],
            "response": output["choices"][0]["text"].strip(),
            "elapsed_time": elapsed,
            "config": {"cores": cores, "freq_mhz": freq},
            "temp_start": ambient,
            "temp_end": get_cpu_temp()
        }

        with open(os.path.join(RESULTS_DIR, f"q{i+1}_result.json"), "w") as f:
            json.dump(result, f, indent=2)

if __name__ == "__main__":
    run_test()
