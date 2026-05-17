# Idle-Death-Gamble

## 1. 프로젝트 개요
이 프로젝트는 오사카 여행 중 1엔 파친코 매장 후보와 현장 판단 기준을 정리하는 개인용 정적 리포트 생성기입니다.

- **GitHub에는 객관 데이터만 저장**: 매장 정보와 기종 정보 등 객관적인 데이터만 보관합니다.
- **방문 순위/최종 판단은 동적 분석**: 방문 순위와 추천 판단, final_decision은 리포트에 고정하지 않고, 사용자가 ChatGPT와 대화하면서 최신 조건에 따라 분석합니다.
- **당첨 예측기가 아님**: 당첨 예측이나 수익 보장이 아니라, 방문 전 객관적 정보 정리용 리포트입니다. 당첨 예측 표현은 금지됩니다.

## 2. GitHub 공개 데이터 정책

GitHub에 넣는 데이터:

- 점포명
- 기종명
- 레이트
- 대수
- 확률
- 보더라인
- 출처
- 확인일

GitHub에 넣지 않는 데이터:

- 방문 순위
- 추천 점수
- 오늘 어디 가라는 지시
- 당첨 가능성
- 승률 표현
- 원시 시뮬레이터 표본, 로컬 `results.csv`, 누적 시뮬레이터 기록
- 개인 예산, 실제 지출, 손익 기록
- 여행 일정, 항공/숙박 세부정보
- 신분증/여권 관련 식별값
- 예약 관련 식별값

## 3. 주요 기능
- **수동 데이터 수집**: GitHub Actions `workflow_dispatch`로 필요할 때만 수집합니다.
- **정적 리포트 제공**: 수집된 데이터를 바탕으로 GitHub Pages를 통해 모바일 친화적인 리포트를 제공합니다.
- **AI 입력용 공개 JSON**: `docs/latest.json`에는 원본 표와 함께 `ai_context`, `ai_compact_machines`를 생성해 대화형 분석에 바로 사용할 수 있게 합니다.
- **시뮬레이터 AI 컨텍스트**: `docs/simulator-ai-context.md`와 `docs/latest.json`의 `simulator_context`는 다른 AI가 GitHub만 보고도 로컬 시뮬레이터의 전제, 지표명, 해석 금지선을 이해할 수 있게 합니다.
- **현장 입력 템플릿**: `docs/onsite-input-template.md`는 현장 회전수와 표기 대조값을 AI에게 전달하기 위한 빈 양식입니다. 개인 일정이나 지출 기록은 넣지 않습니다.
- **시뮬레이터 결과 공유**: 로컬 CLI에서 공개 공유를 명시적으로 선택하면 `docs/latest-sim-results.*`에 최신 1개 집계표만 덮어씁니다. 로컬 `results.csv`는 gitignored이며 누적하지 않습니다.
- **오프라인 안전 정책**: 공격적인 웹 크롤링이나 외부 AI API 연동 없이, 정해진 룰 기반(Rule-based)으로만 동작합니다.
- **로컬 비공개 메모 지원**: `data/manual-notes.md`를 로컬에서 사용할 수 있지만 공개 저장소에는 커밋하지 않습니다.
- **개인 정보 보호 검증**: 공개 파일에 여행 일정이나 예약/항공/숙박 식별 정보가 섞이지 않도록 `scripts/validate_data.py`가 주요 패턴을 검사합니다.
- **수동 機種情報(기종 정보) 검증**: `data/namba-actual-1yen-lineup.json`의 매장, 기종명, 1엔 여부, 확률, RUSH(러시) 정보를 검사합니다.
- **파친코 전용 리포트**: 1엔과 エヴァ(에반게리온 계열) 중심으로 확인 후보를 정리합니다.
- **범위 제외**: 台番号(기기 번호)별 大当り(대당첨), 総回転(총 회전수), 差玉(구슬 수 증감), スランプグラフ(구슬 수 추이 그래프)는 절대 수집하지 않습니다.

## 4. 로컬 실행

기본 검증은 외부 사이트 수집 없이 실행됩니다.

```bash
python scripts/check.py
```

리포트 재생성까지 포함하려면:

```bash
python scripts/check.py --report
```

선택 개발 도구를 쓰려면 무료 도구인 Ruff, pytest, coverage.py를 설치합니다.

```bash
pip install -r requirements-dev.txt
python scripts/check.py --dev-tools
python scripts/check.py --coverage
```

```bash
python scripts/validate_data.py
python scripts/collect.py
python scripts/analyze.py
python scripts/build_report.py
```

`python`이 없으면 `python3`로 실행해도 됩니다.

주요 공개 출력:

- `docs/index.html`: 모바일용 정적 리포트
- `docs/latest.json`: AI/웹용 구조화 데이터
- `docs/ai-context.md`: AI 활용 규칙과 필드 설명
- `docs/simulator-ai-context.md`: 시뮬레이터 결과를 AI가 해석할 때 필요한 공개 규칙과 빈 입력 템플릿
- `docs/latest-sim-results.html`: 명시적으로 공유한 최신 1개 시뮬레이터 집계표
- `docs/onsite-input-template.md`: 현장 관찰값 입력 템플릿

시뮬레이터 스펙 회귀 테스트:

```bash
python -m unittest discover -s tests
```

난바 저대여 실제 라인업은 `data/namba-actual-1yen-lineup.json`의 `machines` 배열에 추가합니다.

```json
{
  "store_id": "rakuen_namba",
  "store_name": "楽園なんば店",
  "store_name_ko": "라쿠엔 난바점",
  "machine_name": "新世紀エヴァンゲリオン〜未来への咆哮〜",
  "machine_name_ko": "신세기 에반게리온 미래로의 포효",
  "rate": "1.111yen",
  "category": "eva_middle",
  "spec_type": "middle",
  "initial_probability": "1/319.7",
  "rush_type": "ST",
  "machine_count": 6,
  "source_type": "dmm",
  "install_source": "dmm_pachitown",
  "checked_at": "2026-05-12",
  "memo": "공개 설치 대수 확인"
}
```

## 5. GitHub Pages 설정
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: /docs
- **게시 주소**: https://khskyasu-maker.github.io/Idle-Death-Gamble/

## 6. 주의사항
- 이 프로젝트는 파친코 결과를 예측하거나 수익을 보장하지 않습니다.
- 파친코는 사행성 오락이므로 예산을 정하고 책임 있게 이용해야 합니다.
- 실제 機種情報(기종 정보)와 1円(1엔) 라인업은 현장 또는 사용자가 직접 확인한 출처를 기준으로 입력해야 합니다.
- `pachinko-sim/`은 로컬 체감 리스크용 시뮬레이터입니다. 공개 리포트의 방문 순위, 추천 점수, 당첨 예측 데이터로 사용하지 않습니다.
- 공개 GitHub에는 시뮬레이터의 설명, 전제, 빈 결과 입력 템플릿, 명시적으로 공유한 최신 1개 집계표만 둡니다. 원시 표본, 로컬 CSV, 방문 판단, 개인 예산/시간 판단은 로컬 메모나 대화에서만 다룹니다.
- 여행 일정, 숙박 세부정보, 항공 이동 정보, 예약 관련 식별값은 `private/` 또는 `data/manual-notes.md` 같은 gitignored 경로에만 보관합니다.

## 7. 데이터 출처 (Data Sources)
- **DMMぱちタウン / 피타운**
  - URL: https://p-town.dmm.com/
  - 용도: 점포 정보, 설치 기종, 레이트, 설치 대수 확인
  - 주의: 台番号별 상세 데이터는 앱/대응점포/현장 확인 필요

- **ちょんぼりすた / 촌보리스타**
  - URL: https://chonborista.com/
  - 용도: 기종별 스펙, 도입일, 확률, RUSH, LT, 보더라인, 연출 정보 확인
  - 주의: 점포별 설치 대수 확인용이 아님

## 8. 보더라인 (Borderline) 설명
- 보더라인은 기대값상 기준 회전수입니다.
- 실제 수익을 보장하지 않습니다.
- 1円은 200玉당 회전수로 표시합니다.
- 楽園なんば店의 1.111円은 200円=180玉이므로 별도의 환산값을 사용합니다.
- 현장에서는 첫 1,000円 또는 200円 단위로 실제 회전수를 확인해야 합니다.

**예시:**
- 1円 보더: 13.4회/200玉
- 1.111円 환산 보더: 12.1회/180玉
