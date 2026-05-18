# Simulator AI Context

이 파일은 GitHub에서 `pachinko-sim/` 결과를 읽는 AI가 참고할 공개용 해석 규칙입니다.
실제 실행 결과, 방문 판단, 개인 운영 메모는 공개 파일에 고정하지 않습니다.

## AI 분석 파일 우선순위

- 1. `docs/latest-sim-results.json`: AI/코드 분석용 구조화 정본 (수치 지표, 가정, seed, 스키마 버전, 개인정보 정책, 추가 분석이 typed field로 보존됩니다.)
- 2. `docs/latest-sim-results.md`: JSON 파싱이 어려울 때 쓰는 텍스트 요약 (필드 파싱보다 표 설명과 요약 텍스트가 필요한 AI 대화에서 보조 컨텍스트로 씁니다.)
- 3. `docs/latest.json`: 라인업, 점포/레이트, 보더, 시뮬 정책 컨텍스트 (기종명, 레이트, 공개 라인업 필드를 대조할 때 시뮬 결과와 함께 봅니다.)

## 공개 가능

- simulator purpose, assumptions, and metric definitions
- reproducible local commands
- fixed public machine specs and store/rate lineup context
- latest sanitized aggregate simulator result table in docs/latest-sim-results.*
- blank result-sharing template for conversation use

## 공개 금지

- raw per-sample Monte Carlo sessions or local results.csv files
- accumulated simulator result history
- visit rankings, go-here-today instructions, or final decisions
- personal movement, lodging, booking, passport, or spending records
- screenshots or app/member-only 台番号별 data

## 로컬 결과 저장 정책

- If CSV save is explicitly selected in the local CLI, results.csv is gitignored and overwritten with the latest run only. Public sharing, when explicitly selected, overwrites docs/latest-sim-results.json, docs/latest-sim-results.md, and docs/latest-sim-results.html with sanitized aggregate metrics only.

## 표준 공개 집계 조건

- 재생성 명령: `python3 scripts/publish_sim_results.py`
- AI 정본: `docs/latest-sim-results.json`
- 해설용 요약: `docs/latest-sim-results.md`
- 브라우저 표시: `docs/latest-sim-results.html`
- 시뮬 점포 범위: `123難波店 1円, 楽園なんば店 1.111円`
- 예산 케이스: `[10000, 15000, 20000]`엔
- 행별 반복: `5000`회
- 회전 가정: `field_rotation_margin=0 / 보더±0`
- 회전율 민감도: `10000`엔 / `3000`회
- 하방/꼬리 리스크 리뷰: `10000`엔 기준
- 교환율: `0.89`엔/발
- 전략: `no_rule`
- 세션 방식: `play_until_budget_and_balls_gone`
- 세션 방식 설명: 현금과 재사용 가능한 보유구슬이 모두 부족할 때까지 진행하되, 9시간 이후에는 진행 중인 우타치/RUSH 상태 종료 시 정리하고 11시간 하드 캡을 둡니다.
- 공개 범위: 여행 전 가정 기반의 정제된 집계만 공개합니다. 시뮬 점포 범위는 123難波店과 楽園なんば店의 저대여 조건으로 제한하고, HIPS/마루한 나니와는 대화 중 비교·참조용으로만 둡니다. 원시 표본, 실제 플레이 기록, 방문 지시, 개인 지출은 포함하지 않습니다.
- 모델링 한계: 보류 심볼 제약: 일부 기종의 特図1/特図2 보류 우선순위와 심볼 선택 제약은 공개 스펙만으로 확정하기 어렵기 때문에, 현재는 상태별 분포와 잔보류 회전수로 근사합니다.
- 모델링 한계: 우측 소비 구슬: right_spend_per_spin은 ST/時短(시단)/確変(확변)/LT 상태별 평균값입니다. 기종별 상구 수, 오버입상, 전동 패턴 차이는 시간·잔류 구슬 오차로 남습니다.
- 모델링 한계: 연출 강제 대기 시간: TimeAssumptions는 기종족별 평균 프로파일입니다. 개별 기기의 당첨 고지, 라운드 전후 대기, 특수 모드 연출 시간은 별도 확정값이 있을 때만 반영해야 합니다.

## 로컬 CLI 기본 가정

- 교환율 기본값: `0.89`엔/발
- 회전수 케이스: `[50, 60, 70, 80, 90, 100]`회/1000엔
- 예산 케이스: `[5000, 10000, 15000, 20000]`엔
- 프로파일 예산 케이스: `[1000, 5000, 10000, 15000, 20000]`엔
- 기본 전략: `no_rule`
- 기본 세션 방식: `fixed_spin_cap`
- 스타트 입상 변동 반영: `True`
- 신뢰도 해석: 확률 분모/공식 스펙: very_high - DMM/스펙 사이트의 공개 확률과 보더를 그대로 옮긴 영역입니다.
- 신뢰도 해석: 상태 전이 분포: high - NORMAL/ST/時短(시단)/確変(확변)/LT/UPPER 계열 전이는 공개 분포와 벤치마크로 검증합니다.
- 신뢰도 해석: 예산/환율/재사용 구슬 회계: very_high - 고정 레이트, 교환율, 보유구슬 재사용 규칙에 따른 산술 영역입니다.
- 신뢰도 해석: 호기 품질/입상 분포: medium - 1000円당 회전수와 보더 마진으로 제약하지만, 실제 못 상태는 현장 관찰값에 의존합니다.
- 신뢰도 해석: 체류 시간: medium - 기종족별 시간 프로파일로 추정하며, 개별 기기의 연출/소화 속도 차이는 오차로 남습니다.
- 신뢰도 해석: 우측 소비 구슬: medium_low - right_spend_per_spin은 상태별 평균값이며, 기종별 상구/오버입상/전동 패턴은 세부 반영하지 않습니다.
- 신뢰도 해석: 보류 심볼/특図 제약: low - 공개 스펙에서 확인 가능한 잔보류 회전수는 반영하지만, 특図1/특図2 보류 큐와 심볼 선택 제약은 명시 큐로 모델링하지 않습니다.

## 레이트 규칙

- 1yen uses 200玉 per 200円 and 1000玉 per 1000円.
- 1.111yen uses 180玉 per 200円 and 900玉 per 1000円.
- Compare stores either by identical observed spins per 1000円 or by identical start-gate quality, but do not mix the two.

## 로컬 재현 명령

- `cd pachinko-sim && python3 main.py`
- `python3 -m unittest discover -s tests`
- `python3 scripts/validate_data.py`

## 로컬 출력 지표

- `avg_profit`: Monte Carlo sample average net result in yen; local estimate only.
- `median_profit`: Median net result in yen; often more useful than average for skewed payout distributions.
- `worst_10_profit`: Lower 10% percentile value in yen.
- `cvar10`: Average of the lower 10% tail outcomes.
- `positive_close_rate`: Share of sampled sessions ending above zero; not a real-world guarantee.
- `hit_rate`: Share of sampled sessions with at least one 大当り(대당첨); not a next-spin prediction.
- `rush_entry_rate`: Sampled RUSH entry share.
- `lt_entry_rate`: Sampled LT entry share; non-LT machines should be interpreted as not applicable.
- `avg_play_minutes`: Estimated stay/play time, including ball firing, reserve waiting, right-side spins, and hit effects.
- `avg_cashless_play_minutes`: Estimated time continuing without new cash input through right-side play, hit effects, and reusable held balls.
- `stay_reach_rates`: Share of sampled sessions reaching each hour from 1 to 9 hours.
- `time_limit_stop_rate`: Share of sampled sessions stopped by the 9-hour after-RUSH cleanup rule.
- `hard_time_limit_stop_rate`: Share of sampled sessions stopped by the 11-hour hard safety cap.
- `cash_input_cutoff_rate`: Share of sampled sessions that reached the late-session no-new-cash cutoff.
- `final_remaining_value`: Unused cash plus exchangeable final balls converted to yen.
- `funds_exhausted_stop_rate`: Share of sessions that stopped because cash budget and held balls were both insufficient.
- `avg_post_budget_play_minutes`: Average play time after the cash budget was fully spent, sustained by RUSH or won balls.

## AI 해석 규칙

- Treat all simulator outputs as local estimates, not predictions.
- Use observed spins per 1000円, rate, remaining time, and budget as conversation-time inputs only.
- Past 大当り count, current graph shape, and previous misses do not change the next-spin probability.
- Prefer explaining risk and assumptions over ranking stores or machines in public files.
- Keep final go/stop decisions in chat or private notes, not in GitHub Pages.

## 대화용 결과 입력 템플릿

아래 템플릿은 채팅에 임시로 붙여 넣기 위한 형식입니다. 채운 값을 public `docs/`나 `data/`에 저장하지 않습니다.

```json
{
  "source": "local pachinko-sim CLI output",
  "store_id": "",
  "store_name_seen": "",
  "rate_seen": "1yen or 1.111yen",
  "machine_name_seen": "",
  "mode": "matrix or budget_matrix or profile or store_comparison",
  "assumptions": {
    "spins_per_1000yen": null,
    "budget_yen": null,
    "exchange_rate_yen_per_ball": 0.89,
    "strategy": "no_rule",
    "session_policy": "fixed_spin_cap or play_until_budget_and_balls_gone",
    "iterations": null
  },
  "metrics_to_paste_temporarily": {
    "avg_profit": null,
    "median_profit": null,
    "worst_10_profit": null,
    "cvar10": null,
    "positive_close_rate": null,
    "hit_rate": null,
    "rush_entry_rate": null,
    "lt_entry_rate": null
  },
  "publication_note": "Do not commit filled results if they include personal budget, schedule, or decisions."
}
```
