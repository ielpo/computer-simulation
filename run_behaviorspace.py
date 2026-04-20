#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NetLogo BehaviorSpace experiments from the CLI."
    )
    parser.add_argument(
        "--model",
        default="simulation.nlogox",
        help="Path to the NetLogo model file (default: simulation.nlogox).",
    )
    parser.add_argument(
        "--experiment",
        help="BehaviorSpace experiment name to run.",
    )
    parser.add_argument(
        "--list-experiments",
        action="store_true",
        help="List available experiment names in the model and exit.",
    )
    parser.add_argument(
        "--netlogo-home",
        default=os.environ.get("NETLOGO_HOME"),
        help="NetLogo installation directory. Defaults to NETLOGO_HOME if set.",
    )
    parser.add_argument(
        "--headless-cmd",
        default=None,
        help="Explicit path/command for netlogo-headless.sh.",
    )
    parser.add_argument(
        "--table",
        default=None,
        help="Path for table output CSV. Defaults to output/<experiment>-table-<timestamp>.csv.",
    )
    parser.add_argument(
        "--spreadsheet",
        default=None,
        help="Path for spreadsheet output CSV. Defaults to output/<experiment>-spreadsheet-<timestamp>.csv.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of BehaviorSpace threads (optional).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command without executing it.",
    )
    return parser.parse_args()


def get_experiment_names(model_path: Path) -> list[str]:
    root = ET.parse(model_path).getroot()
    experiments = root.find("experiments")
    if experiments is None:
        return []

    names: list[str] = []
    for experiment in experiments.findall("experiment"):
        name = experiment.get("name")
        if name:
            names.append(name)
    return names


def resolve_headless_cmd(args: argparse.Namespace) -> str:
    if args.headless_cmd:
        return args.headless_cmd

    if args.netlogo_home:
        candidate = Path(args.netlogo_home) / "netlogo-headless.sh"
        if candidate.exists():
            return str(candidate)

    path_cmd = shutil.which("netlogo-headless.sh")
    if path_cmd:
        return path_cmd

    raise FileNotFoundError(
        "Could not find netlogo-headless.sh. Set NETLOGO_HOME, use --netlogo-home, or pass --headless-cmd."
    )


def default_output_paths(experiment: str) -> tuple[Path, Path]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    table = output_dir / f"{experiment}-table-{timestamp}.csv"
    spreadsheet = output_dir / f"{experiment}-spreadsheet-{timestamp}.csv"
    return table, spreadsheet


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)

    if not model_path.exists():
        print(f"Model file not found: {model_path}", file=sys.stderr)
        return 1

    try:
        experiments = get_experiment_names(model_path)
    except ET.ParseError as exc:
        print(f"Could not parse NetLogo model XML: {exc}", file=sys.stderr)
        return 1

    if args.list_experiments:
        if not experiments:
            print("No BehaviorSpace experiments found in model.")
            return 0
        print("Available experiments:")
        for name in experiments:
            print(f"- {name}")
        return 0

    if not args.experiment:
        print("--experiment is required unless --list-experiments is used.", file=sys.stderr)
        return 2

    if args.experiment not in experiments:
        print(
            f"Experiment '{args.experiment}' not found. Available: {', '.join(experiments) if experiments else 'none'}",
            file=sys.stderr,
        )
        return 2

    try:
        headless_cmd = resolve_headless_cmd(args)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    default_table, default_spreadsheet = default_output_paths(args.experiment)
    table_path = Path(args.table) if args.table else default_table
    spreadsheet_path = Path(args.spreadsheet) if args.spreadsheet else default_spreadsheet

    command = [
        headless_cmd,
        "--model",
        str(model_path),
        "--experiment",
        args.experiment,
        "--table",
        str(table_path),
        "--spreadsheet",
        str(spreadsheet_path),
    ]
    if args.threads is not None:
        command.extend(["--threads", str(args.threads)])

    print("Running NetLogo BehaviorSpace...")
    print(" ".join(command))

    if args.dry_run:
        return 0

    result = subprocess.run(command, check=False)
    if result.returncode == 0:
        print(f"Table output: {table_path}")
        print(f"Spreadsheet output: {spreadsheet_path}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
