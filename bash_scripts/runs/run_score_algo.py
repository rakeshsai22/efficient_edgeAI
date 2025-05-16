#!/usr/bin/env python3
import json, time, os, subprocess
from llama_cpp import Llama
import psutil
from datetime import datetime
import numpy as np
from pathlib import Path

# === Configuration ===
MODEL_PATH       = "/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
DATASET_PATH     = "/home/rise/models/scripts/python/exp0703/model/squad_val_100.json"
MAX_RUNTIME_OVERSHOOT = 0.10
SAFE_TEMP_C      = 77.0
DEFAULT_FREQ     = 1500
DEFAULT_CORES    = 4
DEFAULT_CTX      = 4096
TEST_SAMPLES     = 100    # ↦ only first 5 for quick test

# Surrogate models
def surrogate_runtime(K, freq_ghz, cores, ctx):
    return K * (30.0 / (freq_ghz * cores)) * (ctx / DEFAULT_CTX)

def surrogate_temp(base_temp, K, freq_ghz, cores, ctx):
    penalty = 1 + 0.02 * (ctx / DEFAULT_CTX)
    return base_temp + K * freq_ghz * cores * 0.05 * penalty

# Enumerate & score configs
def select_config(K, ambient):
    base_L = surrogate_runtime(K, 1.5, DEFAULT_CORES, DEFAULT_CTX)
    candidates = []
    for c in [4,3,2,1]:
      for f in [1500,1400,1300,1200,1100,1000,900,800,700,600]:
        for ctx in [DEFAULT_CTX,2048,1024]:
          L = surrogate_runtime(K, f/1000.0, c, ctx)
          T = surrogate_temp(ambient, K, f/1000.0, c, ctx)
          if T <= SAFE_TEMP_C and L <= base_L*(1+MAX_RUNTIME_OVERSHOOT):
            candidates.append((c,f,ctx,L,T))
    if not candidates:
      return 2,1000,1024,base_L*10,ambient+5.0

    Ls = np.array([x[3] for x in candidates])
    Ts = np.array([x[4] for x in candidates])
    Lmin, Lmax = Ls.min(),Ls.max()
    Tmin, Tmax = Ts.min(),Ts.max()

    best_score, best = float('inf'), None
    for c,f,ctx,L,T in candidates:
      nL = (L-Lmin)/(Lmax-Lmin) if Lmax>Lmin else 0
      nT = (T-Tmin)/(Tmax-Tmin) if Tmax>Tmin else 0
      score = 0.3*nL + 0.7*nT
      if score < best_score:
        best_score, best = score,(c,f,ctx,L,T)
    return best

# Hardware helpers
def get_cpu_temp():
    try: return psutil.sensors_temperatures()["cpu_thermal"][0].current
    except: return 40.0

def set_cpu_freq(mhz):
    khz = str(mhz*1000)
    for cpu in os.listdir("/sys/devices/system/cpu/"):
      if cpu.startswith("cpu") and cpu[3:].isdigit():
        base = f"/sys/devices/system/cpu/{cpu}/cpufreq"
        for fn in ("scaling_max_freq","scaling_min_freq"):
          try: open(f"{base}/{fn}","w").write(khz)
          except: pass

def set_core_affinity(pid, cores):
    mask = (1<<cores)-1
    subprocess.run(["taskset","-p",hex(mask),str(pid)],stdout=subprocess.DEVNULL)

# Main
def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"exp_balanced_{ts}")
    out_dir.mkdir(exist_ok=True)

    data = json.load(open(DATASET_PATH))
    llm = Llama(model_path=MODEL_PATH)

    for i,item in enumerate(data):
        if i>=TEST_SAMPLES: break
        ambient = get_cpu_temp()
        K = (len((item["context"]+item["question"]).split())+128)//16
        c,f,ctx,_,_ = select_config(K,ambient)

        print(f"Q{i+1}: c={c}, f={f}MHz, ctx={ctx}")
        set_cpu_freq(f)
        # llm = Llama(model_path=MODEL_PATH, n_ctx=ctx)
        pid = getattr(llm,"pid",os.getpid())
        set_core_affinity(pid, c)

        t0 = time.time()
        prompt = f"Context: {item['context']}\nQuestion: {item['question']}\nAnswer:"
        # out = llm(f"Context: {item['context']}\nQuestion: {item['question']}\nAnswer:")
        out = llm(prompt=prompt,max_tokens=ctx)
        elapsed = time.time()-t0
        end_temp = get_cpu_temp()

        res = {
          "question": item["question"],
          "response": out["choices"][0]["text"].strip(),
          "ground_truth": item.get("answer", "N/A"),
          "elapsed_time": elapsed,
          "config": {"cores":c,"freq_mhz":f,"n_ctx":ctx},
          "temp_start": ambient,
          "temp_end": end_temp
        }

        json.dump(res, open(out_dir/f"q{i+1}_result.json","w"), indent=2)

if __name__=="__main__":
    main()
