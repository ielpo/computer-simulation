import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv
import os

# ── Parse the BehaviorSpace spreadsheet format ──────────────────────────
filepath = "/mnt/user-data/uploads/simulation_coaching-rate-vs-revenue-spreadsheet-mixed-coaching-rates-long-run.csv"

with open(filepath, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

# Locate the "[all run data]" section
data_start = None
for i, row in enumerate(rows):
    if row and row[0].strip('"') == "[all run data]":
        data_start = i
        break

if data_start is None:
    raise ValueError("Could not find [all run data] section")

cols_per_run = [
    "step", "count_turtles", "revenue_rate", "avg_skill", "turnover_rate",
    *[f"revenue_at_rate_{r}" for r in range(1, 13)],
    *[f"skill_at_rate_{r}" for r in range(1, 13)],
]
n_cols = len(cols_per_run)

run_number_row = rows[6]
run_numbers = [int(x.strip('"')) for x in run_number_row[1:] if x.strip('"').isdigit()]
n_runs = len(run_numbers) // n_cols
print(f"Found {n_runs} runs, {n_cols} columns per run")

all_frames = []
for row in rows[data_start + 1:]:
    if len(row) < 2 or row[1].strip('"') == "":
        continue
    values = row[1:]
    for run_idx in range(n_runs):
        offset = run_idx * n_cols
        run_vals = values[offset:offset + n_cols]
        if len(run_vals) < n_cols:
            continue
        record = {"run": run_idx + 1}
        for j, col in enumerate(cols_per_run):
            try:
                record[col] = float(run_vals[j].strip('"'))
            except (ValueError, IndexError):
                record[col] = np.nan
        all_frames.append(record)

df = pd.DataFrame(all_frames)
df["year"] = df["step"] / 100
print(f"Parsed {len(df)} rows, steps 0–{int(df['step'].max())}")

# ── Steady-state summary (last 20%) ────────────────────────────────────
rates = list(range(1, 13))
steady_state = df[df["step"] >= df["step"].max() * 0.8].copy()

summary = []
for r in rates:
    rev = steady_state[f"revenue_at_rate_{r}"].dropna()
    sk = steady_state[f"skill_at_rate_{r}"].dropna()
    rev = rev[rev > 0]
    sk = sk[sk > 0]
    summary.append({
        "coaching_rate": r,
        "mean_revenue": rev.mean(),
        "std_revenue": rev.std(),
        "mean_skill": sk.mean(),
        "std_skill": sk.std(),
        "n": len(rev),
    })

sdf = pd.DataFrame(summary)
print("\n── Steady-state summary (last 20% of ticks) ──")
print(sdf.to_string(index=False))

# ── Helper: add value labels on bars ────────────────────────────────────
def label_bars(ax, values, fmt="{:.0f}"):
    for bar, val in zip(ax.patches, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                fmt.format(val), ha="center", va="bottom", fontsize=8, fontweight="bold")

# ── PLOTS ───────────────────────────────────────────────────────────────
colors = plt.cm.viridis(np.linspace(0.1, 0.9, 12))

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Coaching Rate Analysis — Finding the Sweet Spot (Long Run)", fontsize=15, fontweight="bold")

# Plot 1: Revenue by coaching rate
ax = axes[0, 0]
ax.bar(sdf["coaching_rate"], sdf["mean_revenue"],
       yerr=sdf["std_revenue"], capsize=3, color=colors, edgecolor="white", linewidth=0.5)
ax.set_xlabel("Coaching Rate (%)")
ax.set_ylabel("Mean Revenue (steady state)")
ax.set_title("Revenue by Coaching Rate")
ax.set_xticks(rates)
label_bars(ax, sdf["mean_revenue"])

# Plot 2: Skill by coaching rate
ax = axes[0, 1]
ax.bar(sdf["coaching_rate"], sdf["mean_skill"],
       yerr=sdf["std_skill"], capsize=3, color=colors, edgecolor="white", linewidth=0.5)
ax.set_xlabel("Coaching Rate (%)")
ax.set_ylabel("Mean Skill Level (steady state)")
ax.set_title("Skill Level by Coaching Rate")
ax.set_xticks(rates)
label_bars(ax, sdf["mean_skill"])

# Plot 3: Revenue over time
ax = axes[1, 0]
sample_every = max(1, int(df["step"].max() / 300))
sampled = df[df["step"] % sample_every == 0].copy()
for i, r in enumerate(rates):
    ts = sampled.groupby("step")[f"revenue_at_rate_{r}"].mean().replace(0, np.nan)
    ax.plot(ts.index / 100, ts.values, color=colors[i], alpha=0.7, linewidth=1, label=f"{r}%")
ax.set_xlabel("Year")
ax.set_ylabel("Mean Revenue")
ax.set_title("Revenue Over Time by Coaching Rate")
ax.legend(title="Rate", fontsize=7, ncol=3, loc="lower right")

# Plot 4: Revenue vs Skill scatter
ax = axes[1, 1]
sc = ax.scatter(sdf["mean_skill"], sdf["mean_revenue"],
                c=sdf["coaching_rate"], cmap="viridis", s=120, edgecolors="black", zorder=5)
for _, row in sdf.iterrows():
    ax.annotate(f'{int(row["coaching_rate"])}%',
                (row["mean_skill"], row["mean_revenue"]),
                textcoords="offset points", xytext=(8, 4), fontsize=9)
ax.set_xlabel("Mean Skill Level")
ax.set_ylabel("Mean Revenue")
ax.set_title("Revenue vs Skill Trade-off")
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label("Coaching Rate (%)")

plt.tight_layout()
plt.savefig("/home/claude/coaching_analysis_long.png", dpi=150, bbox_inches="tight")
print("\nSaved: coaching_analysis_long.png")

# ── Plot 5: Revenue efficiency ──────────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(10, 5))
sdf["revenue_per_skill"] = sdf["mean_revenue"] / sdf["mean_skill"]
ax2.bar(sdf["coaching_rate"], sdf["revenue_per_skill"],
        color=colors, edgecolor="white", linewidth=0.5)
ax2.set_xlabel("Coaching Rate (%)")
ax2.set_ylabel("Revenue per Skill Unit")
ax2.set_title("Revenue Efficiency by Coaching Rate — Higher = Better Skill Utilization")
ax2.set_xticks(rates)
label_bars(ax2, sdf["revenue_per_skill"], fmt="{:.1f}")
plt.tight_layout()
plt.savefig("/home/claude/coaching_efficiency_long.png", dpi=150, bbox_inches="tight")
print("Saved: coaching_efficiency_long.png")

# Copy to outputs
os.makedirs("/mnt/user-data/outputs", exist_ok=True)
for f in ["coaching_analysis_long.png", "coaching_efficiency_long.png"]:
    os.system(f"cp /home/claude/{f} /mnt/user-data/outputs/{f}")
print("\nDone!")
