import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

PYTHON_DIRS = [
    ROOT / "scripts",
    ROOT / "pachinko-sim",
    ROOT / "tests",
]

JSON_FILES = [
    ROOT / "data" / "stores.json",
    ROOT / "data" / "namba-actual-1yen-lineup.json",
    ROOT / "data" / "latest.json",
    ROOT / "docs" / "latest.json",
    ROOT / "docs" / "latest-sim-results.json",
]


def run_step(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def python_files() -> list[str]:
    files = []
    for directory in PYTHON_DIRS:
        files.extend(sorted(str(path.relative_to(ROOT)) for path in directory.rglob("*.py")))
    return files


def validate_json_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        json.load(handle)


def validate_json_files() -> None:
    print("\n== JSON validation ==", flush=True)
    for path in JSON_FILES:
        if not path.exists():
            print(f"skip missing {path.relative_to(ROOT)}", flush=True)
            continue
        validate_json_file(path)
        print(f"ok {path.relative_to(ROOT)}", flush=True)


def require_optional_modules(module_names: list[str]) -> None:
    missing = [name for name in module_names if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit(
            "missing optional dev tool modules "
            f"{', '.join(missing)}. Install them with: python -m pip install -r requirements-dev.txt"
        )


def run_dev_tools() -> None:
    require_optional_modules(["ruff", "pytest"])
    run_step("Ruff lint", [PYTHON, "-m", "ruff", "check", "."])
    run_step("Pytest", [PYTHON, "-m", "pytest"])


def run_coverage() -> None:
    require_optional_modules(["coverage"])
    run_step("Coverage", [PYTHON, "-m", "coverage", "run", "-m", "unittest", "discover", "-s", "tests"])
    run_step("Coverage report", [PYTHON, "-m", "coverage", "report"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local quality checks without scraping external sites.")
    parser.add_argument(
        "--report",
        action="store_true",
        help="also regenerate data/latest.json and docs outputs via analyze/build_report",
    )
    parser.add_argument(
        "--dev-tools",
        action="store_true",
        help="also run optional tools from requirements-dev.txt: ruff and pytest",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="also run coverage.py over the unittest suite",
    )
    args = parser.parse_args()

    files = python_files()
    if not files:
        raise SystemExit("no Python files found")

    run_step("Python syntax", [PYTHON, "-m", "py_compile", *files])
    validate_json_files()
    run_step("Unit tests", [PYTHON, "-m", "unittest", "discover", "-s", "tests"])
    run_step("Data validation", [PYTHON, "scripts/validate_data.py"])
    run_step("Clean dry-run", [PYTHON, "scripts/clean.py"])

    if args.report:
        run_step("Analyze", [PYTHON, "scripts/analyze.py"])
        run_step("Build report", [PYTHON, "scripts/build_report.py"])
        validate_json_files()

    if args.dev_tools:
        run_dev_tools()

    if args.coverage:
        run_coverage()

    print("\nAll requested checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
