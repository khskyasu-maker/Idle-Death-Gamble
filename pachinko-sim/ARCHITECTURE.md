# Pachinko Sim Architecture

## Scope

`pachinko-sim` is a local risk comparison simulator for Osaka Namba low-rate pachinko candidates.
It is not a jackpot predictor and does not publish visit rankings or personal travel decisions.

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
pachinko-sim/result.py
        |
        v
CLI output / optional append-only results.csv
```

Fixed real-world inputs and runtime outputs must remain separate:

- fixed store lineup and border data: `data/namba-actual-1yen-lineup.json`
- fixed machine specs and payout distributions: `machines.py`
- fixed public benchmark values used for model drift checks: `spec_benchmarks.py`
- runtime session assumptions: CLI inputs, strategy settings, `spins_per_1000y`, budget, exchange rate
- runtime time assumptions: launch speed, display seconds per start, right-side seconds per spin, payout/effect time
- runtime statistical output: `result.py` metrics and optional append-only `results.csv`

Do not copy Monte Carlo output, recommendation scores, or visit decisions back into fixed data files.

## Modules

### `stores.py`

Loads `../data/namba-actual-1yen-lineup.json` and builds store inventory.

Responsibilities:

- map DMM/manual lineup machine names to simulator model keys
- keep `MACHINE_NAME_TO_SIM_ID` as the active selectable subset; `machines.py`
  may retain extra reference models for deterministic spec checks
- keep supported and unsupported machines separate
- calculate local registered count, supported count, unsupported count, and DMM low-rate total gap
- convert borderline values into `spins per 1000 yen`
- attach objective fields only

This module should not contain personal visit priority or recommendation decisions.

### `machines.py`

Defines machine specs as `Machine` objects and hit distributions as `Payout` objects.

Core fields:

- `normal_prob`: normal-time jackpot denominator
- `high_prob`: right-side/ST/LT jackpot denominator
- `normal_hit_dist`: initial hit payout and transition distribution
- `st_hit_dist`: ST/RUSH hit distribution
- `jitan_hit_dist`: time-short hit distribution
- `kakuben_hit_dist`: loop-type probability-change distribution
- `lt_hit_dist`: Lucky Trigger state distribution
- `upper_hit_dist`: non-LT upper RUSH distribution, for states like GOLDパールRUSH(골드 펄 러시)
- `jinbee_hit_dist`: Okinawa6 ジンベェタイム(진베에 타임) distribution
- `right_spend_per_spin`: average ball loss during supported right-side states
- `fall_prob`: optional 転落小当り(전락 소당첨) denominator by state for fall-type RUSH
- `fall_reserve_spins`: optional residual spins after fall, used for public continuation-rate alignment
- `spec_source`, `confidence`, `is_estimated`, `notes`
- `Payout.counts_as_rush`: distinguishes short challenge/time-short states from actual RUSH entry metrics

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

Models the first pachinko gate: fired balls becoming start spins through ヘソ(헤소) entry.

Responsibilities:

- convert `spins_per_1000y` and `lend_rate` into a per-ball start-entry probability
- sample hidden table quality with a truncated normal distribution around the field/reference rotation rate
- sample realized start spins with a binomial model
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

This module does not change jackpot probability. It only changes how many
normal-start trials a cash or ball budget can buy.

### `time_model.py`

Converts simulated play into stay/play time.

Responsibilities:

- estimate active launch time from fired balls and a fixed balls-per-minute assumption
- estimate normal display time from start spins
- treat display time beyond active launch time as 保留(보류) full/effect waiting
- estimate right-side/ST/LT/時短(시단) time by state-specific seconds per spin
- estimate 大当り(대당첨) effect and payout time from payout balls
- select a machine-family time profile for Umi/Sea, Eva, Re:Zero, and modern
  battle/LT-style machines
- keep these values as runtime assumptions, not fixed public lineup data

Default assumptions are intentionally simple and visible: 100 balls/minute launch
and 6 seconds per normal start. Right-side speed and payout/effect time then vary
by family: Re:Zero uses a fast profile, Eva uses a medium-fast V-ST profile, and
Umi/Sea uses a slower traditional-support profile. These values are for visit-time
budgeting, not machine performance prediction.

### `store_comparison.py`

Builds runtime same-machine store comparison scenarios.

Responsibilities:

- compare only the same simulator machine id across stores
- keep installed and not-installed store rows visible in the output
- preserve the selected store as the reference condition
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
- nominal payout balls are sampled with a bounded normal distribution, so round
  distribution remains fixed by spec while small over入賞(오버입상)/round-loss
  variation stays centred on the public payout value
- strategy rules may lock balls or request exit
- `session_policy="fixed_spin_cap"` keeps the historical comparison behavior:
  normal spins are capped at `budget / 1000 * spins_per_1000y`
- `session_policy="play_until_budget_and_balls_gone"` allows reusable balls to
  extend normal play until cash budget and held balls are both insufficient
- all session policies use an 11-hour practical stop cap. After the cap is
  reached, the simulator stops instead of letting rare positive loops run
  indefinitely.
- new cash input is blocked after the 10-hour mark. Existing banked balls can
  continue paying normal spins until the 11-hour stop cap or ball exhaustion.
- budget comparison applies a practical normal-spin safety cap when using the
  play-until policy, so rare long positive sessions do not dominate runtime
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
  from 1 to 11 hours. The 11-hour value is a practical stop cap for leaving
  before close and avoiding late cash input, not a prediction that the hall will
  let a session continue unchanged.
- `time_limit_triggered` and `cash_input_cutoff_triggered` distinguish sessions
  stopped by the practical day cap from sessions that simply ran out of cash and
  balls.
- `final_remaining_value` is unused cash plus exchangeable final balls converted
  to yen. This is separate from `net_profit`, which remains final exchange money
  minus cash spent.

Statistical layers:

- table quality: truncated normal distribution around field/reference rotation
- start-entry count: binomial distribution from fired balls and start probability
- jackpot wait: geometric distribution for independent Bernoulli spins
- payout realization: truncated normal distribution around nominal payout balls
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

### `result.py`

Calculates and prints risk metrics.

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
