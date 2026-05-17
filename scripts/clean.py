import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILE_PATTERNS = [
    ".coverage",
    "results.csv",
    "pachinko-sim/results.csv",
    "docs/sim-results-*",
    "docs/simulator-results-*",
]

DIR_PATTERNS = [
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "__pycache__",
    "*/__pycache__",
    "*/*/__pycache__",
]


def iter_matches(patterns: list[str]) -> list[Path]:
    matches = []
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            matches.append(path)
    return sorted(set(matches), key=lambda path: str(path))


def is_safe_target(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def remove_path(path: Path) -> None:
    if not is_safe_target(path):
        raise ValueError(f"Refusing to clean outside repository: {path}")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def clean(dry_run: bool = True) -> list[Path]:
    targets = []
    targets.extend(path for path in iter_matches(FILE_PATTERNS) if path.is_file())
    targets.extend(path for path in iter_matches(DIR_PATTERNS) if path.is_dir())
    unique_targets = sorted(set(targets), key=lambda path: str(path))

    for path in unique_targets:
        relative = path.relative_to(ROOT)
        action = "would remove" if dry_run else "remove"
        print(f"{action}: {relative}")
        if not dry_run:
            remove_path(path)

    if not unique_targets:
        print("clean: no generated artifacts found")
    return unique_targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean local generated artifacts and obsolete simulator result files.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually remove files. Without this flag the command only prints what would be removed.",
    )
    args = parser.parse_args()

    clean(dry_run=not args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
