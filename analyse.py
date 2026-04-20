import csv
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def clean_cell(value):
    return value.strip().strip('"')


def parse_numeric_list(cell):
    text = clean_cell(cell)
    if not text or text == "[]":
        return []
    text = text.strip("[]").strip()
    if not text:
        return []
    return [float(x) for x in text.split()]


def label_bars(ax, values, fmt="{:.0f}"):
    for bar, val in zip(ax.patches, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            fmt.format(val),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )


filepath = "simulation_coaching-rate-vs-revenue-spreadsheet.csv"
with open(filepath, "r", encoding="utf-8-sig") as f:
    rows = list(csv.reader(f))

# Locate key rows in a schema-tolerant way.
all_run_data_idx = None
run_number_idx = None
for i, row in enumerate(rows):
    if not row:
        continue
    tag = clean_cell(row[0])
    if tag == "[all run data]":
        all_run_data_idx = i
    if tag == "[run number]":
        run_number_idx = i

if all_run_data_idx is None:
    raise ValueError("Could not find [all run data] section")

headers_raw = [clean_cell(x) for x in rows[all_run_data_idx][1:]]
if not headers_raw:
    raise ValueError("Could not parse reporter headers from [all run data]")

safe_names = {
    "[step]": "step",
    "count turtles": "count_turtles",
    "revenue-mean": "revenue_mean",
    "skill-mean": "skill_mean",
    "turnover-rate": "turnover_rate",
    "sorted-skill": "sorted_skill",
    "sorted-coaching": "sorted_coaching",
}
cols_per_run = [
    safe_names.get(h, h.replace("-", "_").replace(" ", "_")) for h in headers_raw
]
n_cols = len(cols_per_run)

if run_number_idx is not None:
    run_numbers = [x for x in rows[run_number_idx][1:] if clean_cell(x)]
    n_runs = max(1, len(run_numbers) // n_cols)
else:
    n_runs = 1

print(f"Found {n_runs} runs, {n_cols} columns per run")

records = []
for row in rows[all_run_data_idx + 1 :]:
    if len(row) < 2 or clean_cell(row[1]) == "":
        continue

    values = row[1:]
    if len(values) < n_cols:
        continue

    for run_idx in range(n_runs):
        offset = run_idx * n_cols
        run_vals = values[offset : offset + n_cols]
        if len(run_vals) < n_cols:
            continue

        rec = {"run": run_idx + 1}
        for col, val in zip(cols_per_run, run_vals):
            text = clean_cell(val)
            if col in {"sorted_skill", "sorted_coaching"}:
                rec[col] = parse_numeric_list(text)
            else:
                try:
                    rec[col] = float(text)
                except ValueError:
                    rec[col] = np.nan
        records.append(rec)

df = pd.DataFrame(records)
if df.empty:
    raise ValueError("No run data rows were parsed from CSV")

df["year"] = df["step"] / 100
print(f"Parsed {len(df)} rows, steps 0-{int(df['step'].max())}")

steady_state = df[df["step"] >= df["step"].max() * 0.8].copy()
print("\n-- Steady-state summary (last 20% of ticks) --")
print(
    steady_state[["revenue_mean", "skill_mean", "turnover_rate"]]
    .agg(["mean", "std", "min", "max"])
    .round(3)
    .to_string()
)

# Build coaching-level summary from list reporters in each row.
long_rows = []
for _, r in steady_state.iterrows():
    skills = r.get("sorted_skill", []) or []
    coaching = r.get("sorted_coaching", []) or []
    n = min(len(skills), len(coaching))
    for i in range(n):
        long_rows.append(
            {
                "run": r["run"],
                "step": r["step"],
                "coaching_rate": int(coaching[i]),
                "agent_value": float(skills[i]),
            }
        )

if long_rows:
    ldf = pd.DataFrame(long_rows)
    coaching_summary = (
        ldf.groupby("coaching_rate", as_index=False)["agent_value"]
        .agg(mean_agent_value="mean", std_agent_value="std", n="count")
        .sort_values("coaching_rate")
    )
else:
    ldf = pd.DataFrame(columns=["run", "step", "coaching_rate", "agent_value"])
    coaching_summary = pd.DataFrame(
        columns=["coaching_rate", "mean_agent_value", "std_agent_value", "n"]
    )

if not coaching_summary.empty:
    print("\n-- Coaching-level summary from [sorted-skill]/[sorted-coaching] --")
    print(coaching_summary.round(3).to_string(index=False))

colors = plt.cm.viridis(np.linspace(0.1, 0.9, max(3, len(coaching_summary))))
sample_every = max(1, int(df["step"].max() / 300))
sampled = df[df["step"] % sample_every == 0].copy()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(
    "Coaching Model Analysis (Updated CSV Schema)", fontsize=15, fontweight="bold"
)

ax = axes[0, 0]
ax.plot(sampled["year"], sampled["revenue_mean"], color="#2a9d8f", linewidth=1.4)
ax.set_xlabel("Year")
ax.set_ylabel("Revenue Mean")
ax.set_title("Revenue Mean Over Time")

ax = axes[0, 1]
ax.plot(sampled["year"], sampled["skill_mean"], color="#e76f51", linewidth=1.4)
ax.set_xlabel("Year")
ax.set_ylabel("Skill Mean")
ax.set_title("Skill Mean Over Time")

ax = axes[1, 0]
ax.plot(sampled["year"], sampled["turnover_rate"], color="#264653", linewidth=1.2)
ax.set_xlabel("Year")
ax.set_ylabel("Turnover Rate")
ax.set_title("Turnover Rate Over Time")

ax = axes[1, 1]
if not coaching_summary.empty:
    ax.bar(
        coaching_summary["coaching_rate"],
        coaching_summary["mean_agent_value"],
        yerr=coaching_summary["std_agent_value"],
        capsize=3,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )
    ax.set_xticks(coaching_summary["coaching_rate"].tolist())
    label_bars(ax, coaching_summary["mean_agent_value"], fmt="{:.0f}")
ax.set_xlabel("Coaching Rate")
ax.set_ylabel("Mean Agent Value")
ax.set_title("Steady-State Agent Value by Coaching Rate")

plt.tight_layout()
os.makedirs("output", exist_ok=True)
plot1 = os.path.join("output", "coaching_analysis_long.png")
plt.savefig(plot1, dpi=150, bbox_inches="tight")
print(f"\nSaved: {plot1}")

fig2, ax2 = plt.subplots(figsize=(10, 5))
if not coaching_summary.empty:
    ax2.bar(
        coaching_summary["coaching_rate"],
        coaching_summary["n"],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )
    ax2.set_xticks(coaching_summary["coaching_rate"].tolist())
    label_bars(ax2, coaching_summary["n"], fmt="{:.0f}")
ax2.set_xlabel("Coaching Rate")
ax2.set_ylabel("Sample Count (steady state)")
ax2.set_title("Data Coverage by Coaching Rate")
plt.tight_layout()
plot2 = os.path.join("output", "coaching_efficiency_long.png")
plt.savefig(plot2, dpi=150, bbox_inches="tight")
print(f"Saved: {plot2}")

# Company-level comparison: coaching rate vs revenue distribution.
fig3, ax3 = plt.subplots(figsize=(12, 6))
if not ldf.empty:
    rates = sorted(ldf["coaching_rate"].dropna().astype(int).unique().tolist())
    box_data = [ldf.loc[ldf["coaching_rate"] == r, "agent_value"].values for r in rates]
    bp = ax3.boxplot(
        box_data,
        positions=rates,
        widths=0.6,
        patch_artist=True,
        showfliers=False,
    )
    for patch in bp["boxes"]:
        patch.set_facecolor("#90caf9")
        patch.set_edgecolor("#1f77b4")
    for median in bp["medians"]:
        median.set_color("#d32f2f")
        median.set_linewidth(1.5)

    ax3.plot(
        coaching_summary["coaching_rate"],
        coaching_summary["mean_agent_value"],
        color="#2e7d32",
        marker="o",
        linewidth=1.5,
        label="Mean revenue",
    )
    ax3.legend(loc="upper left")

ax3.set_xlabel("Coaching Rate")
ax3.set_ylabel("Company Revenue")
ax3.set_title("Coaching Rate vs Revenue Between Companies (steady state)")
ax3.set_xticks(
    sorted(ldf["coaching_rate"].dropna().astype(int).unique().tolist())
    if not ldf.empty
    else []
)
ax3.grid(axis="y", alpha=0.25)
plt.tight_layout()
plot3 = os.path.join("output", "coaching_rate_vs_revenue_companies.png")
plt.savefig(plot3, dpi=150, bbox_inches="tight")
print(f"Saved: {plot3}")

print("\nDone!")
