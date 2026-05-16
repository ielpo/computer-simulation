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
JAVA17="/usr/lib/jvm/java-17-openjdk-amd64/bin/java"

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

# ── Step 1: System packages ───────────────────────────────────────────────────
# Java 17 required: rnd extension compiled to class file version 61.0.
echo "=== Step 1/4: Installing system packages ==="
apt-get update -qq
apt-get install -y --no-install-recommends \
  openjdk-17-jdk-headless tar git python3 python3-pip > /dev/null
echo "Java: $(java -version 2>&1 | head -1)"

# Remove any stale JAVA_HOME from previous runs — we rely on the symlink instead.
sed -i '/JAVA_HOME/d' ~/.bashrc
unset JAVA_HOME || true

# ── Step 2: NetLogo ───────────────────────────────────────────────────────────
echo ""
echo "=== Step 2/4: Installing NetLogo ==="
if [[ -f "$NETLOGO_INSTALL_DIR/netlogo-headless.sh" ]]; then
  echo "Already installed at $NETLOGO_INSTALL_DIR — skipping extraction."
else
  mkdir -p "$NETLOGO_INSTALL_DIR"
  tar -xzf "$NETLOGO_TGZ" -C "$NETLOGO_INSTALL_DIR" --strip-components=1
  echo "Extracted to $NETLOGO_INSTALL_DIR"
fi

# Patch 1: NetLogo 7.0.3 has a literal [] in JVM_OPTS which Java treats as
# the main class name, causing ClassNotFoundException.
if grep -q '\[\]' "$NETLOGO_INSTALL_DIR/netlogo-headless.sh"; then
  sed -i 's/ \[\])/)/g' "$NETLOGO_INSTALL_DIR/netlogo-headless.sh"
  echo "Patched: removed stray [] from JVM_OPTS"
fi

# Patch 2: lib/runtime ships without a bin/ directory, but netlogo-headless.sh
# looks for $JAVA_HOME/bin/java (JAVA_HOME defaults to lib/runtime).
# Symlink Java 17 into the expected location. Done AFTER extraction so the
# tarball cannot overwrite it.
mkdir -p "$NETLOGO_INSTALL_DIR/lib/runtime/bin"
ln -sf "$JAVA17" "$NETLOGO_INSTALL_DIR/lib/runtime/bin/java"
echo "Linked Java 17 → $NETLOGO_INSTALL_DIR/lib/runtime/bin/java"
"$NETLOGO_INSTALL_DIR/lib/runtime/bin/java" -version 2>&1 | head -1

# ── Step 3: Verify ────────────────────────────────────────────────────────────
echo ""
echo "=== Step 4/4: Verifying setup ==="
"$NETLOGO_INSTALL_DIR/NetLogo_Console" --help > /dev/null
echo "NetLogo executable verified at $NETLOGO_INSTALL_DIR/NetLogo_Console"

echo ""
echo "Setup complete. Run experiments with:"
echo "  bash run_experiments.sh"
