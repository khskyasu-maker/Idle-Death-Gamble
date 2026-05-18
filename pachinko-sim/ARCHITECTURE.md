# Pachinko Sim Architecture

## Scope

`pachinko-sim` is a local risk comparison simulator for Osaka Namba low-rate pachinko candidates.
It is not a jackpot predictor and does not publish visit rankings or personal travel decisions.
The primary simulation surface is machine spec, observed or assumed rotation, budget, and stop rules.
Store labels are auxiliary context for rate, installation count, and border conversion, not a store ranking.

Public repository data must stay objective:

- store name
- machine name
- rate
- machine count
- probability
- borderline
- source
- checked date

Do not store personal itinerary, lodging, flight, reservation, spending diary, or "go today" decisions in this simulator.

## Data Flow

```text
data/namba-actual-1yen-lineup.json
        |
        v
pachinko-sim/stores.py
        |
        v
pachinko-sim/machines.py
        |
        v
pachinko-sim/rotation.py
        |
        v
pachinko-sim/start_gate.py
        |
        v
pachinko-sim/time_model.py
        |
        v
pachinko-sim/simulator.py
        |
        v
pachinko-sim/store_comparison.py
        |
        v
pachinko-sim/cli_modes.py + pachinko-sim/cli_inputs.py + pachinko-sim/cli_context.py + pachinko-sim/cli_export.py
        |
        v
pachinko-sim/result_printers.py
        |
        v
pachinko-sim/result_basic_printers.py + pachinko-sim/result_matrix_printers.py + pachinko-sim/result_store_printers.py
        |
        v
pachinko-sim/result_printer_common.py
        |
        v
pachinko-sim/result_matrix_sections.py
        |
        v
pachinko-sim/result_metrics.py + pachinko-sim/result_output_helpers.py + pachinko-sim/result_table_builders.py + pachinko-sim/result_stats.py + pachinko-sim/result_formatting.py + pachinko-sim/result_store_views.py + pachinko-sim/result_public_export.py
        |
        v
CLI output / optional latest-only local results.csv / optional latest-only public docs/latest-sim-results.*

pachinko-sim/result.py remains a compatibility export wrapper for older imports.
```

Fixed real-world inputs and runtime outputs must remain separate:

- fixed store lineup and border data: `data/namba-actual-1yen-lineup.json`
- fixed machine specs and payout distributions: `machines.py`
- reusable machine data types and family templates: `machine_types.py`, `machine_templates.py`
- fixed public benchmark values used for model drift checks: `spec_benchmarks.py`
- source-to-model translation rules: `SPEC_MODELING_GUIDE.md`
- runtime session assumptions: CLI inputs, strategy settings, `spins_per_1000y`, budget, exchange rate
- runtime time assumptions: launch speed, display seconds per start, right-side seconds per spin, payout/effect time
- runtime statistical output: `result_metrics.py` metrics, optional latest-only gitignored `results.csv`, and optional latest-only sanitized `docs/latest-sim-results.*`

Do not copy Monte Carlo output, recommendation scores, or visit decisions back into fixed data files.

## Modules

### `stores.py`

Loads `../data/namba-actual-1yen-lineup.json` and builds store inventory.

Responsibilities:

- map DMM/manual lineup machine names to simulator model keys
- keep `MACHINE_NAME_TO_SIM_ID` as the active selectable subset; `machines.py`
  may retain extra reference models for deterministic spec checks
- keep non-Eva/non-DaiUmi selectable models limited to
  `ACTIVE_OTHER_SIM_MODEL_IDS`; validation and unit tests should fail if a
  reference-only other model becomes selectable accidentally
- keep supported and unsupported machines separate
- calculate local registered count, supported count, unsupported count, and DMM low-rate total gap
- convert borderline values into `spins per 1000 yen`
- attach objective fields only

This module should not contain personal visit priority or recommendation decisions.

### `machines.py`

Defines machine specs as `Machine` objects and hit distributions as `Payout` objects.
Use `SPEC_MODELING_GUIDE.md` before adding or promoting a model, so public
DMM/official/source-page terms are mapped consistently into Python states.
When multiple machines share the same game flow, put the shared construction
logic in `machine_templates.py` and pass only the differing source/spec values
from `machines.py`.

Core fields:

- `normal_prob`: normal-time jackpot denominator
- `high_prob`: right-side/ST/LT jackpot denominator
- `jitan_prob`: optional time-short jackpot denominator when 時短(시단) uses a
  different public denominator from normal-time combined jackpot probability
- `normal_hit_dist`: initial hit payout and transition distribution
- `st_hit_dist`: ST/RUSH hit distribution
- `jitan_hit_dist`: time-short hit distribution
- `kakuben_hit_dist`: loop-type probability-change distribution
- `lt_hit_dist`: Lucky Trigger state distribution
- `LT_JITAN`: Lucky Trigger 중 時短(시단)처럼 저확률로 소화되지만, 당첨 후에는 `lt_hit_dist`를 따라 LT가 유지되는 보조 상태
- `upper_hit_dist`: non-LT upper RUSH distribution, for states like GOLDパールRUSH(골드 펄 러시)
- `UPPER_JITAN`: non-LT upper RUSH 중 時短(시단)처럼 저확률로 소화되지만, 당첨 후에는 `upper_hit_dist`를 따라 상위 모드가 유지되는 보조 상태
- `jinbee_hit_dist`: Okinawa6 ジンベェタイム(진베에 타임) distribution
- `right_spend_per_spin`: average ball loss during supported right-side states
- `fall_prob`: optional 転落小当り(전락 소당첨) denominator by state for fall-type RUSH
- `fall_reserve_spins`: optional residual spins after fall, used for public continuation-rate alignment
- `spec_source`, `confidence`, `is_estimated`, `notes`
- `Payout.counts_as_rush`: distinguishes short challenge/time-short states from actual RUSH entry metrics

`Payout.balls` is the simulator's practical budgeting value. If a public source
shows only `払出(지급)`, the model may use a conservative obtained-ball
approximation when that family already has a checked conversion rule. Current
Eva and 大海物語(대해물어) checked models convert `払出` to about 93%, rounded to
the nearest 10 balls. The public paid-out value and the conversion basis must
stay visible in `notes`.

Model confidence policy:

- `high`: public specs are reflected in an individual model
- `medium`: major structure is modeled but some round split, reserve, or provider detail is estimated
- `low`: rough temporary model; ranking should be capped or treated as observation only

For fixed machine data, `spec_source` must identify the public spec source and `is_estimated=False`
must be used only when the model is individually checked against a real machine spec.

### `machine_traits.py`

Provides shared machine classification helpers.

Responsibilities:

- expose the common payout distribution field list
- iterate all payout distributions in one place
- determine whether a machine really has LT
- determine whether a machine has a non-LT upper RUSH

Output code and validation code should use these helpers instead of duplicating LT/upper-RUSH logic.

### `sim_terms.py`

Provides Japanese-to-Korean simulator terminology and state labels.

Responsibilities:

- annotate Japanese terms with Korean translations
- keep state transition labels consistent in single-session logs
- avoid one-off translation dictionaries inside output code

### `spec_benchmarks.py`

Stores fixed public Japanese spec values used by model profile output.

Responsibilities:

- keep public source benchmark values separate from Monte Carlo statistics
- provide bilingual labels for spec comparison rows
- avoid writing simulation results back into fixed reference data

### `start_gate.py`

Models the first pachinko gate: gross fired balls becoming start spins through ヘソ(헤소) entry.

Responsibilities:

- sample realized start spins with a binomial model after the simulator converts
  net budget balls to gross fired balls with `time_model.py`
- sample hidden table quality with a truncated normal distribution around the field/reference rotation rate
- keep the expected rotation input separate from observed session rotation

This is intentionally separate from jackpot probability. A session first samples
the table-level rotation quality affected by 釘(못), 風車(풍차),
ステージ(스테이지), ワープ(와프), and ネカセ(네카세). It then samples how
many start spins the balls produce, and each start spin is an independent
machine-probability trial. Borderline values may bound the table-quality
distribution, but they do not change jackpot probability.

### `rotation.py`

Normalizes runtime rotation and borderline assumptions.

Responsibilities:

- convert observed field notes into `spins_per_1000y`
- preserve the input basis as a `RotationEstimate`, so the CLI can show whether
  a run came from `1000엔`, `200엔`, `250玉`, cash observation, or border-margin input
- convert `250玉`, `200玉`, `180玉`, and cash observations across 1円/1.111円 rates
- build border-relative scenario cases such as `보더-5`, `보더±0`, and `보더+5`
- calculate border margin, border ratio, and human-readable rotation judgement
- keep absolute `70회/1000엔` warnings as fallback only when no machine border is known

The latest public aggregate defaults to a conservative field-like `보더±0`
assumption. Better-than-border cases such as `보더+5` and `보더+10` belong in
the sensitivity analysis unless the run is explicitly marked optimistic.

This module does not change jackpot probability. It only changes how many
normal-start trials a cash or ball budget can buy.

### `time_model.py`

Converts simulated play into stay/play time.

Responsibilities:

- estimate active launch time from gross fired balls and a fixed balls-per-minute assumption
- convert net consumed balls back to gross fired balls with a visible
  ベース(반환 구슬) assumption
- estimate normal display time from start spins
- treat display time beyond active launch time as 保留(보류) full/effect waiting
- estimate right-side/ST/LT/時短(시단) time by state-specific seconds per spin
- estimate 大当り(대당첨) effect and payout time from payout balls
- select a machine-family time profile for Umi/Sea, Eva, Re:Zero, and modern
  battle/LT-style machines
- keep these values as runtime assumptions, not fixed public lineup data

Default assumptions are intentionally simple and visible: 100 balls/minute launch,
6 seconds per normal start, and a normal-time base return rate. The base return
rate is 25% for Umi/Sea and 20% for generic/Eva/Re:Zero/battle profiles. It does
not change cash or ball balance; it only increases the gross fired balls used for
active launch time. Right-side speed and payout/effect time then vary by family:
Re:Zero uses a fast profile, Eva uses a medium-fast V-ST profile, and Umi/Sea
uses a slower traditional-support profile. These values are for visit-time
budgeting, not machine performance prediction.

### `store_comparison.py`

Builds runtime same-machine store comparison scenarios.

Responsibilities:

- compare only the same simulator machine id across stores
- keep installed and not-installed store rows visible in the output
- preserve the selected store as the reference condition
- present store comparison as auxiliary rate, count, and border context rather than a general store ranking
- support three rate-aware assumptions:
  - `cash_rotation`: the same 1,000円(1000엔)당 observed rotation is used at each store
  - `ball_quality`: the same per-ball ヘソ(헤소) entry probability is preserved and
    1,000円(1000엔)당 rotation is recalculated by each store's lend rate
  - `border_margin`: each store uses the same margin against its own
    `border_spins_per_1000yen`, useful when comparing 1円 and 1.111円 stores

This module must not write comparison scores or visit decisions back into public
data files.

### `simulator.py`

Runs Monte Carlo sessions.

Current state machine:

- `NORMAL`: normal left-side play
- `ST`: limited high-probability RUSH/ST state
- `JITAN`: time-short state using normal probability
- `KAKUBEN`: loop-type probability-change state
- `LT`: Lucky Trigger state
- `UPPER`: limited high-probability upper RUSH that must not count as LT
- `UPPER_JITAN`: time-short part of a non-LT upper RUSH; normal probability, but hits use `upper_hit_dist`
- `JINBEE`: Okinawa6 ジンベェタイム確変(진베에 타임 확변), high probability until next hit
- `JINBEE_JITAN`: Okinawa6 ジンベェタイム時短200(진베에 타임 시단 200회), normal probability for 200 spins

Fall-type states can attach `fall_prob` to `ST` or `LT`. In those states the
simulator samples which happens first: 大当り(대당첨) or 転落小当り(전락 소당첨).
If fall happens first, optional `fall_reserve_spins` are sampled before returning
to normal play. This is used for machines such as `e北斗の拳10(e 북두의 권 10)`.

Session accounting:

- cash budget limits new cash input
- `lend_rate` converts cash to rented balls
- `exchange_rate` converts final balls to yen
- `card_reuse=True` allows banked balls to pay normal-spin cost
- right-side states subtract average balls per spin
- normal-spin cash and held-ball balance use net consumed balls from the observed
  `spins_per_1000y`; active launch time uses gross fired balls after adding back
  ベース(반환 구슬)
- nominal payout balls are sampled with a bounded normal distribution, so round
  distribution remains fixed by spec while small over入賞(오버입상)/round-loss
  variation stays centred on the public payout value
- strategy rules may lock balls or request exit
- `session_policy="fixed_spin_cap"` keeps the historical comparison behavior:
  normal spins are capped at `budget / 1000 * spins_per_1000y`
- `session_policy="play_until_budget_and_balls_gone"` allows reusable balls to
  extend normal play until cash budget and held balls are both insufficient
- all session policies use a 9-hour soft stop. In normal play, the simulator
  stops around that mark; if the player is already in RUSH/時短(시단)/確変(확변),
  play continues until the right-side state returns to normal.
- an 11-hour hard cap remains as a safety bound so rare positive loops do not
  run indefinitely.
- new cash input is blocked after the 9-hour mark. Existing banked balls can
  continue only when the player is still resolving the active right-side state.
- budget comparison does not cap normal spins in the play-until policy by
  default; the 9-hour soft stop and 11-hour hard cap are the runtime guards.
- miss streaks are sampled with an equivalent geometric distribution instead
  of looping one spin at a time, which keeps 5,000 to 20,000 iteration runs
  practical without changing Bernoulli hit probabilities
- `basic_stop` samples a first-1000円(1000엔) probe from the same table-quality
  distribution and applies the stop cap from that observed rotation, rather
  than from the scenario input rotation. If the probe produces no jackpot and
  is below threshold, the probe cost is charged.
- `first_hit_spin` records normal-side spins at the first jackpot, while
  `first_hit_total_spins` also includes 時短(시단)/right-side spins before that
  first jackpot for field-like "how long until it hit" interpretation.
- `play_minutes` estimates stay/play time from normal launch time, display time,
  保留(보류) full/effect waiting, right-side spins, and 大当り(대당첨) payout/effect time.
- `cashless_play_minutes` estimates time continuing without new cash input,
  including right-side play, hit effects, and normal spins paid by reusable balls.
- `stay_reach_rates` reports the share of sampled sessions reaching each hour
  from 1 to 9 hours. The 9-hour value is the practical travel-day stop point,
  not a prediction that the hall will let a session continue unchanged.
- `time_limit_triggered` and `cash_input_cutoff_triggered` distinguish sessions
  stopped by the hard cap or late cash-input rule from sessions that simply ran
  out of cash and balls. `soft_stop_triggered` tracks the 9-hour RUSH-ended
  cleanup rule.
- `final_remaining_value` is unused cash plus exchangeable final balls converted
  to yen. This is separate from `net_profit`, which remains final exchange money
  minus cash spent.
- `cash_budget_exhausted`, `funds_exhausted_triggered`, and
  `post_budget_play_minutes` separate "cash budget spent" from "cash and balls
  both gone". This keeps long sessions sustained by RUSH or won balls visible in
  the output.

Statistical layers:

- table quality: truncated normal distribution around field/reference rotation
- start-entry count: binomial distribution from fired balls and start probability
- jackpot wait: geometric distribution for independent Bernoulli spins
- payout realization: truncated normal distribution around nominal practical
  budgeting balls, not raw `払出(지급)` when the model has a conversion rule
- play time: deterministic conversion from sampled spins/balls/events through
  `time_model.py` assumptions
- categorical rates: Wilson confidence intervals
- conditioned useful-profit rates: Wilson confidence intervals for `net_profit > 0`
  after 大当り(대당첨) count and max-streak thresholds
- mean net profit: t-based confidence interval for small samples, normal limit for large samples
- denominator-tail display: normal-probability no-hit probability after 1x/2x/3x/5x
  the denominator, showing that exceeding the public probability denominator is normal
  under independent trials
- border-relative matrix scenarios: when a machine has a known border, default
  rotation comparisons use `보더-10/-5/±0/+5/+10`; unknown-border machines fall
  back to absolute `50/60/70/80/90/100` cases

Important current limitation:

- exchange lot size, leftover balls, time-of-day, closing-time, and exact stop-button
  technique are still outside the model

### `result.py` and CLI helpers

`main.py` is a thin entry point. Interactive flow is split across `cli_modes.py`,
`cli_inputs.py`, `cli_context.py`, and `cli_export.py`.

`result_printers.py` reexports the public printer API used by the CLI. The actual
printer implementations live in `result_basic_printers.py`,
`result_matrix_printers.py`, and `result_store_printers.py`.
Shared printer header/context/footer helpers live in `result_printer_common.py`.
Matrix-family table headers and section printers live in
`result_matrix_sections.py`.
`result.py` is a compatibility export wrapper for older `from result import ...`
callers.

Focused printer modules should keep the user-facing report assembly while
delegating reusable pure helpers to:

- `result_metrics.py`: Monte Carlo aggregate metrics such as profit, hit, stay-time, cash exhaustion, and condition rows
- `result_output_helpers.py`: output text helpers, benchmark comparison values, LT/upper-RUSH labels, and reusable table rows
- `result_table_builders.py`: reusable row builders for single, repeated, matrix, budget, profile, and strategy output tables
- `result_stats.py`: Monte Carlo uncertainty helpers, Wilson intervals, quantile intervals, tail means, and useful-profit condition rows
- `result_formatting.py`: terminal table width handling, yen/percent/minute text, and ASCII bar/table helpers
- `result_csv.py`: latest-only matrix CSV serialization used only after explicit user confirmation
- `result_public_export.py`: latest-only sanitized public simulator result JSON/Markdown/HTML export used only after explicit user confirmation
- `result_store_views.py`: same-machine store comparison table rows and explanatory labels

Primary outputs:

- hit experience rate
- no-hit finish rate
- 1,000 yen baseline spins, theoretical first-hit chance, and no-hit chance
- budget profile for 1,000 / 10,000 / 20,000 / 30,000 / 40,000 / 50,000 yen
- RUSH/LT rate
- LT should be shown as `해당없음` for non-LT machines, not as `0%`
- non-LT upper RUSH should be shown separately from LT
- per-session 大当り(대당첨) count and max streak
- single-session 大当り(대당첨) event log
- positive close rate
- useful-profit condition rows by 大当り(대당첨) count and max streak, so
  "hit once" is not confused with a session that actually ends positive
- average and median net profit
- lower 10% and upper 10% outcomes
- standard error for average net profit
- standard error as a percentage of budget, to show Monte Carlo precision
- rank-based 95% confidence intervals for median/lower-10%/upper-10% quantiles
- CVaR10-style lower-tail average for downside risk
- P10/P25 stay-time, mean-minus-median profit gap, and LT entry rate as a lower-tail review, so high-variance LT/e-machine rows are not judged by average profit alone
- independent-trial tail probabilities for denominator-overrun interpretation
- first-hit total-spin metrics that include 時短(시단)/right-side spins before the first jackpot
- budget comparison for 10,000 / 20,000 / 30,000 / 40,000 / 50,000 yen inputs
- recovery rates
- profit-lock and stop-loss trigger rates
- relative comparison score
- borderline warning, border margin, border ratio, and rotation judgement
- public Japanese spec benchmark comparison, shown with Korean translation

Statistical outputs should include uncertainty because Monte Carlo rankings can move when iteration counts are low.

When Japanese terms are displayed in CLI or docs, include Korean translation beside them whenever practical.

### `model_checks.py`

Provides deterministic checks independent of random simulation.

Responsibilities:

- calculate theoretical no-hit rate for normal-only spins
- calculate theoretical hit rate for fixed spin counts
- calculate state continuation probability for ST/LT-like states
- validate payout distribution weights
- validate state names and non-negative payout values
- validate fixed model metadata such as `confidence`, `spec_source`, and `is_estimated`
- reuse shared machine trait definitions for distribution coverage

These checks are not a replacement for machine specs. They are guardrails to catch impossible or internally inconsistent models.

## Simulation Assumptions

The current simulator intentionally simplifies several real-world factors.

Modeled:

- fired balls entering ヘソ(헤소) and becoming start spins as a stochastic first gate
- normal jackpot probability
- ST/JITAN/KAKUBEN/LT/UPPER/JINBEE state transitions
- payout distribution by hit state
- average right-side ball loss
- lend rate and exchange rate
- card reuse
- simple stop-loss/profit-lock/aggressive strategies
- borderline comparison
- same-machine store comparison with explicit 1円(1엔)/1.111円(1.111엔) assumption handling

Partially modeled:

- start rotation variance through an aggregate binomial approximation, not exact nail physics
- LT entry and LT continuation
- non-LT upper RUSH entry and continuation
- Okinawa6 ジンベェタイム確変(진베에 타임 확변)/時短200(시단 200회) split
- 1種2種(1종2종) machines through combined limited-spin states
- practical net payout through random payout variance

Not yet fully modeled:

- exact round/count/award/net-ball formula
- over-entry and under-entry distribution
- prize exchange lot size and leftover balls
- start rotation already sitting on the machine
- 遊タイム(유타임) targeting
- residual保留(잔보류) exceptions by machine
- per-machine right-side ball loss calibration
- time-of-day or closing-time constraints
- actual unit-by-unit data, jackpot history, slump graph, or app-only data

## Statistical Policy

Monte Carlo results must be treated as estimates, not exact values.

Recommended iteration policy:

- quick smoke check: 100 to 500 iterations
- working comparison: 1,000 to 5,000 iterations
- final candidate comparison: 10,000 or more iterations for high-variance machines

Ranking interpretation:

- score differences under 2 points should be treated as effectively tied
- 129 LT, 319, 349, and 399 machines need more iterations than 99 machines
- average profit alone is not enough; median, lower 10%, and no-hit rate must be read together
- low-confidence models should not outrank high-confidence models without a warning

## Improvement Roadmap

### Phase 1: Statistical Guardrails

- add 95% confidence intervals for positive close rate, no-hit rate, RUSH/LT rate, and average profit
- add theoretical no-hit checks beside simulation no-hit results
- add payout distribution validation
- record single-session 大当り(대당첨) events with state, spin count, payout, transition, RUSH entry, LT entry, and streak

### Phase 2: Explicit Session Policy

- split `cash_budget` from `session_spin_limit`
- support policies such as:
  - fixed normal-spin cap
  - play until cash budget and reusable balls are gone
  - stop at profit lock
  - stop at time/rotation cap
- make the current cap visible in output

### Phase 3: Payout Model Upgrade

- replace simple `balls` values with round/count/award/net-output definitions where specs are known
- keep fallback `balls` for estimated machines
- track gross payout, right-side spend, and final net balls separately

### Phase 4: Machine-Spec Completeness

- promote models from `medium` to `high` only when major spec values are checked
- keep estimated fields visible in output
- add missing low-rate machines only as unsupported/observation rows unless a model is implemented

### Phase 5: Field Use

- keep final operational rules separate from public report outputs
- use on-site measured rotations as input
- do not publish personal session logs or travel schedule
