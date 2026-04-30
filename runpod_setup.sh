#!/usr/bin/env bash
# runpod_setup.sh — run once on a fresh RunPod CPU pod
# Usage: bash runpod_setup.sh [--netlogo-url <url>]
#
# After this script completes, run experiments with:
#   bash run_experiments.sh
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
NETLOGO_VERSION="7.0.3"
NETLOGO_INSTALL_DIR="/opt/netlogo"
NETLOGO_URL="${NETLOGO_URL:-}"   # pass via env or --netlogo-url flag

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --netlogo-url) NETLOGO_URL="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$NETLOGO_URL" ]]; then
  echo ""
  echo "ERROR: NetLogo download URL required."
  echo "  1. Go to https://ccl.northwestern.edu/netlogo/ → Downloads"
  echo "  2. Copy the Linux (.tgz) download link for NetLogo $NETLOGO_VERSION"
  echo "  3. Re-run: NETLOGO_URL=<paste-url> bash runpod_setup.sh"
  echo ""
  exit 1
fi

echo "=== Step 1/4: Installing Java ==="
apt-get update -qq
apt-get install -y --no-install-recommends default-jdk-headless wget tar git python3 python3-pip > /dev/null
java -version

echo ""
echo "=== Step 2/4: Downloading NetLogo $NETLOGO_VERSION ==="
if [[ -f "$NETLOGO_INSTALL_DIR/netlogo-headless.sh" ]]; then
  echo "NetLogo already installed at $NETLOGO_INSTALL_DIR — skipping."
else
  TMP=$(mktemp -d)
  wget -q --show-progress "$NETLOGO_URL" -O "$TMP/netlogo.tgz"
  mkdir -p "$NETLOGO_INSTALL_DIR"
  tar -xzf "$TMP/netlogo.tgz" -C "$NETLOGO_INSTALL_DIR" --strip-components=1
  rm -rf "$TMP"
  echo "NetLogo installed at $NETLOGO_INSTALL_DIR"
fi

echo ""
echo "=== Step 3/4: Installing Python dependencies ==="
pip install --quiet uv
uv sync

echo ""
echo "=== Step 4/4: Verifying setup ==="
echo "NETLOGO_HOME=$NETLOGO_INSTALL_DIR"
echo "export NETLOGO_HOME=$NETLOGO_INSTALL_DIR" >> ~/.bashrc

python3 run_behaviorspace.py \
  --netlogo-home "$NETLOGO_INSTALL_DIR" \
  --list-experiments

echo ""
echo "Setup complete. Run experiments with:"
echo "  bash run_experiments.sh"
