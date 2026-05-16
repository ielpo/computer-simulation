#!/usr/bin/env bash
# run_experiments.sh — run all BehaviorSpace experiments on RunPod
#
# Usage:
#   bash run_experiments.sh
#   bash run_experiments.sh --threads 32
#   bash run_experiments.sh --experiments "coaching-output-exp3 strategy-exp3"
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
NETLOGO_INSTALL_DIR="/opt/netlogo"
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
    --threads)     THREADS="$2"; shift 2 ;;
    --experiments) IFS=' ' read -r -a EXPERIMENTS <<< "$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
[[ ${#EXPERIMENTS[@]} -eq 0 ]] && EXPERIMENTS=("${ALL_EXPERIMENTS[@]}")

# ── Verify Java is reachable ──────────────────────────────────────────────────
echo "java: $("$NETLOGO_INSTALL_DIR/lib/runtime/bin/java" -version 2>&1 | head -1)"

# ── Preflight checks ──────────────────────────────────────────────────────────
if [[ ! -f "$NETLOGO_INSTALL_DIR/NetLogo_Console" ]]; then
  echo "ERROR: NetLogo_Console not found. Run: bash runpod_setup.sh"
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
echo " Model      : $MODEL"
echo " Threads    : $THREADS / $(nproc) cores"
echo " JAVA_HOME  : $JAVA_HOME"
echo " Output     : $RESULTS_DIR"
echo " Experiments ($TOTAL):"
for exp in "${EXPERIMENTS[@]}"; do echo "   - $exp"; done
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
  echo "[$NUM/$TOTAL] Starting: $EXP  ($(date '+%H:%M:%S'))"

  SPREADSHEET="$RESULTS_DIR/${EXP}-spreadsheet.csv"
  TABLE="$RESULTS_DIR/${EXP}-table.csv"
  LOG="$RESULTS_DIR/${EXP}.log"
  START=$SECONDS

    # Run BehaviorSpace using the NetLogo_Console headless launcher.
    # Use an absolute path for the model so the launcher can find it.
    MODEL_PATH="$(pwd)/$MODEL"
    if "$NETLOGO_INSTALL_DIR/NetLogo_Console" --headless \
      --model       "$MODEL_PATH" \
      --experiment  "$EXP" \
      --spreadsheet "$SPREADSHEET" \
      --threads     "$THREADS" \
      > "$LOG" 2>&1; then
    ELAPSED=$((SECONDS - START))
    SIZE=$(du -sh "$SPREADSHEET" 2>/dev/null | cut -f1)
    echo "        Done in ${ELAPSED}s — spreadsheet: $SIZE"
    PASS=$((PASS + 1))
  else
    ELAPSED=$((SECONDS - START))
    echo "        FAILED after ${ELAPSED}s — see $LOG"
    tail -5 "$LOG"
    FAIL=$((FAIL + 1))
    FAILED_EXPS+=("$EXP")
  fi
  echo ""
done

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL_ELAPSED=$((SECONDS - START_TOTAL))
echo "================================================="
echo " Finished: $PASS passed, $FAIL failed"
echo " Total time: $((TOTAL_ELAPSED / 60))m $((TOTAL_ELAPSED % 60))s"
echo " Results: $RESULTS_DIR"
echo "================================================="

if [[ $FAIL -gt 0 ]]; then
  echo "Failed:"
  for exp in "${FAILED_EXPS[@]}"; do
    echo "  - $exp  (log: $RESULTS_DIR/${exp}.log)"
  done
fi

# ── Bundle for download ───────────────────────────────────────────────────────
ARCHIVE="results-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$ARCHIVE" "$RESULTS_DIR"
echo ""
echo "Results bundled: $ARCHIVE"
echo "Download with:"
echo "  scp root@<pod-ip>:$(pwd)/$ARCHIVE ."

exit $([[ $FAIL -eq 0 ]] && echo 0 || echo 1)
