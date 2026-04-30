#!/usr/bin/env bash
# run_experiments.sh — run all BehaviorSpace experiments on RunPod
# Usage: bash run_experiments.sh [--threads N] [--experiments "exp1 exp2 ..."]
#
# Defaults to all 6 research experiments using all available CPU cores.
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
NETLOGO_HOME="${NETLOGO_HOME:-/opt/netlogo}"
THREADS="${THREADS:-$(nproc)}"
RESULTS_DIR="results/$(date +%Y%m%d-%H%M%S)"
MODEL="simulation.nlogox"

ALL_EXPERIMENTS=(
  "coaching-output-exp1"
  "coaching-output-exp2"
  "coaching-output-exp3"
  "strategy-exp1"
  "strategy-exp2"
  "strategy-exp3"
)

# ── Parse args ────────────────────────────────────────────────────────────────
EXPERIMENTS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --threads)    THREADS="$2"; shift 2 ;;
    --experiments) IFS=' ' read -r -a EXPERIMENTS <<< "$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ ${#EXPERIMENTS[@]} -eq 0 ]]; then
  EXPERIMENTS=("${ALL_EXPERIMENTS[@]}")
fi

# ── Preflight checks ──────────────────────────────────────────────────────────
if [[ ! -f "$NETLOGO_HOME/netlogo-headless.sh" ]]; then
  echo "ERROR: netlogo-headless.sh not found at $NETLOGO_HOME"
  echo "  Run: bash runpod_setup.sh --netlogo-url <url>"
  exit 1
fi

if [[ ! -f "$MODEL" ]]; then
  echo "ERROR: $MODEL not found. Run from the repo root directory."
  exit 1
fi

mkdir -p "$RESULTS_DIR"

# ── Print plan ────────────────────────────────────────────────────────────────
TOTAL=${#EXPERIMENTS[@]}
echo "================================================="
echo " NetLogo BehaviorSpace — RunPod Runner"
echo "================================================="
echo " Model    : $MODEL"
echo " Threads  : $THREADS / $(nproc) cores"
echo " Output   : $RESULTS_DIR"
echo " Experiments ($TOTAL):"
for exp in "${EXPERIMENTS[@]}"; do
  echo "   - $exp"
done
echo "================================================="
echo ""

# ── Run experiments ───────────────────────────────────────────────────────────
PASS=0
FAIL=0
FAILED_EXPS=()
START_TOTAL=$SECONDS

for i in "${!EXPERIMENTS[@]}"; do
  EXP="${EXPERIMENTS[$i]}"
  NUM=$((i + 1))
  echo "[$NUM/$TOTAL] Starting: $EXP"
  echo "        $(date '+%H:%M:%S')"

  SPREADSHEET="$RESULTS_DIR/${EXP}-spreadsheet.csv"
  TABLE="$RESULTS_DIR/${EXP}-table.csv"
  LOG="$RESULTS_DIR/${EXP}.log"

  START=$SECONDS

  if python3 run_behaviorspace.py \
      --netlogo-home "$NETLOGO_HOME" \
      --model        "$MODEL" \
      --experiment   "$EXP" \
      --spreadsheet  "$SPREADSHEET" \
      --table        "$TABLE" \
      --threads      "$THREADS" \
      > "$LOG" 2>&1; then
    ELAPSED=$((SECONDS - START))
    echo "        Done in ${ELAPSED}s → $(du -sh "$SPREADSHEET" 2>/dev/null | cut -f1) spreadsheet"
    PASS=$((PASS + 1))
  else
    ELAPSED=$((SECONDS - START))
    echo "        FAILED after ${ELAPSED}s — see $LOG"
    FAIL=$((FAIL + 1))
    FAILED_EXPS+=("$EXP")
  fi
  echo ""
done

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL_ELAPSED=$((SECONDS - START_TOTAL))
TOTAL_MIN=$((TOTAL_ELAPSED / 60))

echo "================================================="
echo " Finished: $PASS passed, $FAIL failed"
echo " Total time: ${TOTAL_MIN}m $((TOTAL_ELAPSED % 60))s"
echo " Results: $RESULTS_DIR"
echo "================================================="

if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "Failed experiments:"
  for exp in "${FAILED_EXPS[@]}"; do
    echo "  - $exp (log: $RESULTS_DIR/${exp}.log)"
  done
fi

# ── Bundle results for download ───────────────────────────────────────────────
ARCHIVE="results-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$ARCHIVE" "$RESULTS_DIR"
echo ""
echo "Results bundled: $ARCHIVE"
echo "Download with:"
echo "  scp root@<pod-ip>:$(pwd)/$ARCHIVE ."

exit $([[ $FAIL -eq 0 ]] && echo 0 || echo 1)
