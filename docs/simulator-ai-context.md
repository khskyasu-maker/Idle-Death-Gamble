# Simulator AI Context

이 파일은 GitHub에서 `pachinko-sim/` 결과를 읽는 AI가 참고할 공개용 해석 규칙입니다.
실제 실행 결과, 방문 판단, 개인 운영 메모는 공개 파일에 고정하지 않습니다.

## 공개 가능

- simulator purpose, assumptions, and metric definitions
- reproducible local commands
- fixed public machine specs and store/rate lineup context
- blank result-sharing template for conversation use

## 공개 금지

- per-run Monte Carlo result tables or CSV files
- visit rankings, go-here-today instructions, or final decisions
- personal movement, lodging, booking, passport, or spending records
- screenshots or app/member-only 台番号별 data

## 기본 가정

- 교환율 기본값: `0.89`엔/발
- 회전수 케이스: `[50, 60, 70, 80, 90, 100]`회/1000엔
- 예산 케이스: `[5000, 10000, 15000, 20000]`엔
- 프로파일 예산 케이스: `[1000, 5000, 10000, 15000, 20000]`엔
- 기본 전략: `no_rule`
- 기본 세션 방식: `fixed_spin_cap`
- 스타트 입상 변동 반영: `True`

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
- `stay_reach_rates`: Share of sampled sessions reaching each hour from 1 to 11 hours.
- `final_remaining_value`: Unused cash plus exchangeable final balls converted to yen.

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
    "session_policy": "fixed_spin_cap",
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
