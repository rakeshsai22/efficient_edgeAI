import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
import json

base_dir = "/home/rise/models/scripts/python/exp0703/results/sweep/core"
all_dirs = sorted(glob.glob(os.path.join(base_dir, "q*_c*_*/")))

# Only keep the latest run for each (query_id, core_count)
latest_dirs = {}
for path in all_dirs:
    match = re.search(r"q(\d+)_c(\d+)_([0-9]{8}_[0-9]{6})", path)
    if not match:
        continue
    qid, core, timestamp = int(match.group(1)), int(match.group(2)), match.group(3)
    key = (qid, core)
    if key not in latest_dirs or timestamp > latest_dirs[key][1]:
        latest_dirs[key] = (path, timestamp)

avg_temp_data = {}
elapsed_time_data = {}

# Read data
for (qid, core), (path, _) in latest_dirs.items():
    csv_path = os.path.join(path, "metrics.csv")
    json_path = os.path.join(path, "output.json")

    if not os.path.isfile(csv_path) or not os.path.isfile(json_path):
        continue

    try:
        df = pd.read_csv(csv_path)
        if "CPU_Temperature" in df.columns:
            avg_temp = df["CPU_Temperature"].mean()
            avg_temp_data.setdefault(qid, {})[core] = avg_temp

        with open(json_path) as f:
            output = json.load(f)
        elapsed = output.get("elapsed_time")
        if elapsed is not None:
            elapsed_time_data.setdefault(qid, {})[core] = elapsed
    except Exception as e:
        print(f"Error processing {path}: {e}")

# Plot for each query
output_dir = "core_sweep_avgtemp_plots"
os.makedirs(output_dir, exist_ok=True)

for qid in sorted(avg_temp_data.keys()):
    cores = sorted(avg_temp_data[qid].keys())
    temps = [avg_temp_data[qid][c] for c in cores]
    times = [elapsed_time_data.get(qid, {}).get(c, None) for c in cores]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax1.plot(cores, temps, marker='o', color='tab:red')
    ax1.set_ylabel("Avg Temp (°C)")
    ax1.set_title(f"Query {qid}: Avg Temperature & Elapsed Time vs Core Count")
    ax1.grid(True)

    ax2.plot(cores, times, marker='o', color='tab:blue')
    ax2.set_xlabel("Number of CPU Cores")
    ax2.set_ylabel("Elapsed Time (s)")
    ax2.grid(True)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, f"query_{qid}_core_sweep_avgtemp.png"))
    plt.close()

print(f"Plots saved to {output_dir}/")
