import os
import glob
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set(style="whitegrid")

def collect_query_data(base_dir, param):
    data = []
    search_path = f"{base_dir}/{param}/q*_*/output.json"
    for json_path in glob.glob(search_path):
        try:
            with open(json_path) as f:
                j = json.load(f)

            parent_dir = os.path.basename(os.path.dirname(json_path))
            query_str = parent_dir.split('_')[0]
            query_id = int(query_str.replace("q", ""))

            metrics_path = json_path.replace("output.json", "metrics.csv")
            if not os.path.exists(metrics_path):
                continue
            df = pd.read_csv(metrics_path)

            temp_candidates = ["cpu_temp_C", "CPU_Temperature", "cpu_temp"]
            temp_col = next((col for col in temp_candidates if col in df.columns), None)
            if temp_col is None:
                continue

            avg_temp = df[temp_col].mean()

            param_value = None
            if param == "freq":
                param_value = j.get("cpu_freq_set")
            elif param == "core":
                param_value = j.get("cpu_cores_start")
            elif param == "ctx":
                param_value = j.get("n_ctx")
            if param_value is None:
                continue

            data.append({
                "query": query_id,
                "param_value": param_value,
                "latency": j.get("elapsed_time"),
                "avg_temp": avg_temp
            })

        except Exception as e:
            print(f"Skipping {json_path}: {e}")
    return pd.DataFrame(data)


def plot_safe_region(ax1, ax2, df_q, baseline_latency):
    min_val = df_q[df_q["avg_temp"] <= 77]["param_value"].min()
    max_val = df_q[df_q["latency"] <= 1.10 * baseline_latency]["param_value"].max()

    if pd.notna(min_val) and pd.notna(max_val) and min_val < max_val:
        ax1.axvspan(min_val, max_val, color='gray', alpha=0.2, label="Safe Region")
        ax1.axvline(min_val, linestyle='--', color='gray')
        ax1.axvline(max_val, linestyle='--', color='gray')
        ax2.axvline(min_val, linestyle='--', color='gray')
        ax2.axvline(max_val, linestyle='--', color='gray')
        return min_val, max_val
    return None, None


def composite_plot_per_query(query_id, df_freq, df_ctx, df_core, out_dir):
    fig, axs = plt.subplots(3, 1, figsize=(8, 12), sharex=False)
    param_info = [("freq", df_freq, 1500), ("ctx", df_ctx, 4096), ("core", df_core, 4)]
    colors = ['tab:blue', 'tab:red']

    all_handles = []
    all_labels = []

    for i, (param, df, baseline_val) in enumerate(param_info):
        df_q = df[df["query"] == query_id].sort_values("param_value")
        if df_q.empty:
            continue

        baseline_row = df_q[df_q["param_value"] == baseline_val]
        if baseline_row.empty:
            continue

        baseline_latency = baseline_row.iloc[0]["latency"]
        ax1 = axs[i]
        ax2 = ax1.twinx()

        sns.lineplot(x="param_value", y="latency", data=df_q, marker='o',
                     ax=ax1, color=colors[0], label="Latency (s)", errorbar=None)
        sns.lineplot(x="param_value", y="avg_temp", data=df_q, marker='o',
                     ax=ax2, color=colors[1], label="Avg Temp (°C)", errorbar=None)

        ax1.set_ylabel("Latency (s)")
        ax2.set_ylabel("Avg Temp (°C)")
        ax1.set_xlabel(param.upper())
        min_val, max_val = plot_safe_region(ax1, ax2, df_q, baseline_latency)

        #tradeoff points in safe region
        candidates = df_q[
            (df_q["latency"] <= 1.10 * baseline_latency) &
            (df_q["avg_temp"] <= 77)
        ]

        if not candidates.empty:
            best_temp = candidates.loc[candidates["avg_temp"].idxmin()]
            best_lat = candidates.loc[candidates["latency"].idxmin()]

            ax1.plot(best_temp["param_value"], best_temp["latency"],
                     marker='o', color='green', markersize=10, label="Best Temp", zorder=5)
            ax2.plot(best_temp["param_value"], best_temp["avg_temp"],
                     marker='o', color='green', markersize=10, zorder=5)

            ax1.plot(best_lat["param_value"], best_lat["latency"],
                     marker='o', color='blue', markersize=10, label="Best Latency", zorder=5)
            ax2.plot(best_lat["param_value"], best_lat["avg_temp"],
                     marker='o', color='blue', markersize=10, zorder=5)

        ax1.set_title(f"Query {query_id} — {param.upper()} Sweep")

        h1, l1 = ax1.get_legend_handles_labels()
        all_handles += h1
        all_labels += l1
    unique = dict(zip(all_labels, all_handles))
    fig.legend(unique.values(), unique.keys(),
               loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.02))

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, f"query_{query_id}_composite.png"))
    plt.close()


if __name__ == "__main__":
    BASE = "/home/rise/models/scripts/python/exp0703/results/sweep"
    OUT = "composite_plots"
    os.makedirs(OUT, exist_ok=True)

    df_freq = collect_query_data(BASE, "freq")
    df_ctx  = collect_query_data(BASE, "ctx")
    df_core = collect_query_data(BASE, "core")

    all_queries = sorted(set(df_freq["query"]) | set(df_ctx["query"]) | set(df_core["query"]))

    for qid in all_queries:
        composite_plot_per_query(
            query_id=qid,
            df_freq=df_freq,
            df_ctx=df_ctx,
            df_core=df_core,
            out_dir=OUT
        )
