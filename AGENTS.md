# AGENTS.md

## Project Overview

`Idle-Death-Gamble` is a personal static report generator for organizing Osaka Namba-area 1-yen pachinko store candidates and on-site decision criteria.

- **Objective Data Only**: Only objective machine and store data are stored in GitHub.
- **Dynamic Decision Making**: Visit priorities and final decisions are not fixed in the report. The user analyzes these dynamically through conversations with ChatGPT based on the latest conditions.
- **Not a Prediction Tool**: This project is not a jackpot predictor. It is a pre-visit information organization tool.

It organizes manually checked public store/spec data, applies simple rules, and publishes a mobile-friendly static report through GitHub Pages.

## GitHub Public Data Policy

Store only objective public data in GitHub:

- Store name
- Machine name
- Rate
- Machine count
- Probability
- Borderline
- Source
- Checked date

Do not store or publish dynamic decision data in GitHub:

- Visit ranking
- Recommendation score
- "Go here today" instructions
- Jackpot likelihood
- Win-rate expressions
- Raw simulator sample sessions, local `results.csv`, or accumulated simulation history
- Personal budget, actual spending, or profit/loss records
- Personal travel schedule, lodging details, transport booking identifiers, passport identifiers, or other private trip records

## Data Sources

- **DMMぱちタウン / 피타운**
  - URL: https://p-town.dmm.com/
  - 용도: 점포 정보, 설치 기종, 레이트, 설치 대수 확인
  - 주의: 台番号별 상세 데이터는 앱/대응점포/현장 확인 필요

- **ちょんぼりすた / 촌보리스타**
  - URL: https://chonborista.com/
  - 용도: 기종별 스펙, 도입일, 확률, RUSH, LT, 보더라인, 연출 정보 확인
  - 주의: 점포별 설치 대수 확인용이 아님

### 보더라인 (Borderline) 설명
- 보더라인은 기대값상 기준 회전수
- 실제 수익 보장은 아님
- 1円은 200玉당 회전수로 표시
- 楽園なんば店의 1.111円은 200円=180玉이므로 별도 환산값 사용
- 현장에서는 첫 1,000円 또는 200円 단위로 실제 회전수를 확인해야 함

예:
- 1円 보더 13.4회/200玉
- 1.111円 환산 보더 12.1회/180玉

## Repository Structure

```text
.
├── .github/workflows/ci.yml      # CI quality gate workflow
├── README.md                     # Project overview and Pages setup notes
├── requirements.txt              # Core runtime dependency placeholder
├── requirements-dev.txt          # Optional local developer tools
├── pyproject.toml                # Ruff/pytest/coverage configuration
├── data/
│   ├── stores.json               # Store list, URL targets, and machine rules
│   ├── namba-actual-1yen-lineup.json # Corrected Namba low-rate lineup
│   ├── manual-notes.md           # Optional private local memo; gitignored
│   ├── latest.json               # Generated local analysis data; gitignored
│   └── latest-report.md          # Generated local Markdown report; gitignored
├── docs/
│   ├── index.html                # GitHub Pages HTML output
│   ├── latest.json               # GitHub Pages JSON output
│   ├── latest-report.md          # GitHub Pages Markdown output
│   ├── latest-sim-results.*       # Optional latest-only public simulator aggregate table
│   ├── ai-context.md             # Generated AI usage notes
│   └── onsite-input-template.md  # Generated blank onsite observation template
├── pachinko-sim/
│   ├── main.py                   # Thin local CLI simulator entry point
│   ├── cli_context.py            # CLI lineup/result context helpers
│   ├── cli_inputs.py             # Interactive CLI input and rotation selection helpers
│   ├── cli_export.py             # Explicit public simulator export prompt
│   ├── cli_modes.py              # Interactive simulator mode orchestration
│   ├── machines.py               # Compatibility registry for simulator machine models
│   ├── machine_definitions/       # Family-split simulator machine model definitions
│   ├── machine_types.py           # Shared Machine/Payout dataclasses
│   ├── machine_templates.py       # Reusable machine-family model factories
│   ├── machine_traits.py          # Shared machine trait helpers for LT/upper-RUSH detection
│   ├── sim_terms.py               # Shared Japanese/Korean simulator terminology
│   ├── session_accounting.py      # Strategy/session policy labels and accounting helpers
│   ├── session_events.py          # Runtime hit event record builder
│   ├── session_result.py          # Final simulator result dictionary builder
│   ├── session_runtime.py         # Time-limit and spin-cap runtime helpers
│   ├── session_sampling.py        # Hit labels, payout sampling, and geometric hit wait helpers
│   ├── session_setup.py           # Initial spin/start probability and stop-loss setup helpers
│   ├── session_scenarios.py       # Matrix/budget/strategy scenario builders
│   ├── session_limits.py          # Practical stay/cash-input limit constants
│   ├── spec_benchmarks.py         # Fixed public spec benchmark values for profile checks
│   ├── start_gate.py              # Ball-to-start-spin stochastic first gate model
│   ├── time_model.py              # Play/stay time assumptions and conversion helpers
│   ├── rotation.py                # Rotation-rate, border, and rate-unit conversion helpers
│   ├── store_comparison.py        # Same-machine store comparison scenario builder
│   ├── simulator.py              # Monte Carlo session engine
│   ├── result.py                 # Compatibility exports for legacy result imports
│   ├── result_printers.py        # Public printer exports and CSV save notice
│   ├── result_basic_printers.py  # Single-run and repeated-run printer functions
│   ├── result_matrix_printers.py # Matrix, budget, profile, and strategy printer functions
│   ├── result_matrix_sections.py # Matrix printer table headers and section printers
│   ├── result_store_printers.py  # Same-machine store comparison printer function
│   ├── result_printer_common.py  # Shared printer header/context/footer helpers
│   ├── result_metrics.py          # Monte Carlo metric aggregation
│   ├── result_model_helpers.py    # Public spec benchmark and probability helper functions
│   ├── result_output_helpers.py   # Output text, rotation, and LT/upper-RUSH display helpers
│   ├── result_single_table_builders.py # Single-run event and summary table row builders
│   ├── result_repeated_table_builders.py # Repeated-run summary and risk table row builders
│   ├── result_matrix_table_builders.py # Rotation and budget matrix table row builders
│   ├── result_profile_table_builders.py # Machine profile and benchmark table row builders
│   ├── result_strategy_table_builders.py # Strategy comparison table row builders
│   ├── result_table_builders.py   # Compatibility exports for table row builders
│   ├── result_stats.py           # Pure statistical helper functions
│   ├── result_formatting.py       # Terminal table, yen, percent, and time formatting helpers
│   ├── result_csv.py              # Explicit opt-in latest-only local CSV serialization
│   ├── result_public_sections.py  # Public simulator Markdown/HTML method and analysis sections
│   ├── result_public_rendering.py # Public simulator Markdown/HTML table rendering
│   ├── result_public_export.py    # Explicit opt-in latest-only public simulator payload/files
│   ├── result_store_views.py      # Same-machine store comparison view row builders
│   ├── stores.py                 # Local simulator lineup adapter from public JSON
│   ├── model_checks.py           # Deterministic model consistency checks
│   ├── README.md                 # Simulator usage notes
│   ├── SPEC_MODELING_GUIDE.md     # DMM/official spec-to-Python modeling guide
│   ├── REFACTOR_PLAN.md           # Simulator refactor and border-input improvement plan
│   └── ARCHITECTURE.md           # Simulator design and assumptions
├── tests/
│   ├── test_simulator_specs.py   # Deterministic simulator/spec regression tests
│   ├── test_rotation.py          # Rotation, border, and rate-unit conversion tests
│   ├── test_store_comparison.py  # Same-machine store comparison view/scenario tests
│   ├── test_simulator_session.py # Simulator session, time, start-gate, and Monte Carlo tests
│   ├── test_result_metrics.py    # Metric and statistical helper tests
│   ├── test_result_compat.py     # Compatibility import tests
│   ├── test_session_accounting.py # Strategy/session accounting helper tests
│   ├── test_session_runtime.py   # Time-limit and spin-cap helper tests
│   ├── test_session_setup.py     # Initial session setup helper tests
│   ├── test_session_scenarios.py # Scenario builder compatibility tests
│   ├── test_result_table_builders.py # Result table row builder tests
│   ├── test_result_exports.py    # Latest-only CSV/public export tests
│   └── test_clean.py             # Local generated artifact cleanup tests
└── scripts/
    ├── analyze.py                # Rule-based analysis and ranking
    ├── build_report.py           # Report generation; this is the real report builder
    ├── check.py                  # Local syntax/JSON/test/validation/dev-tool check runner
    ├── clean.py                  # Dry-run by default local generated artifact cleaner
    ├── publish_sim_results.py    # Latest-only public simulator aggregate generation
    ├── validate_data.py          # Public data and simulator consistency validation
    └── utils.py                  # Shared paths, JSON/text I/O, logging, KST time
```

Use `scripts/build_report.py` as the only report generation script unless the repository structure is intentionally changed.

## Main Workflow

The normal data and report pipeline is:

1. Public store/spec pages are checked manually during an AI-assisted update, then objective fields are written to `data/namba-actual-1yen-lineup.json`.
2. `scripts/analyze.py` reads `data/namba-actual-1yen-lineup.json`, then writes `data/latest.json`.
3. `scripts/build_report.py` reads `data/latest.json` and writes:
   - `data/latest-report.md`
   - `docs/latest-report.md`
   - `docs/index.html`
   - `docs/latest.json`
   - `docs/ai-context.md`
   - `docs/onsite-input-template.md`

`docs/` is the published GitHub Pages directory.

## Local Simulator Notes

`pachinko-sim/` is a local risk comparison simulator. It must stay separate from the published report pipeline.

- `data/namba-actual-1yen-lineup.json` stores objective lineup/spec/border fields only.
- `pachinko-sim/stores.py` may derive simulator-only fields such as supported models, temporary categories, risk labels, and keep/quit guidance at runtime.
- Local simulator store choices are limited to 123難波店 1円 and 楽園なんば店 1.111円. ARROW namBa HIPS and 마루한 나니와 are comparison/reference stores only and must not become simulator store choices unless the project scope is intentionally changed.
- Keep fixed real-world data separate from simulation assumptions and results. Machine counts, public specs, rates, and borderlines are constants; CLI inputs, strategy settings, sampled outcomes, and comparison scores are runtime data.
- Use shared helpers such as `pachinko-sim/machine_traits.py` for LT and non-LT upper-RUSH detection instead of reimplementing those checks in output code.
- Treat `spins_per_1000y` as an expected field observation. The simulator may sample realized start spins through `pachinko-sim/start_gate.py`; do not convert sampled outcomes back into fixed border or lineup data.
- For same-machine store comparisons, keep `동일 1000엔 회전수`, `동일 헤소 입상 품질`, and `동일 보더 마진` as separate assumptions so 1円 and 1.111円 rates are not mixed accidentally.
- Treat store comparison as auxiliary context only. The simulator's core decision surface is machine spec, observed or assumed rotation, budget, and stop rules; store labels only carry rate, installation count, and border-conversion context.
- Do not store simulator scores, visit rankings, recommended machines, keep/quit decisions, or strategy outcomes in public `data/` files. In public `docs/`, only the explicit latest sanitized aggregate table is allowed.
- Do not accumulate simulator result history. If the user explicitly chooses CSV save in the CLI, overwrite local gitignored `results.csv` with the latest run only.
- If the user explicitly chooses public simulator sharing, overwrite only `docs/latest-sim-results.json`, `docs/latest-sim-results.md`, and `docs/latest-sim-results.html` with sanitized aggregate metrics. Do not create timestamped result files.
- Use `scripts/publish_sim_results.py` for the standard public simulator aggregate. It uses fixed per-row seeds so the same machine/budget/rotation condition can be reproduced without depending on execution order.
- The standard public aggregate should use a conservative field-like rotation assumption, currently `--field-rotation-margin 0` / `보더±0`. Keep `보더+5/+10` as sensitivity cases unless the user explicitly asks for an optimistic scenario.
- Public rotation sensitivity sections are allowed only as sanitized pre-trip assumption analysis. They must not contain actual play results, personal spending, visit instructions, or raw Monte Carlo samples.
- Public lower-tail risk review sections are allowed only as sanitized aggregate diagnostics. They may expose P10/P25 stay time, CVaR10, mean-minus-median profit gap, LT entry rate, and coarse risk labels, but not raw sessions, personal choices, or visit instructions.
- For CLI smoke runs that must not touch public `docs/`, set `PACHINKO_SIM_PUBLIC_DOCS_DIR` to a temporary directory.
- Treat Monte Carlo output as local estimate text, not as public report data or jackpot prediction.
- When changing simulator assumptions, update `pachinko-sim/ARCHITECTURE.md` and keep `pachinko-sim/README.md` aligned.
- When adding or correcting a machine model from DMM/official/product pages, follow `pachinko-sim/SPEC_MODELING_GUIDE.md`.
- Prefer reusable factories in `pachinko-sim/machine_templates.py` for machines with the same structure; add a new template only when it represents a real shared mechanic.
- When Japanese text appears in simulator output or maintained docs, include a Korean translation next to it where practical.

## Development Direction

Current near-term development should keep improving correctness, maintainability, and explainability before adding more speculative features.

- Keep `main.py` and compatibility wrappers such as `result.py` thin. Interactive mode flow belongs in `cli_*` modules; new output tables, row builders, formatting helpers, and pure statistics should move into focused helper modules when they can be tested without running the interactive CLI.
- Prefer deterministic unit tests for pure logic. For result/output helpers, use small fixed dictionaries and metric stubs rather than slow Monte Carlo runs.
- Do not add a new simulator model just because a machine name appears in a store lineup. Add or promote a model only after the public spec structure is understood well enough to encode the state transitions.
- If a model is useful but partially uncertain, mark it with conservative `confidence`, `is_estimated`, `spec_source`, and visible `notes`; do not hide uncertainty in output.
- Keep machine-family duplication low. Reuse `machine_templates.py` for repeated mechanics such as 海物語(바다이야기) loop/ST patterns, Eva V-ST patterns, or other verified shared structures.
- Keep simulation mechanics separate from presentation. Probability/state transitions belong in `simulator.py` and machine definitions; store scenario assumptions belong in `store_comparison.py`; output shaping belongs in `result_*` helper modules.
- Keep time and ball economics explicit. Net ball consumption, gross fired balls, ベース(반환), right-side spend, payout/effect time, soft stop, cash-input cutoff, and hard stop must remain separately inspectable.
- Keep same-machine store comparison rate-aware and explicitly auxiliary. Do not collapse `동일 1000엔 회전수`, `동일 헤소 입상 품질`, and `동일 보더 마진` into one generic comparison, and do not present store comparison as a store ranking.
- Use free, lightweight Python developer tools only when they add clear value. Optional tools belong in `requirements-dev.txt` and `pyproject.toml`; core runtime should remain standard-library-first unless there is a strong reason.
- Avoid broad rewrites. Make small, reviewable patches that preserve existing CLI behavior unless the user explicitly asks for a behavior change.

## Machine Modeling Workflow

When adding or correcting simulator models:

1. Verify the machine is relevant to the current low-rate scope: 1円/1.111円 in the target Namba stores, or a deliberate reference model for tests.
2. Read public machine specs from DMM, official manufacturer pages, or trusted spec sites such as ちょんぼりすた. Store only objective fields in public data.
3. Translate Japanese spec terms through `pachinko-sim/SPEC_MODELING_GUIDE.md` before editing Python distributions.
4. Choose an existing family factory when the flow matches; otherwise model directly first, then extract a template only after a second real machine shares the structure.
5. Convert `払出(지급)` to practical obtained balls only when the family has an explicit documented conversion rule. Keep that basis in `notes`.
6. Add or update public benchmark checks in `spec_benchmarks.py` when a source exposes comparable values such as 初当り(초당첨), RUSH突入(러시 진입), 継続(계속), LT, or upper-RUSH rates.
7. Add deterministic unit tests for payout weights, state names, LT vs non-LT upper RUSH, and any unusual state such as 転落(전락), 残保留(잔보류), 確変(확변), or ジンベェタイム(진베에 타임).
8. Update `pachinko-sim/ARCHITECTURE.md` and `pachinko-sim/README.md` when assumptions, modules, or user-visible metrics change.

Do not invent missing specs. If a page does not confirm a mechanic, either leave the model unsupported, keep it as a clearly marked low-confidence estimate, or ask for source confirmation.

## Python Development Guidelines

- Keep code compatible with Python 3.11 because GitHub Actions uses Python 3.11.
- Prefer dataclasses and typed helper functions for structured simulator data over untyped nested dictionaries when creating new core objects.
- Runtime dictionaries are acceptable at CLI/output boundaries, but new shared contracts should be documented by names, tests, or small typed helpers.
- Avoid circular imports between `result.py`, `result_*`, and `cli_*` helper modules. Result helpers should not import the interactive CLI.
- Keep random Monte Carlo behavior out of deterministic tests unless a fixed seed and wide tolerance are intentionally part of the test.
- Do not create local result files automatically. `results.csv` remains explicit opt-in, gitignored, and latest-only overwrite behavior.
- Preserve UTF-8 Korean/Japanese text. This repository intentionally contains bilingual user-facing output.

## Local Development Commands

Install dependencies if needed. Core analysis/report generation is standard-library-first; optional tools live in `requirements-dev.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the full local pipeline:

```bash
python scripts/validate_data.py
python scripts/analyze.py
python scripts/build_report.py
```

If the local environment does not provide `python`, use `python3` for the same commands:

```bash
python3 scripts/validate_data.py
python3 scripts/analyze.py
python3 scripts/build_report.py
```

Run only the report rebuild from existing analyzed data:

```bash
python scripts/build_report.py
```

## Data Collection Notes

There is no automated external collection script in the current pipeline. Update objective lineup/spec rows manually after checking public pages.

- Use DMM store pages for low-rate installation names, rates, and counts.
- Use DMM machine detail pages or trusted public spec pages for probability, RUSH/ST structure, and borderlines.
- Record source URLs and checked dates in `data/namba-actual-1yen-lineup.json`.
- Do not use mismatched machine specs just because a search result has a similar name.
- Do not commit raw scrape caches or per-unit 台番号(기기 번호) data.

External page access is environment-sensitive. A `403 Forbidden` can be caused by proxy, network, CDN, or anti-bot behavior in the execution environment. Do not assume a `403` is automatically a code bug.

A `404 Not Found` usually means the stored URL changed, is stale, or has a typo. Check `data/stores.json` first when a store URL returns `404`.

## Machine Info Source Notes

This project is not an automated per-unit 台データ(기기별 데이터) collector.

Current scope:

- P-WORLD/DMM/minpachi links are used only for store links, basic status, machine-installation hints, business-hour hints, and notice confirmation.
- Corrected Namba low-rate 機種情報 (machine/spec info) lives in `data/namba-actual-1yen-lineup.json`.
- `data/namba-actual-1yen-lineup.json` is a low-rate file. Do not mix 4円 machines into it; Rakuen rows use `1.111yen`, while 123 Namba and ARROW namBa HIPS rows use `1yen`. Simulator selection remains limited to 123 Namba and Rakuen rows; HIPS rows are report/reference context.
- The report uses manually checked fields such as store, machine name, 1円(1엔) status, category, 初当り確率(초당첨 확률), RUSH(러시) type, RUSH突入率(러시 진입률), RUSH継続率(러시 계속률), payout feature, source type, checked date, and memo.
- 台番号(기기 번호)별 大当り(대당첨), 総回転(총 회전수), 差玉(구슬 수 증감), and スランプグラフ(구슬 수 추이 그래프) are out of scope.
- App-only provider crawling, login/session handling, VPN-dependent scraping, and jackpot/payout prediction are out of scope.

Provider access is not uniform. Some links open as normal web pages, while others may require a browser session, mobile app, JavaScript, cookies, or membership flow. A CLI `403` from a provider URL should be recorded as an access condition, not treated as proof that the URL is invalid. A `404` should still be treated as a likely moved or mistyped URL.

Do not add automated 台データ(기기별 데이터) collection unless the project scope is intentionally changed.

## Report Build Notes

`scripts/build_report.py` is the real report generation script. It builds Markdown and HTML from `data/latest.json`.

Important outputs:

- `data/latest-report.md` is the data-side Markdown copy.
- `docs/latest-report.md` is the published Markdown copy.
- `docs/index.html` is the main GitHub Pages page.
- `docs/latest.json` is the published JSON data.
- `docs/ai-context.md` is the generated AI usage note.
- `docs/onsite-input-template.md` is the generated blank onsite observation template.

If `data/latest.json` is empty or missing, `build_report.py` logs an error and aborts. Run `scripts/analyze.py` before `scripts/build_report.py` when ranking data must be regenerated.

## GitHub Actions and Pages

The active workflow is `.github/workflows/ci.yml`.

Current workflow behavior:

- Runs on `ubuntu-latest`.
- Uses Python `3.11`.
- Runs on push, pull request, and manual `workflow_dispatch`.
- Runs `python scripts/check.py`.
- Does not collect external data and does not commit generated `docs/` changes back to `main`.

GitHub Pages is configured to publish from:

- Branch: `main`
- Folder: `/docs`

Published URL:

```text
https://khskyasu-maker.github.io/Idle-Death-Gamble/
```

## Store URL Maintenance

Store URLs live in `data/stores.json` under each store's `links` object.

Reference data URLs may still live in the same store object under `machine_data.sources`, but they are not crawled for per-unit data. Keep each source annotated with:

- `provider`
- `kind`
- `url`
- `access_status`
- `notes`

Keep store `id` values stable unless a migration is intentionally planned, because collected and analyzed data are keyed by store ID.

Known current URL rule:

```text
ARROW namBa HIPS P-WORLD:
https://www.p-world.co.jp/osaka/arrow-nanba-hips.htm
```

If a P-WORLD or Minpachi URL starts returning `404`, verify the latest public URL and update `data/stores.json`. If the response is `403`, first consider environment/network blocking before changing code.

Blank URLs are allowed and are recorded as `skipped` with `No URL`.

## Testing Checklist

Before finishing changes, run the checks that match the change scope.

Preferred full local check:

```bash
python scripts/check.py
```

Optional developer-tool check when `.venv` has `requirements-dev.txt` installed:

```bash
python scripts/check.py --dev-tools --coverage
```

Local generated artifact check:

```bash
python scripts/clean.py
```

Local generated artifact cleanup:

```bash
python scripts/clean.py --apply
```

Equivalent manual syntax check:

```bash
python -m py_compile scripts/analyze.py scripts/build_report.py scripts/check.py scripts/clean.py scripts/validate_data.py scripts/utils.py scripts/term_notes.py pachinko-sim/main.py pachinko-sim/cli_context.py pachinko-sim/cli_inputs.py pachinko-sim/cli_export.py pachinko-sim/cli_modes.py pachinko-sim/machines.py pachinko-sim/machine_definitions/__init__.py pachinko-sim/machine_definitions/sea.py pachinko-sim/machine_definitions/eva.py pachinko-sim/machine_definitions/rezero.py pachinko-sim/machine_definitions/other.py pachinko-sim/machine_types.py pachinko-sim/machine_templates.py pachinko-sim/machine_traits.py pachinko-sim/sim_terms.py pachinko-sim/session_accounting.py pachinko-sim/session_events.py pachinko-sim/session_result.py pachinko-sim/session_runtime.py pachinko-sim/session_sampling.py pachinko-sim/session_setup.py pachinko-sim/session_scenarios.py pachinko-sim/session_limits.py pachinko-sim/spec_benchmarks.py pachinko-sim/start_gate.py pachinko-sim/time_model.py pachinko-sim/rotation.py pachinko-sim/store_comparison.py pachinko-sim/model_checks.py pachinko-sim/result.py pachinko-sim/result_printers.py pachinko-sim/result_basic_printers.py pachinko-sim/result_matrix_printers.py pachinko-sim/result_matrix_sections.py pachinko-sim/result_store_printers.py pachinko-sim/result_printer_common.py pachinko-sim/result_metrics.py pachinko-sim/result_model_helpers.py pachinko-sim/result_output_helpers.py pachinko-sim/result_single_table_builders.py pachinko-sim/result_repeated_table_builders.py pachinko-sim/result_matrix_table_builders.py pachinko-sim/result_profile_table_builders.py pachinko-sim/result_strategy_table_builders.py pachinko-sim/result_table_builders.py pachinko-sim/result_stats.py pachinko-sim/result_formatting.py pachinko-sim/result_csv.py pachinko-sim/result_public_sections.py pachinko-sim/result_public_rendering.py pachinko-sim/result_public_export.py pachinko-sim/result_store_views.py pachinko-sim/simulator.py pachinko-sim/stores.py tests/test_simulator_specs.py tests/test_rotation.py tests/test_store_comparison.py tests/test_simulator_session.py tests/test_result_metrics.py tests/test_session_accounting.py tests/test_session_runtime.py tests/test_session_setup.py tests/test_session_scenarios.py tests/test_result_compat.py tests/test_result_table_builders.py tests/test_result_exports.py tests/test_validate_data.py tests/test_clean.py
```

JSON validation:

```bash
python -m json.tool data/stores.json > /dev/null
python -m json.tool data/namba-actual-1yen-lineup.json > /dev/null
python -m json.tool data/latest.json > /dev/null
python -m json.tool docs/latest-sim-results.json > /dev/null
```

Unit tests:

```bash
python -m unittest discover -s tests
```

Report regeneration check:

```bash
python scripts/validate_data.py
python scripts/analyze.py
python scripts/build_report.py
```

Use `python3` instead of `python` if required by the local machine.

For URL fixes, verify the old and new URLs separately when possible:

```bash
curl -I --max-time 15 <url>
```

## Rules for AI Agents / Codex

- Inspect the repository structure and relevant files before editing.
- Prefer small, focused changes that match the existing simple Python/static-site architecture.
- Do not add external AI APIs, prediction systems, or aggressive scraping behavior.
- Do not rename or replace the main pipeline scripts without updating the workflow and this file.
- Use `scripts/build_report.py` for report generation; do not assume another report generator exists.
- Treat `data/stores.json` as the source of truth for store URLs and objective machine focus rules.
- Treat `data/namba-actual-1yen-lineup.json` as public objective lineup/spec data. Do not add simulator-derived fields such as `sim_supported`, `sim_model_key`, `risk_level`, `first_test_budget`, `keep_condition`, or `quit_condition`.
- Keep 1円/1.111円 simulator candidates separate from 4円 machines. If a source page mixes rates, verify the row's rate before adding it to the low-rate lineup.
- Keep simulator-derived guidance in `pachinko-sim/stores.py` or runtime CLI output, not in public JSON outputs.
- Simulator verification output should expose practical inputs such as 1,000円당 회전수, 예산별 당첨률, 평균 大当り(아타리), 평균 연속, RUSH/LT, 평균 체류 시간, 1~9시간 도달률, 9시간 이후 RUSH 종료 정리율, 11시간 하드 종료율, 최종 잔류액, 예산 소진 후 지속 시간, 완전 소진 정지율, 현금 없이 이어진 시간, and public Japanese spec benchmark differences.
- In simulator output, display LT as `해당없음` for non-LT machines. Use `0%` only when the model actually has an LT path and the simulated entry rate is zero. Keep non-LT upper RUSH metrics separate from LT.
- Treat `docs/` as generated Pages output, not as a separate hand-maintained app.
- AI helper files in `docs/` must stay generic and blank. Do not write actual onsite observations, personal movement, budget, or spending notes into generated public files.
- When changing report logic, update generated `data/` and `docs/` outputs as needed.
- When public page access fails because of `403`, treat it as an access condition and avoid replacing verified data with all-failure results unless explicitly requested.
- When URLs fail with `404`, check for store URL changes or typos first.
- Keep `data/manual-notes.md` local/private. Do not commit sensitive travel details, screenshots, app/member data, or spending/profit notes.
- Keep private trip files under gitignored paths such as `private/`, `data/manual-notes.md`, or `data/travel-*`. Public `data/` and `docs/` files must stay objective and non-personal.
- Preserve UTF-8 content; this repository intentionally contains Korean and Japanese text.
- Keep GitHub Actions compatible with Python 3.11 and the dependencies in `requirements.txt`.
