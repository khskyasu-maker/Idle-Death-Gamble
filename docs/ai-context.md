# AI Context

이 파일은 `docs/latest.json`을 AI 대화에 넣을 때 함께 참고하는 짧은 규칙입니다.

## 사용 목적

- store/machine lookup
- rate and border cross-checking
- onsite observation comparison
- conversation-time dynamic analysis

## 금지

- jackpot prediction
- fixed visit ranking in public files
- win-rate or profit guarantee
- personal trip, booking, passport, lodging, or spending records

## 핵심 필드

- `rate`: 1yen uses 200玉 per 200円. 1.111yen uses 180玉 per 200円.
- `border_spins_per_1000yen`: Converted reference rotations per 1000円 for simulator and AI comparison.
- `onsite_judgment`: Rotation threshold reference only, not a result prediction.
- `aliases`: Search/display helpers derived from objective machine names.
- `checked_at`: Manual/public-source check date. Re-check onsite if stale.

## 최신성

- 생성 시각: 2026-05-18 20:21:46 KST
- 가장 오래된 확인일: 2026-05-10
- 가장 최신 확인일: 2026-05-18

## AI 사용 메모

- 공개 JSON에는 객관 데이터만 있습니다.
- 현장 관찰값은 대화 중 임시 입력으로만 사용하고 공개 파일에 저장하지 않습니다.
- 라쿠엔 `1.111yen`과 일반 `1yen`의 회전 단위를 반드시 분리합니다.
- 시뮬레이터 해석 규칙은 `simulator-ai-context.md`를 함께 봅니다.
