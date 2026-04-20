import csv
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Load CSV
# ---------------------------------------------------------------------------

FILEPATH = "simulation_turnover.csv"

with open(FILEPATH, "r", encoding="utf-8-sig") as f:
    rows = list(csv.reader(f))

# Locate key rows by their tag in column 0.
tag_rows: dict[str, int] = {}
for i, row in enumerate(rows):
    if not row:
        continue
    tag = clean_cell(row[0])
    if tag and tag not in tag_rows:
        tag_rows[tag] = i

run_number_idx = tag_rows.get("[run number]")
reporter_idx = tag_rows.get("[reporter]")
all_run_data_idx = tag_rows.get("[all run data]")

if all_run_data_idx is None:
    raise ValueError("Could not find [all run data] section in CSV")
if run_number_idx is None:
    raise ValueError("Could not find [run number] row in CSV")

# ---------------------------------------------------------------------------
# Determine reporters and column width per run.
# ---------------------------------------------------------------------------

ref_row = rows[reporter_idx][1:] if reporter_idx is not None else rows[all_run_data_idx][1:]
reporter_row = [clean_cell(x) for x in ref_row]

# The column block repeats; detect width by finding where the first header recurs.
first_header = reporter_row[0]
cols_per_run: list[str] = []
for h in reporter_row:
    if h == first_header and cols_per_run:
        break
    cols_per_run.append(h)

n_cols = len(cols_per_run)

safe_names = {
    "[step]": "step",
    "turnover-rate": "turnover_rate",
    "sorted-coaching": "sorted_coaching",
}
col_ids = [safe_names.get(h, h.replace("-", "_").replace(" ", "_")) for h in cols_per_run]

# Determine number of runs from the [run number] row.
run_number_values = [clean_cell(x) for x in rows[run_number_idx][1:] if clean_cell(x)]
n_runs = len(run_number_values) // n_cols

print(f"Reporters per run : {cols_per_run}")
print(f"Runs found        : {n_runs}  ({n_cols} columns each)")

# ---------------------------------------------------------------------------
# Parse parameter values per run.
# Every non-bracket-tagged row between [run number] and [reporter] is a param.
# ---------------------------------------------------------------------------

params: dict[str, list] = {}
end_idx = reporter_idx if reporter_idx is not None else all_run_data_idx
for i in range(run_number_idx + 1, end_idx):
    row = rows[i]
    if not row:
        continue
    tag = clean_cell(row[0])
    if not tag or tag.startswith("["):
        continue
    raw_vals = [clean_cell(x) for x in row[1:]]
    param_vals: list[float] = []
    for run_idx in range(n_runs):
        raw = raw_vals[run_idx * n_cols] if run_idx * n_cols < len(raw_vals) else ""
        try:
            param_vals.append(float(raw))
        except ValueError:
            param_vals.append(np.nan)
    params[tag] = param_vals

print(f"Parameters found  : {list(params.keys())}")
for name, vals in params.items():
    unique = sorted({v for v in vals if not np.isnan(v)})
    print(f"  {name}: {unique}")

# ---------------------------------------------------------------------------
# Parse [all run data] time-series.
# ---------------------------------------------------------------------------

records = []
for row in rows[all_run_data_idx + 1:]:
    if len(row) < 2 or clean_cell(row[1]) == "":
        continue
    values = row[1:]
    if len(values) < n_cols:
        continue

    for run_idx in range(n_runs):
        offset = run_idx * n_cols
        run_vals = values[offset: offset + n_cols]
        if len(run_vals) < n_cols:
            continue

        rec: dict = {"run": run_idx + 1}
        for pname, pvals in params.items():
            rec[pname] = pvals[run_idx] if run_idx < len(pvals) else np.nan

        for col_id, val in zip(col_ids, run_vals):
            text = clean_cell(val)
            if col_id == "sorted_coaching":
                rec[col_id] = parse_numeric_list(text)
            else:
                try:
                    rec[col_id] = float(text)
                except ValueError:
                    rec[col_id] = np.nan
        records.append(rec)

df = pd.DataFrame(records)
if df.empty:
    raise ValueError("No run data rows were parsed")

if "working-turnover-increase" in df.columns:
    df = df[df["working-turnover-increase"] != 0]

df["year"] = df["step"] / 100
max_step = df["step"].max()
print(f"\nParsed {len(df)} rows, ticks 0–{int(max_step)}")

# ---------------------------------------------------------------------------
# Steady-state: last 20% of ticks.
# ---------------------------------------------------------------------------

ss = df[df["step"] >= max_step * 0.8].copy()

param_cols = list(params.keys())
p1, p2 = param_cols[0], param_cols[1]

ss_agg = (
    ss.groupby(["run", p1, p2], as_index=False)["turnover_rate"]
    .agg(mean_turnover="mean", std_turnover="std", max_turnover="max")
)

print("\n-- Steady-state turnover-rate by parameter combination --")
print(ss_agg.round(3).sort_values([p1, p2]).to_string(index=False))

# ---------------------------------------------------------------------------
# Heatmaps: mean and max steady-state turnover over the parameter grid.
# ---------------------------------------------------------------------------

p1_vals = sorted(ss_agg[p1].unique())
p2_vals = sorted(ss_agg[p2].unique())


def make_grid(col: str) -> np.ndarray:
    grid = np.full((len(p2_vals), len(p1_vals)), np.nan)
    for _, row in ss_agg.iterrows():
        ix = p1_vals.index(row[p1])
        iy = p2_vals.index(row[p2])
        grid[iy, ix] = row[col]
    return grid


grid_mean = make_grid("mean_turnover")
grid_max = make_grid("max_turnover")

os.makedirs("output", exist_ok=True)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle(
    f"Parameter Space: {p1} × {p2}  →  Steady-State Turnover Rate",
    fontsize=13, fontweight="bold",
)

for ax, grid, title in [
    (axes[0], grid_mean, "Mean turnover rate (steady state)"),
    (axes[1], grid_max, "Max turnover rate (steady state)"),
]:
    im = ax.imshow(grid, origin="lower", aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(range(len(p1_vals)))
    ax.set_xticklabels([f"{v:.2g}" for v in p1_vals], rotation=45, ha="right")
    ax.set_yticks(range(len(p2_vals)))
    ax.set_yticklabels([f"{v:.2g}" for v in p2_vals])
    ax.set_xlabel(p1)
    ax.set_ylabel(p2)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, shrink=0.85)
    for iy in range(len(p2_vals)):
        for ix in range(len(p1_vals)):
            val = grid[iy, ix]
            if not np.isnan(val):
                ax.text(ix, iy, f"{val:.1f}", ha="center", va="center", fontsize=7)

plt.tight_layout()
heatmap_path = os.path.join("output", "turnover_parameter_heatmap.png")
plt.savefig(heatmap_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {heatmap_path}")

# ---------------------------------------------------------------------------
# Time-series: one panel per p1 value, one line per p2 value.
# ---------------------------------------------------------------------------

sample_every = max(1, int(max_step / 400))
sampled = df[df["step"] % sample_every == 0].copy()

p1_unique = sorted(df[p1].dropna().unique())
p2_unique = sorted(df[p2].dropna().unique())
n_p1 = len(p1_unique)

fig2, axes2 = plt.subplots(
    1, n_p1, figsize=(4 * n_p1, 4), sharey=True, constrained_layout=True
)
if n_p1 == 1:
    axes2 = [axes2]
fig2.suptitle(
    f"Turnover Rate Over Time  —  one panel per '{p1}' value",
    fontsize=12, fontweight="bold",
)

palette = plt.cm.plasma(np.linspace(0.1, 0.9, len(p2_unique)))

for ax, p1_val in zip(axes2, p1_unique):
    subset_p1 = sampled[np.isclose(sampled[p1], p1_val)]
    for color, p2_val in zip(palette, p2_unique):
        subset = subset_p1[np.isclose(subset_p1[p2], p2_val)]
        if subset.empty:
            continue
        ax.plot(
            subset["year"],
            subset["turnover_rate"],
            color=color,
            linewidth=0.9,
            alpha=0.85,
            label=f"{p2_val:.2g}",
        )
    # Mark the start of the steady-state window.
    ax.axvline(max_step * 0.8 / 100, color="grey", linestyle="--", linewidth=0.7, alpha=0.6)
    ax.set_title(f"{p1}={p1_val:.2g}")
    ax.set_xlabel("Year")
    if ax is axes2[0]:
        ax.set_ylabel("Turnover Rate")

handles, labels = axes2[-1].get_legend_handles_labels()
fig2.legend(
    handles, labels, title=p2, loc="upper right",
    fontsize=7, title_fontsize=8, bbox_to_anchor=(1.0, 1.0), framealpha=0.8,
)
timeseries_path = os.path.join("output", "turnover_timeseries.png")
plt.savefig(timeseries_path, dpi=150, bbox_inches="tight")
print(f"Saved: {timeseries_path}")

# ---------------------------------------------------------------------------
# Stability: coefficient of variation of turnover-rate in the steady state.
# ---------------------------------------------------------------------------

ss_cv = ss_agg.copy()
ss_cv["cv"] = ss_cv["std_turnover"] / ss_cv["mean_turnover"].replace(0, np.nan)

grid_cv = np.full((len(p2_vals), len(p1_vals)), np.nan)
for _, row in ss_cv.iterrows():
    ix = p1_vals.index(row[p1])
    iy = p2_vals.index(row[p2])
    grid_cv[iy, ix] = row["cv"]

fig3, ax3 = plt.subplots(figsize=(7, 5))
im3 = ax3.imshow(grid_cv, origin="lower", aspect="auto", cmap="Blues", interpolation="nearest")
ax3.set_xticks(range(len(p1_vals)))
ax3.set_xticklabels([f"{v:.2g}" for v in p1_vals], rotation=45, ha="right")
ax3.set_yticks(range(len(p2_vals)))
ax3.set_yticklabels([f"{v:.2g}" for v in p2_vals])
ax3.set_xlabel(p1)
ax3.set_ylabel(p2)
ax3.set_title(
    "Coefficient of Variation of Turnover Rate (steady state)\n"
    "Lower = more stable behaviour"
)
plt.colorbar(im3, ax=ax3, shrink=0.85)
for iy in range(len(p2_vals)):
    for ix in range(len(p1_vals)):
        val = grid_cv[iy, ix]
        if not np.isnan(val):
            ax3.text(ix, iy, f"{val:.2f}", ha="center", va="center", fontsize=7)
plt.tight_layout()
cv_path = os.path.join("output", "turnover_stability_cv.png")
plt.savefig(cv_path, dpi=150, bbox_inches="tight")
print(f"Saved: {cv_path}")

# ---------------------------------------------------------------------------
# Ranked summary: combinations with lowest, most stable turnover first.
# ---------------------------------------------------------------------------

ss_cv_sorted = ss_cv.sort_values(["mean_turnover", "cv"]).reset_index(drop=True)
print("\n-- Parameter combinations ranked by mean steady-state turnover (ascending) --")
print(
    ss_cv_sorted[[p1, p2, "mean_turnover", "std_turnover", "max_turnover", "cv"]]
    .round(3)
    .to_string(index=False)
)

print("\nDone!")
