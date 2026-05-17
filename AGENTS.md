# AGENTS.md

## Project Overview

`Idle-Death-Gamble` is a personal static report generator for organizing Osaka Namba-area 1-yen pachinko store candidates and on-site decision criteria.

- **Objective Data Only**: Only objective machine and store data are stored in GitHub.
- **Dynamic Decision Making**: Visit priorities and final decisions are not fixed in the report. The user analyzes these dynamically through conversations with ChatGPT based on the latest conditions.
- **Not a Prediction Tool**: This project is not a jackpot predictor. It is a pre-visit information organization tool.

It collects a small set of public store pages, applies simple rules, and publishes a mobile-friendly static report through GitHub Pages.

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
├── .github/workflows/daily.yml   # Manual GitHub Actions workflow
├── README.md                     # Project overview and Pages setup notes
├── requirements.txt              # Python dependencies
├── data/
│   ├── stores.json               # Store list, URL targets, and machine rules
│   ├── namba-actual-1yen-lineup.json # Corrected Namba low-rate lineup
│   ├── collected.json            # Generated local cache; gitignored
│   ├── manual-notes.md           # Optional private local memo; gitignored
│   ├── latest.json               # Generated local analysis data; gitignored
│   └── latest-report.md          # Generated local Markdown report; gitignored
├── docs/
│   ├── index.html                # GitHub Pages HTML output
│   ├── latest.json               # GitHub Pages JSON output
│   ├── latest-report.md          # GitHub Pages Markdown output
│   ├── ai-context.md             # Generated AI usage notes
│   └── onsite-input-template.md  # Generated blank onsite observation template
├── pachinko-sim/
│   ├── main.py                   # Local CLI simulator entry point
│   ├── machines.py               # Simulator machine models and payout distributions
│   ├── machine_traits.py          # Shared machine trait helpers for LT/upper-RUSH detection
│   ├── sim_terms.py               # Shared Japanese/Korean simulator terminology
│   ├── session_limits.py          # Practical stay/cash-input limit constants
│   ├── spec_benchmarks.py         # Fixed public spec benchmark values for profile checks
│   ├── start_gate.py              # Ball-to-start-spin stochastic first gate model
│   ├── time_model.py              # Play/stay time assumptions and conversion helpers
│   ├── rotation.py                # Rotation-rate, border, and rate-unit conversion helpers
│   ├── store_comparison.py        # Same-machine store comparison scenario builder
│   ├── simulator.py              # Monte Carlo session engine
│   ├── result.py                 # ASCII output, metrics, and CSV append helper
│   ├── stores.py                 # Local simulator lineup adapter from public JSON
│   ├── model_checks.py           # Deterministic model consistency checks
│   ├── README.md                 # Simulator usage notes
│   ├── REFACTOR_PLAN.md           # Simulator refactor and border-input improvement plan
│   └── ARCHITECTURE.md           # Simulator design and assumptions
├── tests/
│   └── test_simulator_specs.py   # Deterministic simulator/spec regression tests
└── scripts/
    ├── collect.py                # External page collection
    ├── analyze.py                # Rule-based analysis and ranking
    ├── build_report.py           # Report generation; this is the real report builder
    ├── validate_data.py          # Public data and simulator consistency validation
    └── utils.py                  # Shared paths, JSON/text I/O, logging, KST time
```

Use `scripts/build_report.py` as the only report generation script unless the repository structure is intentionally changed.

## Main Workflow

The normal data and report pipeline is:

1. `scripts/collect.py` reads `data/stores.json` and updates `data/collected.json`.
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
- Keep fixed real-world data separate from simulation assumptions and results. Machine counts, public specs, rates, and borderlines are constants; CLI inputs, strategy settings, sampled outcomes, and comparison scores are runtime data.
- Use shared helpers such as `pachinko-sim/machine_traits.py` for LT and non-LT upper-RUSH detection instead of reimplementing those checks in output code.
- Treat `spins_per_1000y` as an expected field observation. The simulator may sample realized start spins through `pachinko-sim/start_gate.py`; do not convert sampled outcomes back into fixed border or lineup data.
- For same-machine store comparisons, keep `동일 1000엔 회전수`, `동일 헤소 입상 품질`, and `동일 보더 마진` as separate assumptions so 1円 and 1.111円 rates are not mixed accidentally.
- Do not store simulator scores, visit rankings, recommended machines, keep/quit decisions, or strategy outcomes in public `data/` or `docs/` files.
- Do not auto-create or overwrite `results.csv`; append only when the user explicitly chooses CSV save in the CLI.
- Treat Monte Carlo output as local estimate text, not as public report data or jackpot prediction.
- When changing simulator assumptions, update `pachinko-sim/ARCHITECTURE.md` and keep `pachinko-sim/README.md` aligned.
- When Japanese text appears in simulator output or maintained docs, include a Korean translation next to it where practical.

## Local Development Commands

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the full local pipeline:

```bash
python scripts/collect.py
python scripts/analyze.py
python scripts/build_report.py
```

If the local environment does not provide `python`, use `python3` for the same commands:

```bash
python3 scripts/collect.py
python3 scripts/analyze.py
python3 scripts/build_report.py
```

Run only the report rebuild from existing analyzed data:

```bash
python scripts/build_report.py
```

## Data Collection Notes

`scripts/collect.py`:

- Loads store definitions from `data/stores.json`.
- Preserves and updates local `data/collected.json` incrementally. This file is gitignored in the public repository.
- Checks `robots.txt` before scraping when possible.
- Uses a browser-like user agent.
- Limits a run to `MAX_URLS_PER_RUN = 10`.
- Sleeps randomly between requests.
- Treats `401`, `403`, and `429` as `blocked_or_limited`.
- Retries once after request exceptions.
- Preserves existing successful data for the same URL when a later attempt fails due to transient network, proxy, DNS, timeout, rate-limit, or CAPTCHA-like blocking. The preserved entry records `last_attempt_status`, `last_attempt_error_type`, and `last_attempt_at`.

External collection is environment-sensitive. A `403 Forbidden` can be caused by proxy, network, CDN, or anti-bot behavior in the execution environment. Do not assume a `403` is automatically a code bug.

A `404 Not Found` usually means the stored URL changed, is stale, or has a typo. Check `data/stores.json` first when a store URL returns `404`.

Do not commit `data/collected.json` unless the project intentionally changes to publish collected raw cache data.

## Machine Info Source Notes

This project is not an automated per-unit 台データ(기기별 데이터) collector.

Current scope:

- P-WORLD/DMM/minpachi links are used only for store links, basic status, machine-installation hints, business-hour hints, and notice confirmation.
- Corrected Namba low-rate 機種情報 (machine/spec info) lives in `data/namba-actual-1yen-lineup.json`.
- `data/namba-actual-1yen-lineup.json` is a low-rate file. Do not mix 4円 machines into it; Rakuen rows use `1.111yen`, while 123 Namba and ARROW namBa HIPS rows use `1yen`.
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

The manual workflow is `.github/workflows/daily.yml`.

Current workflow behavior:

- Runs on `ubuntu-latest`.
- Uses Python `3.11`.
- Does not run on a schedule.
- Runs only through manual `workflow_dispatch`.
- Runs:
  - `python scripts/collect.py`
  - `python scripts/analyze.py`
  - `python scripts/build_report.py`
- Commits generated `docs/` changes back to `main`. Generated local `data/` outputs stay gitignored unless the project intentionally changes that policy.

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

Syntax check:

```bash
python -m py_compile scripts/collect.py scripts/analyze.py scripts/build_report.py scripts/validate_data.py scripts/utils.py scripts/term_notes.py pachinko-sim/main.py pachinko-sim/machines.py pachinko-sim/machine_traits.py pachinko-sim/sim_terms.py pachinko-sim/session_limits.py pachinko-sim/spec_benchmarks.py pachinko-sim/start_gate.py pachinko-sim/time_model.py pachinko-sim/rotation.py pachinko-sim/store_comparison.py pachinko-sim/model_checks.py pachinko-sim/result.py pachinko-sim/simulator.py pachinko-sim/stores.py
```

JSON validation:

```bash
python -m json.tool data/stores.json > /dev/null
python -m json.tool data/namba-actual-1yen-lineup.json > /dev/null
python -m json.tool data/latest.json > /dev/null
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
- When collection fails because of `403`, avoid overwriting useful collected data with all-failure results unless explicitly requested.
- When URLs fail with `404`, check for store URL changes or typos first.
- Keep `data/manual-notes.md` local/private. Do not commit sensitive travel details, screenshots, app/member data, or spending/profit notes.
- Keep private trip files under gitignored paths such as `private/`, `data/manual-notes.md`, or `data/travel-*`. Public `data/` and `docs/` files must stay objective and non-personal.
- Preserve UTF-8 content; this repository intentionally contains Korean and Japanese text.
- Keep GitHub Actions compatible with Python 3.11 and the dependencies in `requirements.txt`.
