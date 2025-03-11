import time
import json
import psutil
import argparse
from datasets import load_dataset
from llama_cpp import Llama

def get_cpu_metrics():
    try:
        temp = psutil.sensors_temperatures()["cpu_thermal"][0].current
        freq = psutil.cpu_freq().current
        return temp, freq
    except Exception as e:
        print(f"Error reading CPU metrics: {e}")
        return None, None

def load_model(model_path):
    print("Loading the model...")
    try:
        llm = Llama(model_path=model_path)
        print("Model Loaded Successfully")
        return llm
    except Exception as e:
        print(f"Error loading the model: {e}")
        return None

def run_inference(llm, question, context, max_tokens):
    temp_before, freq_before = get_cpu_metrics()
    start_time = time.time()

    try:
        prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
        output = llm(prompt, echo=False, max_tokens=max_tokens)
        elapsed_time = time.time() - start_time
        total_tokens = output.get('usage', {}).get('total_tokens', 0)
        completion_tokens = output.get('usage', {}).get('completion_tokens', 0)
        token_rate = total_tokens / elapsed_time if elapsed_time > 0 else 0
        temp_after, freq_after = get_cpu_metrics()
        generated_text = output['choices'][0]['text'].strip()

        # Output results
        result_data = {
            "question": question,
            "context": context,
            "elapsed_time": elapsed_time,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "token_rate": token_rate,
            "cpu_temp_before": temp_before,
            "cpu_temp_after": temp_after,
            "cpu_freq_before": freq_before,
            "cpu_freq_after": freq_after,
            "response": generated_text,
            "max_tokens": max_tokens
        }

        return result_data

    except Exception as e:
        print(f"Error during inference: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run inference with LLaMA model.")
    parser.add_argument("--max_tokens", type=int, required=True, help="Maximum number of tokens to generate.")
    args = parser.parse_args()

    MODEL_PATH = "/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
    llm = load_model(MODEL_PATH)

    # Load SQuAD dataset
    print("Loading SQuAD dataset...")
    squad_dataset = load_dataset("squad")["validation"]
    first_sample = squad_dataset[0]  # Get the first sample

    question = first_sample["question"]
    context = first_sample["context"]
    print(f"\n{'='*60}\nRunning inference on the first SQuAD sample\n{'='*60}")
    result = run_inference(llm, question, context, args.max_tokens)

    if result:
        # Save the result to a JSON file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"/home/rise/models/scripts/python/exp0703/results/MT/llama7b_output_{args.max_tokens}_max_tokens_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=4)
        print(f"Results saved to {output_file}")