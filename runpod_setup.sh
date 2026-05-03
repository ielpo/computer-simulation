#!/usr/bin/env bash
# runpod_setup.sh — run once on a fresh RunPod CPU pod
#
# Before running, upload the NetLogo archive and repo:
#   scp NetLogo-7.0.3-64.tgz root@<pod-ip>:~/computer-simulation/
#
# Usage:
#   bash runpod_setup.sh
#   bash runpod_setup.sh --netlogo-tgz /path/to/NetLogo-7.0.3-64.tgz
set -euo pipefail

NETLOGO_INSTALL_DIR="/opt/netlogo"
NETLOGO_TGZ="${NETLOGO_TGZ:-NetLogo-7.0.3-64.tgz}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --netlogo-tgz) NETLOGO_TGZ="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -f "$NETLOGO_TGZ" ]]; then
  echo "ERROR: Archive not found: $NETLOGO_TGZ"
  echo "Upload it first:  scp NetLogo-7.0.3-64.tgz root@<pod-ip>:~/computer-simulation/"
  exit 1
fi

# ── Step 1: Java ──────────────────────────────────────────────────────────────
echo "=== Step 1/5: Installing Java ==="
apt-get update -qq
apt-get install -y --no-install-recommends default-jdk-headless tar git python3 python3-pip > /dev/null
java -version

# ── Step 2: JAVA_HOME ─────────────────────────────────────────────────────────
echo ""
echo "=== Step 2/5: Setting JAVA_HOME ==="
# Use the JRE bundled with NetLogo (Java 17) rather than the system Java (Java 11).
# The rnd extension and others require class file version 61.0 (Java 17).
export JAVA_HOME="$NETLOGO_INSTALL_DIR/lib/runtime"
echo "JAVA_HOME=$JAVA_HOME"

# Persist across sessions
grep -q "JAVA_HOME" ~/.bashrc \
  && sed -i "s|export JAVA_HOME=.*|export JAVA_HOME=$JAVA_HOME|" ~/.bashrc \
  || echo "export JAVA_HOME=$JAVA_HOME" >> ~/.bashrc

# ── Step 3: NetLogo ───────────────────────────────────────────────────────────
echo ""
echo "=== Step 3/5: Installing NetLogo from $NETLOGO_TGZ ==="
if [[ -f "$NETLOGO_INSTALL_DIR/netlogo-headless.sh" ]]; then
  echo "Already installed at $NETLOGO_INSTALL_DIR — skipping."
else
  mkdir -p "$NETLOGO_INSTALL_DIR"
  tar -xzf "$NETLOGO_TGZ" -C "$NETLOGO_INSTALL_DIR" --strip-components=1
  echo "Installed at $NETLOGO_INSTALL_DIR"
fi

# Patch a bug in NetLogo 7.0.3: netlogo-headless.sh has a literal [] in
# JVM_OPTS which Java treats as the main class name, causing ClassNotFoundException.
if grep -q '\[\]' "$NETLOGO_INSTALL_DIR/netlogo-headless.sh"; then
  sed -i 's/ \[\])/)/g' "$NETLOGO_INSTALL_DIR/netlogo-headless.sh"
  echo "Patched [] bug in netlogo-headless.sh"
fi
grep -q "NETLOGO_HOME" ~/.bashrc || echo "export NETLOGO_HOME=$NETLOGO_INSTALL_DIR" >> ~/.bashrc

# ── Step 4: Python ────────────────────────────────────────────────────────────
echo ""
echo "=== Step 4/5: Installing Python dependencies ==="
pip install --quiet uv
uv sync

# ── Step 5: Verify ────────────────────────────────────────────────────────────
echo ""
echo "=== Step 5/5: Verifying setup ==="
python3 run_behaviorspace.py \
  --netlogo-home "$NETLOGO_INSTALL_DIR" \
  --list-experiments

echo ""
echo "Setup complete. Run experiments with:"
echo "  bash run_experiments.sh"
