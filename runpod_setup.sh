#!/usr/bin/env bash
# runpod_setup.sh — run once on a fresh RunPod CPU pod
#
# Before running:
#   scp NetLogo-7.0.3-64.tgz root@<pod-ip>:~/computer-simulation/
#
# Usage:
#   bash runpod_setup.sh
#   bash runpod_setup.sh --netlogo-tgz /path/to/NetLogo-7.0.3-64.tgz
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
NETLOGO_INSTALL_DIR="/opt/netlogo"
NETLOGO_TGZ="${NETLOGO_TGZ:-NetLogo-7.0.3-64.tgz}"

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --netlogo-tgz) NETLOGO_TGZ="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -f "$NETLOGO_TGZ" ]]; then
  echo ""
  echo "ERROR: NetLogo archive not found: $NETLOGO_TGZ"
  echo ""
  echo "Upload it to the pod first:"
  echo "  scp NetLogo-7.0.3-64.tgz root@<pod-ip>:~/computer-simulation/"
  echo ""
  echo "Then re-run this script."
  exit 1
fi

echo "=== Step 1/4: Installing Java ==="
apt-get update -qq
apt-get install -y --no-install-recommends default-jdk-headless tar git python3 python3-pip > /dev/null
java -version

echo ""
echo "=== Step 2/4: Installing NetLogo from $NETLOGO_TGZ ==="
if [[ -f "$NETLOGO_INSTALL_DIR/netlogo-headless.sh" ]]; then
  echo "NetLogo already installed at $NETLOGO_INSTALL_DIR — skipping."
else
  mkdir -p "$NETLOGO_INSTALL_DIR"
  tar -xzf "$NETLOGO_TGZ" -C "$NETLOGO_INSTALL_DIR" --strip-components=1
  echo "NetLogo installed at $NETLOGO_INSTALL_DIR"
fi

echo ""
echo "=== Step 3/4: Installing Python dependencies ==="
pip install --quiet uv
uv sync

echo ""
echo "=== Step 4/4: Verifying setup ==="
echo "export NETLOGO_HOME=$NETLOGO_INSTALL_DIR" >> ~/.bashrc
export NETLOGO_HOME="$NETLOGO_INSTALL_DIR"

python3 run_behaviorspace.py \
  --netlogo-home "$NETLOGO_INSTALL_DIR" \
  --list-experiments

echo ""
echo "Setup complete. Run experiments with:"
echo "  bash run_experiments.sh"
