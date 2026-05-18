# Machine Spec Modeling Guide

This document defines how to translate public pachinko machine information into
the local Python simulator model.

The goal is not to scrape DMM or official product pages every time. Public pages
change, and provider access can be blocked. Instead, read public sources when a
model is added or corrected, categorize the machine structure, then implement a
small explicit `Machine` model with source notes and confidence.

## Source Priority

Use sources in this order:

1. Official manufacturer product/spec page
2. DMMぱちタウン machine page
3. P-WORLD, 777パチガブ, なな徹, 1geki, chonborista, or similar public spec pages
4. Store machine list pages for installation count and rate only
5. Videos, screenshots, and 台データ(기기별 데이터) only as behavioral reference, not fixed spec truth

Record the source in `Machine.spec_source`. Do not store screenshots, login-only
data, app-only data, or personal trip observations in public files.

## Public Fields To Capture

For each machine, collect these public fields before writing code:

- Japanese machine name and Korean display name
- Normal jackpot probability: `大当り確率`, `通常時確率`, or `図柄揃い確率`
- Right-side probability: `高確率`, `RUSH中確率`, `ST中確率`, or `右打ち中確率`
- Initial hit distribution: `ヘソ`, `特図1`, `通常時振分`
- Right-side distribution: `電チュー`, `特図2`, `RUSH中振分`
- State names: `ST`, `RUSH`, `時短`, `確変`, `LT`, `上位RUSH`, `転落`, `Cタイム`
- Support spin counts: `ST回数`, `時短回数`, `残保留`, `次回まで`
- Entry rates: `RUSH突入率`, `LT突入率`, `継続率`
- Payout values: `出玉`, `払出`, `賞球`, `ラウンド`, `カウント`
- Special mechanics: `転落小当り`, `チャージ`, `小当りRUSH`, `3000個`, `一撃`, `上乗せ`
- Borderline values, with rate and exchange assumptions, if used for rotation

When a value is ambiguous, keep `confidence="medium"` or `confidence="low"` and
explain the ambiguity in `notes`.

Do not silently patch over missing internal mechanics. If the public source does
not expose exact 特図1/特図2(특도1/특도2) hold queues, symbol-selection
constraints, right-side pocket loss, or forced effect waits, keep the probability
model anchored to public distributions and describe the gap through
`simplification_notes`, `confidence`, and `modeling_assumptions.py`.

## Source Term To Python Field Map

Use this table while reading DMM or official pages.

| Public term | Korean meaning | Python field or module | Notes |
| --- | --- | --- | --- |
| `大当り確率`, `通常時確率` | 초당첨/통상 확률 | `Machine.normal_prob` | Denominator only, such as `319.7` |
| `時短中図柄揃い確率` | 시단 중 도안 당첨 확률 | `Machine.jitan_prob` | Only set when it differs from `normal_prob`, such as エヴァ17 チャージ込み1/349.9 vs 図柄揃い1/399.9 |
| `右打ち中確率`, `ST中確率`, `高確率` | 우타치/ST/고확률 | `Machine.high_prob` | For fall type, this is the jackpot side of the race |
| `ヘソ`, `特図1` | 헤소/특도1 배분 | `normal_hit_dist` | Initial hit payout and next state |
| `電チュー`, `特図2` | 전추/특도2 배분 | `st_hit_dist`, `lt_hit_dist`, `upper_hit_dist` | Choose the distribution matching the current state |
| `RUSH突入率` | RUSH 진입률 | `Payout.counts_as_rush`, benchmark | Do not count short challenge states as real RUSH unless public spec does |
| `継続率` | 계속률 | benchmark and state validation | Use to validate, not as a replacement for state mechanics |
| `ST○回`, `時短○回` | ST/시단 회수 | `st_spins`, `jitan_spins` | Add residual balls only when deliberately approximating total chance count |
| `残保留` | 잔보류 | usually folded into spin count | Document if folded into `st_spins` or ignored |
| `次回まで` | 다음 당첨까지 | `KAKUBEN` or fall/race state | Avoid pretending it is fixed ST |
| `転落小当り` | 전락 소당첨 | `fall_prob`, `fall_reserve_spins` | Use race model when available |
| `LT`, `ラッキートリガー` | 럭키 트리거 | `LT`, `lt_hit_dist`, `Payout.is_lt` | Must be official LT, not just strong RUSH |
| `上位RUSH` | 상위 러시 | `UPPER`, `UPPER_JITAN`, `upper_hit_dist` | Use `UPPER_JITAN` when the upper mode has a low-probability time-short segment that still returns to the upper distribution |
| `出玉`, `獲得` | 실획득/출옥 | `Payout.balls` | Preferred payout basis |
| `払出` | 지급/불출 | `Payout.balls` with note | Can be optimistic versus net obtained balls |
| `賞球`, `ラウンド`, `カウント` | 상구/라운드/카운트 | payout calculation input | Calculate only when no direct payout value exists |
| `ボーダー` | 보더라인 | `data/...json`, `rotation.py` | Rate/exchange dependent; not a machine probability |

## Model Category Decision Tree

Choose the category first, then write code.

| Category | Typical public wording | Python state core | Confidence risk |
| --- | --- | --- | --- |
| Plain ST / V-ST | `ST○回`, `V-ST`, fixed support | `ST`, `JITAN` | low once distributions are known |
| Breakthrough ST | `突破`, `チャレンジ`, short support first | `counts_as_rush=False` challenge | medium if challenge and real RUSH share `ST` |
| 1種2種 | `RUSH○回+残保留`, high-speed right side | `ST` with combined chance count | medium if only continuation rate is public |
| 確変ループ | `確変`, `次回まで`, normal after fail | `KAKUBEN`, `JITAN` | low/medium depending on round split |
| 転落 type | `転落`, `転落小当り` | `fall_prob` race | high if fall denominator is missing |
| LT | `LT`, `ラッキートリガー` | `LT`, `is_lt=True` | high if confused with upper RUSH |
| Non-LT upper RUSH | `上位RUSH`, named upper mode | `UPPER`, optional `UPPER_JITAN` | medium if public continuation is aggregate only |
| Charge / C-Time | `チャージ`, `Cタイム` | `normal_support_dist` or note | high if counted as jackpot differently by provider |

## Current Local Family Mapping

The simulator should stay focused on the current low-rate Osaka/Namba use case.
Rows can exist in the public lineup data without becoming selectable simulator
models. Promote a row only when the machine is present in the low-rate lineup,
the user may realistically play it, and the public spec can be represented
without inventing mechanics.

| Family | Category to check first | Local examples | Notes |
| --- | --- | --- | --- |
| Eva / エヴァ | V-ST, breakthrough V-ST, LT-ST, or LT 1種2種 | `eva_15_roar`, `eva_15_premium`, `eva_15_special_199`, `shin_eva_type_rei`, `shin_eva_premium_99`, `shin_eva_129_lt`, `eva_beginning` | Promote only when low-rate installation is confirmed. Use shared Eva templates when the state flow matches. `eゴジラ対エヴァンゲリオン2 超デカゴールド` stays lineup-only until its large-start/LT route is modeled explicitly. |
| Daiumi / 海物語 | 確変ループ, ST+時短, 1種2種, LT, or non-LT upper RUSH | `sea_5`, `sea_5_special`, `sea_5_agnes`, `sea_5_black_lt`, `sea_5_black_199` | Prefer `sea_kakuhen_loop` or `sea_st_jitan` before hand-writing repeated distributions. Sea machines often need `KAKUBEN`, `JITAN`, and slower `sea_classic` time assumptions. |
| Re:Zero / リゼロ | 1種2種 RUSH or ST-like limited RUSH | `re_zero_99`, `re_zero_199`, `re_zero_s2_129`, `re_zero_s2_349` | Use fast time assumptions; verify 3000-ball and bonus split carefully. Keep `re_zero_s2_129` reference-only while it is HIPS-only; promote it only if 123/Rakuen low-rate installation is reconfirmed. |
| Hokuto / 北斗 | fall-type, battle RUSH, ST+時短 LT, or battle LT | `hokuto_jibo`, `hokuto_10` | Do not approximate fall/LT mechanics as plain ST when fall probability is public. For ST+long時短 LT, use `LT_JITAN` so low-probability time-short hits keep LT continuation rules. |
| Other anime/battle LT | LT, upper RUSH, or charge/C-Time | `lupin_77_sweet`, `kabaneri_2`, `tokyo_ghoul` | Keep unsupported until normal probability, entry route, right distribution, LT route, and time profile are clear. Charge/C-Time models may use a combined normal denominator when public spec pages define one. |

## One-Machine Reading Sheet

Use this worksheet before editing `machines.py`.

```text
Machine:
Store/rate confirmation:
Source URLs checked:
Normal denominator:
Right-side denominator:
Initial hit distribution:
Right-side distribution:
Support spins / residual balls:
RUSH entry route:
Real RUSH or challenge first:
Continuation benchmark:
LT path:
Upper RUSH path:
Fall or transfer lottery:
Payout basis: 出玉 / 獲得 / 払出 / calculated
Border value and rate basis:
Likely time profile:
Python category:
Implementation confidence: high / medium / low
Simplification notes:
Reject/remove reason, if any:
```

If a required row cannot be filled from public sources, do not create a precise
model. Either keep the lineup row unsupported, keep a low-confidence temporary
reference, or remove the model if it was based on a wrong/nonexistent spec.

## Promote, Keep Unsupported, Or Remove

Use these rules after the reading sheet is filled:

- Promote to selectable simulator model only when the store/rate row is low-rate
  and the main game flow is known.
- Keep as unsupported lineup data when installation is confirmed but the Python
  model is not worth implementing yet.
- Keep as reference-only in `machines.py` only when it helps tests or near-term
  comparison and is not exposed as a selectable store machine.
- Remove from the low-rate lineup if the source confirms it is 4円-only at the
  target store.
- Remove or downgrade a model when public sources do not confirm the probability,
  distribution, or named mechanic that the Python code assumes.

### 1. Plain ST / V-ST

Use when the spec has:

- normal hit
- limited high-probability support, such as ST100 or ST163
- no fall lottery
- right-side hits usually return to the same ST

Python mapping:

- `normal_prob`: normal denominator
- `high_prob`: ST denominator
- `normal_hit_dist`: initial ST vs non-ST/time-short split
- `st_hit_dist`: right-side payout distribution
- `jitan_hit_dist`: time-short pullback distribution, if time-short can promote to ST
- `counts_as_rush=False` for short challenge states that should not count as real RUSH yet

Example shape:

```python
Machine(
    normal_prob=319.7,
    high_prob=99.4,
    normal_hit_dist=[
        Payout(balls=1500, weight=0.03, next_state="ST", st_spins=163),
        Payout(balls=450, weight=0.56, next_state="ST", st_spins=163),
        Payout(balls=450, weight=0.41, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
    ],
    st_hit_dist=[Payout(balls=1500, weight=1.0, next_state="ST", st_spins=163)],
)
```

### 2. Breakthrough ST / Challenge Type

Use when initial hits enter a short challenge and only a hit during that
challenge becomes real RUSH.

Python mapping:

- initial short ST or time-short can be represented as `ST` or `JITAN`
- set `counts_as_rush=False` on challenge entry payouts
- right-side challenge hits transition into the real RUSH state
- if the simulator cannot distinguish challenge ST from real ST cleanly, document
  the simplification in `simplification_notes`

This category is common for 1/99 and 1/129 light machines.

### 3. One-Shot / 1種2種 RUSH

Use when the right side is not classic high-probability ST, but a limited number
of high-speed chances plus residual balls.

Python mapping:

- `high_prob`: combined right-side hit denominator if public pages provide it
- `st_spins`: total chance count, including residual balls when practical
- `normal_hit_dist`: direct RUSH, challenge, or normal end split
- `st_hit_dist`: right-side payout split
- explain residual-ball approximation in `simplification_notes`

If public pages give only `継続率`, derive a denominator only when the implied
spin count and hit chance are clear. Otherwise mark the model `medium` or `low`.

### 4. 確変ループ(확변 루프)

Use when hits are split between probability-change continuation and normal/time
short, often with `次回まで`.

Python mapping:

- `KAKUBEN`: next-hit probability-change state
- `JITAN`: time-short state after normal hits
- `kakuben_hit_dist`: next hit distribution while in probability change
- `jitan_hit_dist`: pullback distribution during time-short

This is appropriate for many Umi/Sea middle models.
Use `sea_kakuhen_loop` for repeated 10R確変/通常 distributions before
hand-writing `normal_hit_dist`, `jitan_hit_dist`, and `kakuben_hit_dist`.

### 4b. ST+時短(시단) Ama/Light Sea

Use when every hit enters a short ST and then carries a time-short reserve,
such as Agnes-style PA大海 models.

Python mapping:

- `ST`: fixed high-probability spins
- `Payout.jitan_spins`: time-short spins after ST if no hit occurs
- same payout distribution normally applies to normal/ST/JITAN hits

Use `sea_st_jitan` when the distribution can be represented as
`(balls, weight, st_spins, jitan_spins)` rows.

### 5. 転落(전락) Type

Use when RUSH continues until either jackpot or fall lottery happens first.

Python mapping:

- `fall_prob`: denominator by state, such as `{"ST": 155.3}`
- `fall_reserve_spins`: residual chances after fall, if public continuation rate includes them
- `st_hit_dist` or `lt_hit_dist`: payout distribution when hit wins the race

Do not approximate a fall-type RUSH as fixed ST unless the fall detail is unknown
and the model is intentionally low-confidence.

### 6. LT / Lucky Trigger

Use when the public spec explicitly has `LT`, `ラッキートリガー`, or an LT-only
state.

Python mapping:

- `LT` state for LT support
- `lt_hit_dist` for LT hits
- `Payout.is_lt=True` on payouts that enter or continue LT
- use `machine_has_lt()` in output and validation

Do not label a non-LT upper mode as LT just because it is stronger than normal
RUSH.

### 7. Non-LT Upper RUSH

Use for modes such as `上位RUSH`, `GOLDパールRUSH`, or named upper states that
are not officially LT.

Python mapping:

- `UPPER` state
- `UPPER_JITAN` when the named upper mode continues through a normal-probability 時短 segment
- `upper_hit_dist`
- `machine_has_upper()` for output
- keep LT output as `해당없음` when the machine has no official LT path

### 8. Charge / C-Time / Support Event

Some e-machines have `チャージ`, `Cタイム`, or support events that are not normal
jackpots.

Python mapping:

- if it changes only state and gives little or no payout, consider
  `normal_support_prob` and `normal_support_dist`
- if it is counted in public jackpot probability but not in the user's lived
  jackpot feeling, document the difference clearly
- if the normal headline probability includes a charge route but 時短 uses a
  symbol-hit denominator, use `normal_prob` for the combined normal jackpot and
  `jitan_prob` for 時短 hit checks
- keep confidence `medium` until benchmark checks match public values

## Payout Conversion Rules

Public pages may show either paid-out balls or net balls. This simulator's
`Payout.balls` should represent practical obtained balls for budgeting.

Use this order:

1. If public page gives `出玉` or `獲得`, use that value.
2. If only `払出` is shown, convert to a practical budgeting value when the
   same family already uses one, and note the conversion in `notes`.
   - Current Eva and Daiumi models use about 93% of `払出`, rounded to the
     nearest 10 balls, for budgeting.
3. If round/count/award are shown, calculate `rounds * count * award`, then apply
   a conservative adjustment only when the existing model family already does so.
4. Do not mix 4円 and 1円 values. Machine spec is rate-independent; border and
   store rotation are rate-dependent.

`sample_payout_balls()` adds a small bounded variance around the nominal payout.
Do not encode random over入賞(오버입상) directly into the fixed distribution.

## Probability And Weight Rules

- Distribution weights must sum to `1.0` per state.
- Use decimal probabilities, not percentages: 59% becomes `0.59`.
- For public continuation rates, verify the implied model with
  `spec_benchmarks.py` before marking confidence `high`.
- Do not infer that a machine is "hot" from past hit history. Past hits can be
  used only as example scenarios or behavioral references.

## Time Model Mapping

Public spec pages often provide payout speed, shortest variation, or RUSH
duration examples. Map them to `time_model.py`, not `machines.py`.

Use family profiles first:

- Eva V-ST: medium-fast right side and medium payout speed
- Umi/Sea: slower traditional support and payout; default normal-time
  ベース(반환 구슬) is 25% for stay-time gross launch conversion
- Re:Zero and high-speed LT machines: faster right side and faster payout
- Modern battle/LT machines: fast but usually not as fast as Re:Zero

The simulator treats field rotation such as `70回/1000円` as net ball
consumption. For stay time, `time_model.py` converts that net consumption back
to gross launched balls with `net / (1 - base_return_rate)`. Do not change
jackpot probability or border conversion with this value.

Only add a new time profile when a machine family clearly behaves differently
and affects stay-time output materially.

## Border And Rotation Mapping

Borderline belongs to lineup/store data and `rotation.py`, not machine payout
logic.

- 1円: keep border as `200玉당 회전수`, then convert to `spins_per_1000yen`
- 1.111円: keep 180玉 or 200円 basis separate
- 4円 values can be used as source references only after rate/exchange conversion
- actual field observation should remain a runtime input

## Confidence Checklist

Mark `confidence="high"` only when:

- normal probability is checked
- right-side probability is checked
- initial hit distribution is checked
- right-side payout distribution is checked
- support spin counts are checked
- LT/upper/fall mechanics are classified correctly
- `model_checks.py` passes
- public benchmark rows are close enough or the difference is explained

Use `medium` when the main behavior is represented but one or more details are
estimated. Use `low` for temporary placeholders.

## Implementation Checklist

1. Pick an existing reusable factory in `machine_templates.py` when the machine
   has the same structure as an existing family.
2. Add a new factory in `machine_templates.py` only when at least two machines
   share a real mechanic and only values differ.
3. Add or update the `Machine` entry in `machines.py`.
4. Add `spec_source`, `confidence`, `is_estimated`, `simplification_notes`, and `notes`.
5. Add public benchmark values to `spec_benchmarks.py` when available.
6. Add validation metadata in `model_checks.py` if the model should be selectable.
7. Add name mapping in `stores.py` only if the machine exists in the low-rate lineup and should be selectable.
8. For non-Eva/non-DaiUmi machines, update `ACTIVE_OTHER_SIM_MODEL_IDS` only after deciding that the model is part of the current small active set. Reference models may stay in `machines.py` without a store mapping.
9. Run:

```bash
python3 -m py_compile pachinko-sim/machine_types.py pachinko-sim/machine_templates.py pachinko-sim/machines.py pachinko-sim/model_checks.py pachinko-sim/spec_benchmarks.py pachinko-sim/simulator.py pachinko-sim/result.py pachinko-sim/result_printers.py pachinko-sim/result_basic_printers.py pachinko-sim/result_matrix_printers.py pachinko-sim/result_matrix_sections.py pachinko-sim/result_store_printers.py pachinko-sim/result_printer_common.py
python3 -m unittest discover -s tests
python3 scripts/validate_data.py
```

Current active other-machine policy:

- Active: `hokuto_jibo`, `re_zero_99`, `lupin_77_sweet`, `kabaneri_2`, `tokyo_ghoul`
- Reference only: `re_zero_199`, `re_zero_s2_349`, `hokuto_10`
- `re_zero_s2_129` remains reference-only while the confirmed low-rate row is HIPS 1円, not 123/Rakuen low-rate.

## What Not To Model Yet

- Automated app login, member-only pages, or 台番号(기기 번호) crawling
- Visit recommendations stored in public files
- Past-hit prediction
- Slump graph prediction
- Personal trip budget or actual spending records
- Per-machine live data unless the project scope is explicitly changed

## Practical Reading Examples

When reading DMM or an official page, translate the page into these questions:

- What is the normal denominator?
- What state does the initial hit enter?
- Is the first support state real RUSH or only a challenge?
- How many support spins exist, and are residual balls included?
- Are right-side hits always the same payout, or is there a split?
- Is there a fall lottery?
- Is there an official LT path?
- Is an upper mode LT or non-LT upper RUSH?
- Is the displayed payout paid-out balls or practical obtained balls?
- Does the public continuation rate match the Python state model?

Only after these answers are clear should a model be promoted from unsupported
lineup row to selectable simulator machine.
