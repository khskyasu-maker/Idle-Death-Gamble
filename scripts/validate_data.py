import json
import re
import sys
import fnmatch
import subprocess
from pathlib import Path
from datetime import datetime
from utils import get_data_path, load_json, logger

MACHINE_INFO_FILES = [
    "namba-actual-1yen-lineup.json",
]

ALLOWED_MACHINE_INFO_CATEGORIES = {
    "eva",
    "daiumi",
    "other",
}

ALLOWED_MACHINE_INFO_RATES = {"1yen", "1.111yen"}
ALLOWED_MACHINE_INFO_SOURCES = {"pworld", "dmm", "app", "onsite", "manual_note"}
ALLOWED_MACHINE_INFO_INSTALL_SOURCES = {"dmm_pachitown", "pworld", "manual_note"}
ALLOWED_MACHINE_INFO_SPEC_SOURCES = {"chonborista", "dmm_pachitown", "manual_note"}

REQUIRED_MACHINE_INFO_FIELDS = [
    "store_id",
    "store_name",
    "store_name_ko",
    "machine_name",
    "machine_name_ko",
    "rate",
    "category",
    "spec_type",
    "initial_probability",
    "rush_type",
    "machine_count",
    "source_type",
    "checked_at",
    "memo",
]

DISALLOWED_PUBLIC_MACHINE_INFO_FIELDS = {
    "visit_rank",
    "visit_order",
    "visit_priority",
    "recommendation_score",
    "recommended_today",
    "go_today",
    "today_target",
    "final_decision",
    "jackpot_likelihood",
    "jackpot_probability",
    "win_probability",
    "winning_rate",
    "sim_supported",
    "sim_model_key",
    "spec_confidence",
    "lineup_confidence",
    "unsupported_reason",
    "temporary_category",
    "risk_level",
    "first_test_budget",
    "keep_condition",
    "quit_condition",
    "is_eva",
    "is_umi",
    "is_re_zero",
    "is_lt",
}

MANUAL_PUBLIC_DOC_FILES = [
    "docs/eva-spec-summary.md",
    "docs/eva-spec-summary.html",
]

DISALLOWED_MANUAL_PUBLIC_TEXT_PATTERNS = [
    "추천 순서",
    "첫 방문 추천",
    "기종 우선순위",
    "우선순위",
    "visit_priority",
    "승률",
    "당첨 예측",
]

PUBLIC_PRIVACY_SCAN_FILES = [
    "README.md",
    "AGENTS.md",
    "data/stores.json",
    "data/namba-actual-1yen-lineup.json",
    "docs/eva-spec-summary.md",
    "docs/eva-spec-summary.html",
    "docs/ai-context.md",
    "docs/simulator-ai-context.md",
    "docs/onsite-input-template.md",
    "docs/latest-report.md",
    "docs/index.html",
    "docs/latest.json",
    "pachinko-sim/README.md",
    "pachinko-sim/ARCHITECTURE.md",
    "pachinko-sim/machine_traits.py",
    "pachinko-sim/sim_terms.py",
    "pachinko-sim/spec_benchmarks.py",
    "pachinko-sim/start_gate.py",
    "pachinko-sim/time_model.py",
    "pachinko-sim/store_comparison.py",
    ".github/workflows/daily.yml",
]

PUBLIC_PRIVACY_TEXT_PATTERNS = [
    (r"예약\s*번호", "reservation number"),
    (r"reservation\s*(number|no\.?|id\b)", "reservation number"),
    (r"booking\s*(number|no\.?|id\b)", "booking number"),
    (r"여권\s*번호", "passport number"),
    (r"passport\s*(number|no\.?|id\b)", "passport number"),
    (r"항공편\s*번호", "flight number"),
    (r"flight\s*(number|no\.?|id\b)", "flight number"),
    (r"항공권\s*예약", "flight booking"),
    (r"숙소\s*(주소|예약|체크인|체크아웃)", "lodging details"),
    (r"호텔\s*(주소|예약|체크인|체크아웃)", "hotel details"),
    (r"(출국|입국)\s*(일|날짜|시간)", "arrival/departure schedule"),
]

PRIVATE_PUBLIC_JSON_FIELDS = {
    "travel_date",
    "travel_dates",
    "travel_schedule",
    "itinerary",
    "trip_plan",
    "arrival_date",
    "departure_date",
    "arrival_time",
    "departure_time",
    "flight_number",
    "flight_booking",
    "reservation_number",
    "booking_number",
    "passport_number",
    "hotel",
    "hotel_name",
    "hotel_address",
    "accommodation",
    "lodging",
    "checkin",
    "checkout",
    "check_in",
    "check_out",
    "personal_budget",
    "private_note",
    "personal_note",
}

DISALLOWED_TRACKED_ARTIFACT_PATTERNS = [
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.db-*",
    "*.pyc",
    "results.csv",
    "pachinko-sim/results.csv",
    "pachinko-sim/results-*.csv",
    "data/pachinko.sqlite",
    "data/machine-snapshots/*",
    "*/__pycache__/*",
]


def add_issue(issues, path, message):
    issues.append(f"{path}: {message}")


def parse_date(value):
    if not isinstance(value, str) or not value.strip():
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S KST"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_probability(value, path, errors, warnings):
    if value in ("", None):
        add_issue(warnings, path, "missing probability keeps this as a loose candidate")
        return

    if not isinstance(value, str):
        add_issue(errors, path, "must be a string like 1/99, 1/199, or 1/319")
        return

    if not re.fullmatch(r"1/[0-9]{2,3}(?:\.[0-9]+)?", value.strip()):
        add_issue(
            warnings,
            path,
            "expected a simple probability string like 1/99 or 1/319",
        )


def machine_info_from_raw(raw, errors, file_name):
    if isinstance(raw, dict):
        machines = raw.get("machines", [])
        if not isinstance(machines, list):
            add_issue(
                errors,
                f"data/{file_name}.machines",
                "must be a list",
            )
            return []
        return machines

    add_issue(
        errors,
        f"data/{file_name}",
        "must be an object with machines[]",
    )
    return []


def validate_no_known_lineup_mixups(machines, errors, file_name):
    """Catch high-impact model-name mixups in the Namba low-rate lineup."""
    expected_store_rates = {
        "rakuen_namba": "1.111yen",
        "123_namba": "1yen",
        "arrow_namba_hips": "1yen",
    }

    for index, machine in enumerate(machines):
        path = f"data/{file_name}.machines[{index}]"
        store_id = machine.get("store_id", "")
        machine_name = machine.get("machine_name", "")
        machine_count = machine.get("machine_count", 0)
        rate = machine.get("rate", "")

        if file_name == "namba-actual-1yen-lineup.json" and rate == "4yen":
            add_issue(
                errors,
                f"{path}.rate",
                "4yen machines must not be stored in the corrected Namba low-rate lineup file.",
            )

        expected_rate = expected_store_rates.get(store_id)
        if expected_rate and rate and rate != expected_rate:
            add_issue(
                errors,
                f"{path}.rate",
                f"{store_id} low-rate lineup must use {expected_rate}, got {rate}",
            )

        if store_id == "rakuen_namba" and "with アイマリン" in machine_name:
            add_issue(
                errors,
                path,
                "Rakuen Namba low-rate lineup should not contain with アイマリン. It is likely 夜桜超旋風 99ver. or an onsite-only change.",
            )

        if (
            store_id == "rakuen_namba"
            and "PAスーパー海物語 IN 沖縄5 夜桜超旋風 99ver." in machine_name
            and machine_count != 5
        ):
            add_issue(
                errors,
                f"{path}.machine_count",
                "Rakuen 夜桜超旋風 99ver. expected count is 5 in the corrected low-rate baseline.",
            )

        if (
            store_id == "123_namba"
            and "PAスーパー海物語 IN 沖縄5 with アイマリン" in machine_name
            and machine_count != 1
        ):
            add_issue(
                errors,
                f"{path}.machine_count",
                "123 Namba アイマリン expected count is 1 in the corrected low-rate baseline.",
            )


def validate_machine_info_file(file_name, errors, warnings, required=False):
    raw = load_json(get_data_path(file_name), None)
    if raw is None:
        if required:
            add_issue(errors, f"data/{file_name}", "file is missing")
        else:
            add_issue(warnings, f"data/{file_name}", "file is missing")
        return

    updated_at = raw.get("updated_at", "") if isinstance(raw, dict) else ""
    if updated_at and parse_date(updated_at) is None:
        add_issue(
            errors,
            f"data/{file_name}.updated_at",
            "must be a supported timestamp",
        )

    machines = machine_info_from_raw(raw, errors, file_name)
    for index, machine in enumerate(machines):
        path = f"data/{file_name}.machines[{index}]"
        if not isinstance(machine, dict):
            add_issue(errors, path, "machine entry must be an object")
            continue

        for field in REQUIRED_MACHINE_INFO_FIELDS:
            if field not in machine:
                add_issue(warnings, f"{path}.{field}", "field is missing")

        for field in DISALLOWED_PUBLIC_MACHINE_INFO_FIELDS:
            if field in machine:
                add_issue(
                    errors,
                    f"{path}.{field}",
                    "must not be stored in GitHub public machine data",
                )

        store_id = machine.get("store_id", "")
        if not isinstance(store_id, str) or not store_id:
            add_issue(errors, f"{path}.store_id", "must be a non-empty string")

        if not machine.get("machine_name"):
            add_issue(errors, f"{path}.machine_name", "must be a non-empty string")

        rate = machine.get("rate", "")
        if not isinstance(rate, str) or rate not in ALLOWED_MACHINE_INFO_RATES:
            add_issue(
                errors,
                f"{path}.rate",
                f"must be one of {sorted(ALLOWED_MACHINE_INFO_RATES)}",
            )

        category = machine.get("category", "")
        if (
            not isinstance(category, str)
            or category not in ALLOWED_MACHINE_INFO_CATEGORIES
        ):
            add_issue(
                errors,
                f"{path}.category",
                f"must be one of {sorted(ALLOWED_MACHINE_INFO_CATEGORIES)}",
            )

        source_type = machine.get("source_type", "")
        if (
            not isinstance(source_type, str)
            or source_type not in ALLOWED_MACHINE_INFO_SOURCES
        ):
            add_issue(
                errors,
                f"{path}.source_type",
                f"must be one of {sorted(ALLOWED_MACHINE_INFO_SOURCES)}",
            )

        install_source = machine.get("install_source")
        if install_source and (
            not isinstance(install_source, str)
            or install_source not in ALLOWED_MACHINE_INFO_INSTALL_SOURCES
        ):
            add_issue(
                errors,
                f"{path}.install_source",
                f"if present, must be one of {sorted(ALLOWED_MACHINE_INFO_INSTALL_SOURCES)}",
            )

        spec_source = machine.get("spec_source")
        if spec_source and (
            not isinstance(spec_source, str)
            or spec_source not in ALLOWED_MACHINE_INFO_SPEC_SOURCES
        ):
            add_issue(
                errors,
                f"{path}.spec_source",
                f"if present, must be one of {sorted(ALLOWED_MACHINE_INFO_SPEC_SOURCES)}",
            )

        install_source_url = machine.get("install_source_url")
        if install_source_url and not isinstance(install_source_url, str):
            add_issue(
                errors, f"{path}.install_source_url", "if present, must be a string"
            )

        spec_source_url = machine.get("spec_source_url")
        if spec_source_url and not isinstance(spec_source_url, str):
            add_issue(errors, f"{path}.spec_source_url", "if present, must be a string")

        checked_at = machine.get("checked_at", "")
        if checked_at and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked_at):
            add_issue(
                errors,
                f"{path}.checked_at",
                "must be YYYY-MM-DD",
            )
        elif not checked_at:
            add_issue(
                warnings,
                f"{path}.checked_at",
                "missing check date reduces usefulness",
            )

        validate_probability(
            machine.get("initial_probability", ""),
            f"{path}.initial_probability",
            errors,
            warnings,
        )

        for field in (
            "store_name",
            "store_name_ko",
            "machine_name_ko",
            "spec_type",
            "rush_type",
            "memo",
        ):
            value = machine.get(field, "")
            if value is not None and not isinstance(value, str):
                add_issue(errors, f"{path}.{field}", "must be a string")

        machine_count = machine.get("machine_count")
        if not isinstance(machine_count, int) or machine_count < 1:
            add_issue(errors, f"{path}.machine_count", "must be an integer >= 1")

        for border_field in (
            "border_4yen_per_250",
            "border_1yen_per_200",
            "border_1_111yen_per_180",
        ):
            val = machine.get(border_field)
            if val not in (None, ""):
                try:
                    v = float(val)
                    if v <= 0:
                        add_issue(
                            errors, f"{path}.{border_field}", "must be a number > 0"
                        )
                except ValueError:
                    add_issue(errors, f"{path}.{border_field}", "must be a number")

        for str_field in ("border_source", "border_source_url", "border_note"):
            val = machine.get(str_field)
            if val is not None and not isinstance(val, str):
                add_issue(errors, f"{path}.{str_field}", "must be a string")

    validate_no_known_lineup_mixups(machines, errors, file_name)


def validate_machine_info(errors, warnings):
    for file_name in MACHINE_INFO_FILES:
        validate_machine_info_file(file_name, errors, warnings, required=True)


def validate_manual_public_docs(errors, warnings):
    repo_root = Path(__file__).resolve().parents[1]
    for relative_path in MANUAL_PUBLIC_DOC_FILES:
        path = repo_root / relative_path
        if not path.exists():
            add_issue(warnings, relative_path, "manual public document is missing")
            continue

        content = path.read_text(encoding="utf-8")
        for pattern in DISALLOWED_MANUAL_PUBLIC_TEXT_PATTERNS:
            if pattern in content:
                add_issue(
                    errors,
                    f"{relative_path}",
                    f"contains public-policy-sensitive text: {pattern}",
                )


def validate_simulator_lineup(errors, warnings):
    repo_root = Path(__file__).resolve().parents[1]
    sim_dir = repo_root / "pachinko-sim"
    sys.path.insert(0, str(sim_dir))
    try:
        from machines import MACHINES
        from model_checks import validate_all_machine_models
        from stores import ACTIVE_OTHER_SIM_MODEL_IDS, STORE_INVENTORY
    except Exception as exc:
        add_issue(errors, "pachinko-sim", f"failed to import simulator lineup: {exc}")
        return
    finally:
        try:
            sys.path.remove(str(sim_dir))
        except ValueError:
            pass

    if len(ACTIVE_OTHER_SIM_MODEL_IDS) != 5:
        add_issue(
            errors,
            "pachinko-sim/stores.py.ACTIVE_OTHER_SIM_MODEL_IDS",
            "active non-Eva/non-DaiUmi simulator subset must stay at 5 models.",
        )

    for choice, store in STORE_INVENTORY.items():
        store_name = store.get("name", "")
        expected_rate = "1.111yen" if float(store.get("rental_rate", 0) or 0) > 1.0 else "1yen"
        rental_rate = float(store.get("rental_rate", 0) or 0)
        rental_rate_label = store.get("rental_rate_label", "")
        if rental_rate > 1.2 or "4円" in rental_rate_label or "4yen" in rental_rate_label:
            add_issue(
                errors,
                f"pachinko-sim/stores.py.STORE_INVENTORY[{choice}].rental_rate",
                "low-rate simulator stores must not be configured as 4yen machines",
            )
        for index, row in enumerate(store.get("machines", [])):
            machine = MACHINES.get(row.get("id"))
            if not machine:
                add_issue(
                    errors,
                    f"pachinko-sim/stores.py.STORE_INVENTORY[{choice}].machines[{index}]",
                    f"unknown simulator machine id: {row.get('id')}",
                )
                continue
            is_rakuen = "楽園" in store_name or "라쿠엔" in store_name
            if is_rakuen and "with アイマリン" in machine.name_ja:
                add_issue(
                    errors,
                    f"pachinko-sim/stores.py.STORE_INVENTORY[{choice}].machines[{index}]",
                    "Rakuen simulator lineup must not show with アイマリン; use 夜桜超旋風 99ver. or omit unsupported models.",
                )
            row_rate = row.get("rate", "")
            if row_rate and row_rate != expected_rate:
                add_issue(
                    errors,
                    f"pachinko-sim/stores.py.STORE_INVENTORY[{choice}].machines[{index}].rate",
                    f"simulator store rate must stay {expected_rate}, got {row_rate}",
                )
            if row.get("lineup_category") == "other" and row.get("id") not in ACTIVE_OTHER_SIM_MODEL_IDS:
                add_issue(
                    errors,
                    f"pachinko-sim/stores.py.STORE_INVENTORY[{choice}].machines[{index}].id",
                    "active other simulator model must be one of ACTIVE_OTHER_SIM_MODEL_IDS.",
                )

    for issue in validate_all_machine_models(MACHINES):
        add_issue(errors, "pachinko-sim/machines.py", issue)


def validate_private_json_fields(value, path, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{path}.{key}"
            if key in PRIVATE_PUBLIC_JSON_FIELDS:
                add_issue(
                    errors,
                    key_path,
                    "must not be stored in public GitHub data; keep personal travel details in private/ or data/manual-notes.md",
                )
            validate_private_json_fields(child, key_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_private_json_fields(child, f"{path}[{index}]", errors)


def validate_public_privacy_scan(errors, warnings):
    repo_root = Path(__file__).resolve().parents[1]
    for relative_path in PUBLIC_PRIVACY_SCAN_FILES:
        path = repo_root / relative_path
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")
        for pattern, label in PUBLIC_PRIVACY_TEXT_PATTERNS:
            if re.search(pattern, content, flags=re.IGNORECASE):
                add_issue(
                    errors,
                    relative_path,
                    f"contains possible personal travel detail: {label}",
                )

        if path.suffix == ".json":
            try:
                validate_private_json_fields(
                    json.loads(content),
                    relative_path,
                    errors,
                )
            except json.JSONDecodeError as exc:
                add_issue(errors, relative_path, f"invalid JSON: {exc}")


def tracked_files(repo_root):
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return None, str(exc)

    return [line.strip() for line in completed.stdout.splitlines() if line.strip()], None


def validate_no_tracked_garbage_artifacts(errors, warnings):
    repo_root = Path(__file__).resolve().parents[1]
    files, error = tracked_files(repo_root)
    if error:
        add_issue(warnings, "git ls-files", f"could not check tracked artifacts: {error}")
        return

    for file_name in files:
        for pattern in DISALLOWED_TRACKED_ARTIFACT_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                add_issue(
                    errors,
                    file_name,
                    "simulator/cache/database artifact must not be tracked in GitHub",
                )
                break


def report_results(errors, warnings):
    for warning in warnings:
        logger.warning(warning)
    for error in errors:
        logger.error(error)

    if errors:
        logger.error(
            f"Data validation failed: {len(errors)} errors, {len(warnings)} warnings"
        )
        return 1

    logger.info(f"Data validation passed: 0 errors, {len(warnings)} warnings")
    return 0


def main():
    errors = []
    warnings = []
    validate_machine_info(errors, warnings)
    validate_manual_public_docs(errors, warnings)
    validate_simulator_lineup(errors, warnings)
    validate_public_privacy_scan(errors, warnings)
    validate_no_tracked_garbage_artifacts(errors, warnings)
    return report_results(errors, warnings)


if __name__ == "__main__":
    sys.exit(main())
