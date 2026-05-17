# Simulator Refactor Plan

## 목적

`pachinko-sim`은 현재 동작은 유지하고 있지만, 회전율/보더라인/레이트 환산과 출력 통계가 여러 파일에 흩어져 있다. 다음 리팩터링의 목표는 다음과 같다.

- 보더라인을 당첨 확률 보정값이 아니라 회전율 기준선으로만 취급한다.
- `1000엔당 회전수`, `250玉당 회전수`, `200玉/180玉당 회전수`, `보더 +/-`를 같은 내부 단위로 안전하게 환산한다.
- 1円과 1.111円을 같은 절대 현금 회전수로 비교할 때 생기는 착시를 줄인다.
- CLI, 시뮬레이션 엔진, 통계 출력, 점포 라인업 어댑터의 책임을 분리한다.
- 공개 `data/`와 `docs/`에는 런타임 판단/추천/결과를 쓰지 않는다.

## 외부 기준 요약

최근 조사 기준으로 1円 파칭코 회전율은 보통 `1000엔당 회전수`로 말한다. 커뮤니티나 해설 글에서는 `1k 70回`, `250玉で17.5回`, `200玉で14回`처럼 표현이 섞인다.

- 1円: `1000엔 = 1000玉`, 그래서 `70회/1000엔 = 17.5회/250玉 = 14회/200玉`
- 1.111円: `1000엔 = 900玉`, 그래서 같은 `70회/1000엔`이라도 1円보다 구슬 1발당 헤소 입상 품질이 높다.
- 일본 해설 자료들은 대체로 1円 기준 `70회/1000엔`을 합격선, `60회`를 타협선, `50회 이하`를 위험권, `80회 이상`을 우수 조건으로 설명한다.
- 회전율은 1000엔 단위에서는 표본 흔들림이 크다. 현장 입력은 `첫 1000엔 관측값`과 `3000~5000엔 누적 관측값`을 분리해 받는 편이 낫다.

참고 URL:

- `https://www.katsuwin.ai/blog/1pachi-spin-rate/`
- `https://paticalc.net/`
- `https://www.pachikachi.com/column/border.html`

## 현재 구조 조사

파일 크기 기준 현재 주요 병목은 다음이다.

| 파일 | 현재 책임 | 문제 |
|---|---|---|
| `main.py` | CLI 입력, 모드 선택, 시나리오 생성, 결과 출력 호출 | 입력 파싱과 실행 오케스트레이션이 결합됨 |
| `simulator.py` | 세션 상태머신, 전략, 매트릭스 실행, 상수 | 엔진과 시나리오 빌더가 같이 있음 |
| `result.py` | 통계 계산, 보더 판정, ASCII 테이블, CSV 저장 | 계산/표시/저장이 한 파일에 집중됨 |
| `start_gate.py` | 구슬->헤소 입상, 회전율 표본 | 좋은 분리지만 단위 환산 책임은 부족함 |
| `store_comparison.py` | 점포별 같은 기종 비교, 레이트 환산 | 동일 보더 마진 비교가 없음 |
| `stores.py` | 라인업 로딩, 보더 환산, 미지원 후보 표시 | 보더 환산과 관찰 후보 정책이 결합됨 |
| `machines.py` | 기종 모델 전체 | 파일이 크지만 고정 스펙 DB라 우선순위는 낮음 |

현재 보더는 주로 다음 위치에서 쓰인다.

- `stores.py`: `border_1yen_per_200`, `border_1_111yen_per_180`을 `border_spins_per_1000yen`으로 환산
- `result.py`: 보더 대비 +/- 표시, 점수 감점, 경고 문구
- `start_gate.py`: 세션 회전율 표본의 상하한 보조 anchor
- `main.py`: 선택 기종의 보더를 실행 함수에 전달

문제는 실행 기본 축이 여전히 `SPIN_RATE_CASES = [50, 60, 70, 80, 90, 100]`이라는 점이다. 이 방식은 빠르게 감을 잡기에는 좋지만, 보더가 55회인 기종과 80회인 기종을 같은 `80회/1000엔` 조건으로 비교하게 만든다.

## 단위 정책

내부 표준 단위는 계속 `spins_per_1000yen`으로 둔다. 다만 입력과 출력에는 다음 보조 단위를 명확히 노출한다.

| 입력/표시 단위 | 내부 변환 |
|---|---|
| `1000엔당 회전수` | 그대로 사용 |
| `200엔당 회전수` | `value * 5` |
| `250玉당 회전수` | `value * (rented_balls_per_1000yen / 250)` |
| `200玉당 회전수` | `value * (rented_balls_per_1000yen / 200)` |
| `180玉당 회전수` | `value * (rented_balls_per_1000yen / 180)` |
| `사용 금액 + 실제 회전수` | `spins / yen * 1000` |
| `보더 +/-` | `border_spins_per_1000yen + margin` |

예시:

- 1円에서 `17.5회/250玉` -> `17.5 * 4 = 70회/1000엔`
- 1.111円에서 `14회/180玉` -> `14 * 5 = 70회/1000엔`
- 1.111円에서 `17.5회/250玉` -> `17.5 * (900 / 250) = 63회/1000엔`

## 보더라인 정책

보더라인은 당첨 확률을 바꾸지 않는다. 보더는 회전율의 기준선이다.

권장 판정:

| 보더 대비 | 판정 |
|---:|---|
| `<= -10` | 나쁨 |
| `-10 ~ -5` | 불리 |
| `-5 ~ +0` | 보더 근처이나 부족 |
| `+0 ~ +5` | 보더 근처 |
| `+5 ~ +10` | 좋음 |
| `>= +10` | 매우 좋음 |

절대값 `70회 미만` 경고는 보더 미확정 기종에서만 fallback으로 쓴다. 보더가 있는 기종에서는 `65회`라도 보더가 `55회`면 좋은 조건일 수 있다.

## 제안 모듈 구조

1차 리팩터링은 파일 이동을 최소화하고, 새 모듈을 추가한 뒤 기존 함수가 새 모듈을 호출하도록 한다.

```text
pachinko-sim/
├── rotation.py          # 회전율/보더/단위 환산
├── scenarios.py         # 단일/매트릭스/예산/전략 시나리오 빌더
├── metrics.py           # calculate_metrics, 신뢰구간, 조건부 플러스 통계
├── output_tables.py     # ASCII 테이블 row 생성과 출력 텍스트
├── csv_export.py        # results.csv append 전용
├── cli.py               # 입력/선택 UI
├── main.py              # thin entry point
├── simulator.py         # 순수 세션 엔진 중심으로 축소
├── start_gate.py        # 구슬->헤소 입상 표본 유지
├── store_comparison.py  # 점포 비교 시나리오, 보더 마진 모드 추가
└── stores.py            # 라인업 어댑터만 남기기
```

### `rotation.py`

새로 만들 핵심 모듈이다.

책임:

- 레이트별 대여 구슬 계산
- 회전율 입력 단위 환산
- 보더 대비 마진 계산
- 보더 기준 회전율 케이스 생성
- 현실감 라벨 생성

제안 API:

```python
BORDER_MARGIN_CASES = [-10, -5, 0, 5, 10]

def spins_from_yen_observation(spins: float, yen: float) -> float: ...
def spins_from_ball_unit(spins: float, balls: float, lend_rate: float) -> float: ...
def spins_from_border_margin(border_spins: float, margin: float) -> float: ...
def border_margin(spins_per_1000y: float, border_spins: float | None) -> float | None: ...
def border_case_rates(border_spins: float | None, fallback_rates: list[int] | None = None) -> list[dict]: ...
def rotation_reality_label(spins_per_1000y: float, border_spins: float | None) -> str: ...
```

### `scenarios.py`

`simulator.py`의 매트릭스 실행 함수들을 옮긴다.

대상:

- `run_matrix_simulation`
- `run_budget_matrix`
- `run_strategy_matrix`

추가:

- `run_border_margin_matrix`
- `run_budget_matrix_at_border_margin`

시나리오 row에는 다음 필드를 넣는다.

```python
{
    "rotation_basis": "absolute" | "border_margin" | "ball_quality",
    "rotation_label": "보더+5",
    "spins_per_1000y": 72.5,
    "border_spins_per_1000yen": 67.5,
    "border_margin": 5.0,
}
```

### `metrics.py`

`result.py`의 통계 계산을 분리한다.

대상:

- `calculate_metrics`
- Wilson CI
- 평균/분위수 CI
- 조건부 플러스 통계
- 이론 무당첨률 from results

출력 포맷은 넣지 않는다. 숫자만 반환한다.

### `output_tables.py`

`result.py`의 ASCII 테이블/문구 생성 책임을 옮긴다.

대상:

- `build_ascii_table`
- `print_ascii_table`
- `yen`, `pct`, `spins_text`
- 각 모드별 row builder

긴 함수는 `print_*` 하나에 모든 것을 쌓지 말고 다음처럼 쪼갠다.

```python
def core_summary_rows(machine, metrics): ...
def risk_detail_rows(machine, metrics): ...
def useful_profit_rows(metrics): ...
def border_rotation_rows(scenario, metrics): ...
```

### `csv_export.py`

CSV 저장은 사용자가 명시적으로 선택할 때만 append한다는 정책을 유지한다. `result.py`에서 분리해 테스트하기 쉽게 만든다.

### `cli.py`와 `main.py`

`main.py`는 얇은 entry point로 만든다.

```python
from cli import run_cli

if __name__ == "__main__":
    run_cli()
```

CLI에는 회전율 입력 모드를 추가한다.

```text
회전율 입력 방식
1: 1000엔당 회전수
2: 200엔당 회전수
3: 250玉당 회전수
4: 사용 금액 + 실제 회전수
5: 보더 기준 +/- 회전
```

## 모드별 개선안

### 모드 2: 리스크 평가

현재는 반복 횟수 고정 `1000회`이다. 입력을 받도록 바꾼다.

- 기본 반복: `5000`
- 보더가 있으면 기본 회전: `보더+0`
- 좋은 조건 프리셋: `보더+5`

### 모드 3: 회전율 매트릭스

기본을 절대 회전율에서 보더 기준으로 변경한다.

현재:

```text
50 / 60 / 70 / 80 / 90 / 100
```

수정:

```text
보더-10 / 보더-5 / 보더±0 / 보더+5 / 보더+10
```

보더 미확정이면 기존 절대값 fallback을 쓴다.

### 모드 5: 예산 비교

기본 `80회/1000엔`은 후한 조건이다. 기본을 다음 중 하나로 둔다.

- 보더가 있으면 `보더+0`
- 보더가 없으면 `70회/1000엔`

사용자에게는 `보더+5` 같은 마진 입력도 허용한다.

### 모드 6: 모델 프로파일

프로파일은 공개 스펙 검증 성격이 강하므로 다음 세 조건을 자동 비교한다.

- `보더-5`
- `보더±0`
- `보더+5`

기종별 대당첨/연속/실익조건이 보더 주변에서 어떻게 변하는지 보여준다.

### 모드 7: 가게별 같은 기종 비교

현재 비교:

- 동일 1000엔 회전수
- 동일 헤소 입상 품질

추가:

- 동일 보더 마진

예: 모든 점포를 `각 점포의 보더+5회` 조건으로 비교한다. 이 방식이 라쿠엔 1.111円과 123/HIPS 1円을 가장 공정하게 비교한다.

## 단계별 작업 순서

### 현재 구현 상태

- 완료: `rotation.py` 추가, 1000엔/200엔/250玉/180玉/보더 마진 환산 테스트 추가
- 완료: 보더 판정/경고/상대 점수 로직을 보더 기준으로 조정
- 완료: 보더가 있는 기종의 매트릭스/전략 비교 기본축을 `보더-10/-5/±0/+5/+10`으로 변경
- 완료: 가게별 비교에 `동일 보더 마진` 모드 추가
- 완료: CLI에 `1000엔`, `200엔`, `250玉`, `사용 금액+회전수`, `보더 +/-` 회전율 입력 방식을 추가
- 완료: 리스크 평가 모드 반복 횟수를 고정 1000회에서 사용자 입력형 기본 5000회로 변경
- 남음: `metrics.py`, `output_tables.py`, `csv_export.py`, `cli.py`, `scenarios.py`로 추가 분리

### 1단계: 회전율/보더 모듈 추가

- `rotation.py` 추가
- 기존 `start_gate.rented_balls_per_1000yen`은 유지하되, 회전율 단위 환산은 `rotation.py`에서 담당
- 단위 테스트 추가

검증:

- 1円 `17.5회/250玉 = 70회/1000엔`
- 1円 `14회/200玉 = 70회/1000엔`
- 1.111円 `14회/180玉 = 70회/1000엔`
- 1.111円 `17.5회/250玉 = 63회/1000엔`

### 2단계: 보더 판정 로직 이동

- `result.border_label`, `border_delta`, `border_adjustment`, `operating_warning`의 회전율 판정 부분을 `rotation.py`로 이동
- `70회 미만` 절대 경고는 보더 미확정 fallback으로 제한

### 3단계: 보더 기준 매트릭스 추가

- `run_border_margin_matrix` 추가
- 모드 3 기본을 보더 기준으로 변경
- 출력에 `조건`, `입력회전`, `보더+/-`, `보더비` 표시

### 4단계: 입력 방식 확장

- CLI에 회전율 입력 방식 선택 추가
- 1000엔/200엔/250玉/사용금액+회전수/보더마진 입력을 모두 내부 `spins_per_1000y`로 변환

### 5단계: 점포 비교 보강

- `store_comparison.py`에 `border_margin` 비교 모드 추가
- 같은 마진 조건에서 각 점포의 실제 `spins_per_1000y`가 달라지는 것을 출력

### 6단계: 통계/출력 분리

- `metrics.py`로 순수 통계 이동
- `output_tables.py`로 표시 이동
- `result.py`는 호환 래퍼로 잠시 유지한 뒤 축소

### 7단계: 문서/테스트 정리

- `README.md` 실행 설명 갱신
- `ARCHITECTURE.md`에 새 모듈 구조 반영
- `tests/test_simulator_specs.py`를 회전율/보더/통계 테스트 파일로 분리

## 테스트 계획

필수 단위 테스트:

- 회전율 단위 변환
- 보더 마진 케이스 생성
- 보더 미확정 fallback
- 1円/1.111円 동일 헤소 품질 환산
- 동일 보더 마진 점포 비교
- 기존 머신 스펙 검증 유지
- 조건부 플러스 통계 유지

실행 체크:

```bash
python3 -m py_compile scripts/collect.py scripts/analyze.py scripts/build_report.py scripts/validate_data.py scripts/utils.py scripts/term_notes.py pachinko-sim/main.py pachinko-sim/machines.py pachinko-sim/machine_traits.py pachinko-sim/sim_terms.py pachinko-sim/spec_benchmarks.py pachinko-sim/start_gate.py pachinko-sim/rotation.py pachinko-sim/store_comparison.py pachinko-sim/model_checks.py pachinko-sim/result.py pachinko-sim/simulator.py pachinko-sim/stores.py
python3 -m unittest discover -s tests
python3 scripts/validate_data.py
python3 scripts/analyze.py
python3 scripts/build_report.py
```

## 리스크와 주의점

- 보더는 고정 스펙/교환율/출옥 기준에 따라 달라질 수 있다. `border_confidence`와 `border_source`를 계속 출력해야 한다.
- 1.111円 환산은 반드시 900玉/1000엔 기준을 유지한다.
- 회전율 표본 변동은 실제 못 상태가 아니라 현장 관측 불확실성을 근사한 것이다.
- `results.csv`는 자동 생성/덮어쓰기를 하지 않는다.
- 공개 `data/`와 `docs/`에 시뮬 결과, 추천, 방문 순위, 개인 예산 판단을 쓰지 않는다.

## 완료 기준

- 사용자는 절대 회전수뿐 아니라 `보더+5`, `250玉당 17.5회`, `200엔당 14회`, `1000엔에 72회`를 모두 입력할 수 있다.
- 모든 출력은 `입력 회전수`, `보더 대비`, `보더비`, `레이트 환산 단위`를 함께 보여준다.
- 라쿠엔 1.111円과 1円 점포 비교에서 `동일 1000엔 회전수`, `동일 헤소 입상 품질`, `동일 보더 마진`을 명확히 구분한다.
- 기존 단위 테스트와 시뮬레이션 모델 검증이 통과한다.
