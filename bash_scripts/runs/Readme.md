# Dynamic CPU Frequency Scaling for LLM Inference on Raspberry Pi

This repository enables **predictive CPU frequency and core count control** during **quantized LLM inference** (e.g., with `llama.cpp`) on resource-constrained devices like the Raspberry Pi. It helps prevent **thermal throttling** and maintains **token generation performance** by monitoring logs and using a trained model.

## Features

- Predicts token latency based on runtime signals:
  - Context position
  - Prefix-match hits
  - CPU temperature
  - Frequency and core status
- Dynamically adjusts:
  - **CPU frequency** (e.g., 1500 MHz ↔ 1000 MHz)
  - **Active CPU cores** (e.g., 4 ↔ 2)
- Tailored for real-time inference logs (e.g., `llama.cpp`)
- Lightweight, runs entirely on-device

---

## How It Works

1. A small regression model is trained to predict token latency based on runtime features.
2. During inference, the script reads inference logs and makes real-time predictions.
3. Based on the prediction and CPU temperature, it decides to **scale down** or **restore** performance levels.

---

## Requirements

- Python 3.7+
- `joblib`, `psutil`, `scikit-learn`:
  ```bash
  pip install joblib psutil scikit-learn
