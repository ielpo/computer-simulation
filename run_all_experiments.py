#!/usr/bin/env python3
"""Run all BehaviorSpace experiments in simulation.nlogox using NetLogo_Console headless mode."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

MODEL_PATH = Path("simulation.nlogox")
OUTPUT_DIR = Path("output")
NETLOGO_CONSOLE = "/root/netlogo/NetLogo_Console"


def get_experiment_names(model_path: Path) -> list[str]:
    root = ET.parse(model_path).getroot()
    experiments = root.find("experiments")
    if experiments is None:
        return []
    return [exp.get("name") for exp in experiments.findall("experiment") if exp.get("name")]


def run_experiment(console_cmd: str, experiment: str, total: int, index: int) -> int:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    table_path = OUTPUT_DIR / f"{experiment}-table-{timestamp}.csv"

    command = [
        console_cmd,
        "--headless",
        "--model", str(MODEL_PATH),
        "--experiment", experiment,
        "--table", str(table_path),
    ]

    print(f"\n[{index}/{total}] Running experiment: {experiment}")
    print(f"  Table output: {table_path}")
    print(f"  Command: {' '.join(command)}\n")

    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as proc:
        for line in proc.stdout:
            print(f"  {line}", end="")
        proc.wait()

    if proc.returncode == 0:
        print(f"\n  [OK] Experiment '{experiment}' completed.")
    else:
        print(f"\n  [FAILED] Experiment '{experiment}' exited with code {proc.returncode}.")

    return proc.returncode


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"Model file not found: {MODEL_PATH}", file=sys.stderr)
        return 1

    try:
        experiments = get_experiment_names(MODEL_PATH)
    except ET.ParseError as exc:
        print(f"Could not parse NetLogo model XML: {exc}", file=sys.stderr)
        return 1

    if not experiments:
        print("No BehaviorSpace experiments found in model.", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)

    total = len(experiments)
    print(f"Found {total} experiment(s): {', '.join(experiments)}")

    failed: list[str] = []
    for i, experiment in enumerate(experiments, start=1):
        rc = run_experiment(NETLOGO_CONSOLE, experiment, total, i)
        if rc != 0:
            failed.append(experiment)

    print(f"\n{'='*60}")
    print(f"Completed {total - len(failed)}/{total} experiments successfully.")
    if failed:
        print(f"Failed experiments: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
