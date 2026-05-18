# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Idle-Death-Gamble** is a personal static report generator for organizing Osaka Namba 1-yen pachinko store candidates and on-site decision criteria. It does not predict jackpots or publish visit rankings.

The project consists of two primary subsystems:

1. **Report Pipeline** (`scripts/`): Collects store/machine data from public sources, validates, analyzes, and generates static HTML/JSON/Markdown reports published via GitHub Pages.
2. **Pachinko Simulator** (`pachinko-sim/`): A local Monte Carlo risk comparison tool for the same machines. Output is optional, latest-only, and explicitly user-approved before public export.

**Critical Policy**: Only objective data (store name, machine name, rate, machine count, probability, borderline, source, checked date) is committed to GitHub. Personal budgets, spending records, visit decisions, travel schedules, and raw simulation samples are never published.

## Key Commands

All commands assume Python 3.11+ and use `python` (or `python3` if `python` is unavailable).

### Development & Validation

```bash
# Install dependencies (do this once)
pip install -r requirements.txt

# Run core checks without web scraping (unit tests, JSON validation, data validation)
python scripts/check.py

# Install optional dev tools and run linting + tests
pip install -r requirements-dev.txt
python scripts/check.py --dev-tools

# Run test coverage
python scripts/check.py --coverage

# Run specific test
python -m unittest tests.test_simulator_specs.TestMachineSpecs.test_example_name
```

### Data Pipeline (Manual/GitHub Actions)

```bash
# Validate data integrity (JSON syntax, privacy rules, machine specs)
python scripts/validate_data.py

# Collect store/machine data from configured DMM source (slow, ~seconds per store)
python scripts/collect.py

# Analyze collected data and generate data/latest.json
python scripts/analyze.py

# Build static reports (HTML/JSON/Markdown) into docs/ folder
python scripts/build_report.py

# Full pipeline with validation
python scripts/check.py --report
```

### Report Generation with Cache Cleanup

```bash
# Show what would be deleted (cache, old sim results, generated files)
python scripts/clean.py

# Actually delete cache and old files
python scripts/clean.py --apply
```

### Simulator (Interactive CLI)

```bash
# Run interactive pachinko simulator
cd pachinko-sim && python main.py

# Or from root with module path
PYTHONPATH=pachinko-sim python pachinko-sim/main.py
```

### Public Simulator Export

After running a simulation interactively, the CLI prompts to save results publicly. This command rebuilds the latest-only public simulator export:

```bash
# Regenerate docs/latest-sim-results.{json,md,html} from current session
python scripts/publish_sim_results.py

# Update a single machine's results and merge with existing public export
python scripts/publish_sim_results.py --machine-id oki_sea_5_yozakura_99 --merge-existing
```

### Code Quality

```bash
# Lint all Python files (Ruff)
python -m ruff check .

# Format code (Ruff format mode)
python -m ruff format .

# Run unit tests
python -m unittest discover -s tests

# Test a specific module
python -m unittest tests.test_simulator_specs
```

## Architecture & Data Flow

### Report Pipeline (`scripts/`)

```
data/namba-actual-1yen-lineup.json (fixed machine/store lineup)
  ↓
scripts/collect.py (scrapes DMM, adds to data/collected.json cache)
  ↓
scripts/analyze.py (processes lineup + cache, generates data/latest.json)
  ↓
scripts/build_report.py (templates data/latest.json into docs/index.html, etc.)
  ↓
docs/latest.json, docs/index.html, docs/latest-report.md (published via GitHub Pages)
```

**Key Principles**:
- `data/namba-actual-1yen-lineup.json` is the source of truth for store/machine/rate/border data.
- `scripts/collect.py` respects robots.txt and includes transient error retry logic; it does not use external AI APIs or aggressive scraping.
- `scripts/validate_data.py` enforces privacy: blocks travel schedules, booking IDs, passport data, and personal spending records from being committed.
- Local generated data (`data/latest.json`, `data/latest-report.md`) and caches (`data/collected.json`) are gitignored by default.
- Public simulator exports use only latest fixed filenames (`docs/latest-sim-results.*`) and may be committed only after explicit sharing.

### Simulator (`pachinko-sim/`)

High-level flow:

```
stores.py (load data/namba-actual-1yen-lineup.json, build lineup objects)
  ↓
machine_definitions/ + machines.py (fixed machine specs, exposed through compatibility wrapper)
  ↓
rotation.py (normalize observed rotation, borderline scenarios, rate unit conversion)
  ↓
start_gate.py (model ball→start-spin stochastic first gate)
  ↓
time_model.py (estimate play/stay time from balls and state spins)
  ↓
simulator.py + session_* helpers (run Monte Carlo sessions and scenario matrices)
  ↓
result_metrics.py (calculate aggregates: profit, hit rate, stay time, etc.)
  ↓
result_*_printers.py (format results for CLI output)
  ↓
cli_modes.py + cli_export.py (interactive mode orchestration, explicit public export prompt)
```

**Core Abstractions**:

- **`Machine`** (machine_types.py): id, name, probabilities, hit distributions by state, right-side ball loss, spec metadata.
- **`Payout`**: nominal balls won, weight, next state transition, optional jitan/lt entry counts.
- **`RotationEstimate`** (rotation.py): preserves input basis (1000円, 200玉, 250玉, observed cash, border margin) so output can explain conversion.
- **Stores** (stores.py): Maps DMM lineup → simulator machine IDs, tracks installed/unsupported machines, converts borders to `spins_per_1000yen`.
- **Session** (`simulator.py` + `session_accounting.py` + `session_runtime.py`): Monte Carlo state, cash budget, rented balls, card reuse, exchange rate, 9-hour soft stop, 11-hour hard cap, and strategy accounting.

**Important Simulator Constraints**:
- Borderline does NOT change jackpot probability. It only bounds the table-quality rotation distribution and indexes default scenario cases (e.g., `보더-5/±0/+5`).
- Exchange lot size, leftover ball handling, 台番号 per-unit data, and actual jackpot history are NOT modeled.
- Start-entry variance is modeled as binomial (fired balls → start spins), not exact nail physics.
- Payout variance is truncated normal around nominal balls, not exact round/count/award formulas.

### Data Privacy & Public Export

**What is committed:**
- `data/namba-actual-1yen-lineup.json`: store names, machine names, rates, machine counts, probabilities, borderlines, sources.
- `docs/*.md`, `docs/*.html`, `docs/*.json`: static mobile-friendly reports, AI context, onsite-input templates, latest-only simulator results.

**What is gitignored (private/local only)**:
- `data/collected.json`: raw DMM scrape cache.
- `data/latest.json`, `data/latest-report.md`: local analysis cache.
- `data/manual-notes.md`: local private memo.
- `results.csv`: raw simulator session samples.
- `docs/sim-results-*.json` (timestamped history): only latest is public.
- `private/`: travel plans, bookings, spending records.

**Public Simulator Export**:
- `docs/latest-sim-results.json/md/html` are latest-only, explicit-share-only.
- Must include uncertainty (confidence intervals, standard error) so Monte Carlo variance is visible.
- Must NOT include visit rankings, personal budget, session logs, or raw sample sessions.

## Modules & Responsibilities

### Report Scripts

- **`check.py`**: Quality gate orchestrator. Runs syntax, JSON validation, unit tests, data validation, and optional linting/coverage.
- **`collect.py`**: Scrapes DMM store pages, respects robots.txt, retries transient errors, caches results in `data/collected.json`.
- **`analyze.py`**: Loads `namba-actual-1yen-lineup.json`, merges collected data, computes store/category/border totals, generates `data/latest.json`.
- **`build_report.py`**: Templates `data/latest.json` into HTML/Markdown/JSON reports for GitHub Pages, generates AI context files.
- **`validate_data.py`**: Regex-based privacy validation (blocks travel dates, booking IDs, passport data, spending records).
- **`clean.py`**: Removes cache and old generated files on demand.
- **`publish_sim_results.py`**: Rebuilds or updates `docs/latest-sim-results.*` from latest simulator session.
- **`utils.py`**: Shared logging, path helpers, JSON I/O, timezone helpers.
- **`term_notes.py`**: Japanese-term annotation helpers.

### Simulator Modules (pachinko-sim/)

- **`machines.py`**: Thin compatibility wrapper that exposes `MACHINES`, `Machine`, and `Payout`.
- **`machine_definitions/`**: Fixed machine spec database split by family (`sea.py`, `eva.py`, `rezero.py`, `other.py`). Use `SPEC_MODELING_GUIDE.md` when adding models.
- **`machine_types.py`**: Dataclasses for `Machine`, `Payout`, shared machine specs.
- **`machine_templates.py`**: Reusable machine-family factories (e.g., Eva breakthrough ST, Sea kakuhen loop).
- **`machine_traits.py`**: Shared helpers to iterate payouts, detect LT, detect non-LT upper RUSH.
- **`stores.py`**: Load `data/namba-actual-1yen-lineup.json`, map DMM names to sim IDs, track installed/unsupported, convert borders.
- **`rotation.py`**: Normalize observed rotation (1000円, 200玉, 250玉, cash), preserve input basis, build border-relative scenarios (±5/-10).
- **`start_gate.py`**: Model fired balls → start spins (binomial), sample table-quality rotation variance (truncated normal).
- **`time_model.py`**: Convert spins/balls → play time. Fixed assumptions: 100 balls/min launch, 6s/normal start, family-specific right-side speed and effect time.
- **`sim_terms.py`**: Bilingual state labels (Japanese + Korean).
- **`spec_benchmarks.py`**: Fixed public spec values used in profile output and benchmark comparison rows.
- **`session_accounting.py`**: Strategy names, policy names, profit conversion, and lock/exit rules.
- **`session_runtime.py`**: Session time-limit conversion and spin capping helpers.
- **`session_scenarios.py`**: Rotation, budget, and strategy matrix builders. `simulator.py` keeps wrappers for legacy imports.
- **`simulator.py`**: Monte Carlo engine and state machine (NORMAL, ST, JITAN, KAKUBEN, LT, UPPER, JINBEE, etc.).
- **`store_comparison.py`**: Build same-machine, same-state store comparison scenarios. Handles 1円/1.111円 rate conversions (cash_rotation, ball_quality, border_margin assumptions).
- **`model_checks.py`**: Deterministic model validation (no-hit rates, state continuity, payout weights, metadata).
- **`result.py`**: Compatibility export wrapper.
- **`result_metrics.py`**: Pure calculation: profit, hit rate, stay time, cash exhaustion, condition rows.
- **`result_stats.py`**: Monte Carlo uncertainty: Wilson intervals, quantile intervals, CVaR10, tail means.
- **`result_output_helpers.py`**: Output text, benchmark rows, LT/upper-RUSH labels, borderline warnings.
- **`result_table_builders.py`**: Reusable row builders (single, repeated, matrix, budget, profile, strategy tables).
- **`result_formatting.py`**: Terminal width, yen/percent/minute text, ASCII bars.
- **`result_csv.py`**: Latest-only matrix CSV serialization.
- **`result_public_export.py`**: Sanitized JSON/Markdown/HTML export with uncertainty labels.
- **`result_basic_printers.py`**: Single-session and repeated-session output.
- **`result_matrix_printers.py`**: Rotation/budget/profile/strategy matrix output.
- **`result_matrix_sections.py`**: Matrix table headers and section helpers.
- **`result_store_printers.py`**: Store comparison output.
- **`result_store_views.py`**: Store comparison table assembly.
- **`result_printer_common.py`**: Shared header/context/footer helpers.
- **`result_printers.py`**: Public printer API reexport.
- **`cli_modes.py`**: Interactive mode orchestration (single, repeated, matrix, store comparison, profile).
- **`cli_inputs.py`**: Interactive rotation/budget/strategy input helpers.
- **`cli_context.py`**: CLI lineup/result context helpers.
- **`cli_export.py`**: Explicit public export prompt and confirmation.
- **`main.py`**: Thin entry point; calls `run_cli()` from `cli_modes.py`.

### Tests

- **`test_simulator_specs.py`**: Deterministic machine model checks (no-hit rate, state transitions, payout weights).
- **`test_result_exports.py`**: Public export format validation, structure checks.
- **`test_result_compat.py`**: Backward-compatibility for result module imports.
- **`test_result_table_builders.py`**: Row builder logic.
- **`test_clean.py`**: Cache cleanup dry-run and apply logic.

## Key Conventions & Non-obvious Patterns

### Rotation & Borderline Model

1. **Internal unit**: All rotations are stored as `spins_per_1000yen`.
2. **Input normalization** (rotation.py):
   - `17.5회/250玉` → `17.5 * 4 = 70회/1000엔`
   - `14회/180玉` (1.111円) → `14 * 5 = 70회/1000엔`
   - Cash observations + rate converted via lend rate.
3. **Border policy**: Borderline does NOT change jackpot probability. It is a rotation reference line used to:
   - Index scenario cases: `보더-5`, `보더±0`, `보더+5`, etc.
   - Bound table-quality variance in `start_gate.py`.
   - Provide comparison context in output.
4. **Rate conversion**: 1円 rents 1000 balls/1000円; 1.111円 rents 900 balls/1000円. When comparing rates, use `cash_rotation` (same observed spins), `ball_quality` (same entry probability), or `border_margin` (same margin against each rate's border).

### Machine Model Policy

- **`high` confidence**: Individual public spec checked against real machine.
- **`medium` confidence**: Major structure modeled but some split/reserve/provider details estimated.
- **`low` confidence**: Rough temporary model; ranking should be capped or treated as observation only.
- **Payout `balls`**: Practical budgeting value. When public source shows only `払出`, model uses ~93% obtained-ball approximation (conversion basis must be visible in `notes`).
- **Selectable machines**: `MACHINE_NAME_TO_SIM_ID` in `stores.py` is the active subset; unsupported models remain in `machine_definitions/` for reference/test only.

### Session & Strategy Semantics

- **`session_policy="fixed_spin_cap"`**: Normal spins capped at `budget / 1000 * spins_per_1000y` (historical behavior).
- **`session_policy="play_until_budget_and_balls_gone"`**: Reusable balls extend normal play until cash + balls both gone.
- **9-hour soft stop**: In normal play, stop near 9 hours; if in RUSH/時短/確変, continue until right-side state returns.
- **11-hour hard cap**: Safety bound so rare positive loops don't run indefinitely.
- **Strategies**: `no_rule`, `basic_stop` (first-1000円 probe with threshold), `profit_lock` (lock balls when positive), and `aggressive` (redeploy while locking excess balls).

### Output Uncertainty

- All Monte Carlo results include uncertainty (confidence intervals, standard error, quantile intervals).
- Hit rate, RUSH/LT rate, positive-close rate, and no-hit rate use Wilson intervals.
- Median profit, lower-10%, upper-10% quantiles use rank-based 95% intervals.
- Mean profit uses t-based (small samples) or normal limit (large samples).
- Standard error shown as absolute yen and % of budget to assess Monte Carlo precision.
- Denominator-tail display shows normal-probability no-hit exceeding 1x/2x/3x the denominator under independent trials.

### Publication Pipeline Safety

- Explicit user confirmation required before any `docs/latest-sim-results.*` export.
- Privacy validation in `validate_data.py` blocks specific patterns: travel dates, booking IDs, passport data, spending records.
- `.gitignore` enforces: raw samples (`results.csv`), local analysis (`data/latest.json`), private notes (`data/manual-notes.md`), timestamped simulator history.
- Latest-only export rule: `docs/sim-results-*.json` and `docs/simulator-results-*.json` are forbidden; only `latest-sim-results.*` allowed.

## Testing & Quality Gates

**Test Discovery**:
```bash
# Find and run all tests
python -m unittest discover -s tests

# Run a specific test class
python -m unittest tests.test_simulator_specs.TestMachineSpecs

# Run a specific test method
python -m unittest tests.test_simulator_specs.TestMachineSpecs.test_machine_confidence_levels
```

**Continuous Integration**:
- `.github/workflows/ci.yml`: Runs on push/PR/workflow_dispatch. Installs dependencies, runs `python scripts/check.py`.
- `.github/workflows/daily.yml`: Manual workflow_dispatch only. Runs full pipeline (check → collect → analyze → build_report), commits results to docs/.

**Quality Gate** (`scripts/check.py`):
1. Python syntax check (py_compile).
2. JSON validation (utf-8 decode, valid JSON structure).
3. Unit tests (unittest discover).
4. Data validation (`scripts/validate_data.py` privacy checks).
5. Clean dry-run (`scripts/clean.py` with no --apply).
6. Optional: ruff lint/format, pytest, coverage.

## Common Development Scenarios

### Adding a New Machine Model

1. Read `pachinko-sim/SPEC_MODELING_GUIDE.md` for public-source-to-model mapping rules.
2. Add `Machine` definition in the matching `pachinko-sim/machine_definitions/` family file, or create a factory in `machine_templates.py` if it's a family variant.
3. Ensure `spec_source`, `confidence`, and `is_estimated` are set correctly.
4. If a reusable family, add a factory function in `machine_templates.py` and parameterize from the matching `machine_definitions/` file.
5. Add machine to `MACHINE_NAME_TO_SIM_ID` mapping in `stores.py` if selectable, or leave as reference-only.
6. Run `python -m unittest tests.test_simulator_specs` to validate payouts and state transitions.

### Updating Machine Spec (Probability, Border, Payout)

1. Check if the machine is in `stores.py` `MACHINE_NAME_TO_SIM_ID` (selectable) or reference-only.
2. Update the matching `machine_definitions/` file with new probability, border, or payout distribution.
3. If using borderline comparison, update `spec_benchmarks.py` if the public spec changed.
4. Run `python scripts/validate_data.py` and `python -m unittest tests.test_simulator_specs` to confirm no validation errors.
5. If selectable and public-facing, consider running `python scripts/publish_sim_results.py --machine-id <id> --merge-existing` to update the public result table.

### Adding a New Store or Updating Lineup

1. Update `data/namba-actual-1yen-lineup.json` with new store or machine records.
2. Ensure store_id, machine_name, rate, machine_count, initial_probability, borderline, and source are present.
3. Run `python scripts/validate_data.py` to check privacy and syntax.
4. Run `python scripts/check.py --report` to regenerate reports.

### Debugging a Simulator Session

1. Run `cd pachinko-sim && python main.py` and select "single session" mode.
2. Inspect the session output for hit count, stay time, no-hit rate, and profit distribution.
3. If the result seems off, check `simulator.py` state transitions and payout sampling logic.
4. For strategy/profit-lock issues, check `session_accounting.py`.
5. For time-limit or cash-cutoff issues, check `session_runtime.py`.
6. For table-quality variance issues, check `start_gate.py` truncated normal distribution and borderline bounds.
7. For time estimate issues, check `time_model.py` balls-per-minute and state-specific second-per-spin assumptions.

### Viewing Public Data

- `docs/latest.json`: Full structured machine/store data for AI and web consumption.
- `docs/ai-context.md`: Field descriptions and AI usage rules.
- `docs/simulator-ai-context.md`: Simulator output semantic guide for AI interpretation.
- `docs/onsite-input-template.md`: Blank observation form for on-site input collection.
- `docs/latest-sim-results.json/md/html`: Latest-only public simulator aggregate table (if published).

## Git & Deployment

**Branches**: main is the primary branch. Public reports in `docs/` are published via GitHub Pages.

**Workflows**:
- **CI (ci.yml)**: Runs on every push, PR, and manual dispatch. Validates code/data quality.
- **Manual Report (daily.yml)**: Requires manual workflow_dispatch. Scrapes fresh data and publishes reports.

**Commits**: Use descriptive messages. Auto-generated reports should note "manual pachinko report" or "simulator aggregate update".

## References

- **README.md**: Project overview, data policy, execution instructions.
- **AGENTS.md**: AI agent context (what AI is allowed to know/do).
- **pachinko-sim/ARCHITECTURE.md**: Detailed simulator architecture, data flow, module roles, statistical policy.
- **pachinko-sim/SPEC_MODELING_GUIDE.md**: Machine spec source-to-model mapping rules and conversion basis.
- **pachinko-sim/README.md**: Simulator user guide, interactive mode instructions.
- **pachinko-sim/REFACTOR_PLAN.md**: Planned improvements to rotation/border/rate unit handling.
