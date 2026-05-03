import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

MODEL_PATH = Path("simulation.nlogox")
OUTPUT_DIR = Path("output")

## Adapt these values for your setup
NETLOGO_CONSOLE = "/opt/netlogo/NetLogo-7.0.3/NetLogo_Console"
THREAD_COUNT = 12


def get_experiment_names(model_path: Path) -> list[str]:
    root = ET.parse(model_path).getroot()
    experiments = root.find("experiments")
    if experiments is None:
        return []
    return [
        exp.get("name")
        for exp in experiments.findall("experiment")
        if exp.get("name") is not None
    ]


def run_experiment(console_cmd: str, experiment: str, total: int, index: int) -> int:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    spreadsheet_path = OUTPUT_DIR / f"{experiment}-spreadhseet-{timestamp}.csv"

    command = [
        console_cmd,
        "--headless",
        "--threads",
        str(THREAD_COUNT),
        "--model",
        str(MODEL_PATH),
        "--experiment",
        experiment,
        "--spreadsheet",
        str(spreadsheet_path),
    ]

    print(f"\n[{index}/{total}] Running experiment: {experiment}")
    print(f"  Spreadsheet output: {spreadsheet_path}")
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
        print(
            f"\n  [FAILED] Experiment '{experiment}' exited with code {proc.returncode}."
        )

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
    print(f"Found {total} experiment(s):")
    for idx, experiment in enumerate(experiments, start=1):
        print(f"  {idx}. {experiment}")

    # Prompt user to select experiments by index
    print("\nEnter the indices of the experiments to run, separated by commas.")
    print("Leave blank to run all experiments.")
    user_input = input("Selected experiments: ").strip()

    if user_input:
        try:
            selected_indices = [int(idx.strip()) for idx in user_input.split(",")]
            selected_experiments = [
                experiments[idx - 1] for idx in selected_indices if 1 <= idx <= total
            ]
            if not selected_experiments:
                print("No valid experiments selected.", file=sys.stderr)
                return 1
        except ValueError:
            print("Invalid input. Please enter valid indices.", file=sys.stderr)
            return 1
    else:
        selected_experiments = experiments

    print(
        f"\nRunning {len(selected_experiments)} experiment(s): {', '.join(selected_experiments)}"
    )

    failed: list[str] = []
    for i, experiment in enumerate(selected_experiments, start=1):
        rc = run_experiment(NETLOGO_CONSOLE, experiment, len(selected_experiments), i)
        if rc != 0:
            failed.append(experiment)

    print(f"\n{'=' * 60}")
    print(
        f"Completed {len(selected_experiments) - len(failed)}/{len(selected_experiments)} experiments successfully."
    )
    if failed:
        print(f"Failed experiments: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
