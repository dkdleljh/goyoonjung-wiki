# docs/ 문서 포털

`docs/`는 고윤정 위키의 운영 원칙, 자동화 구조, 점수 모델을 설명하는 문서 모음입니다.

프로젝트 목표:

- **"고윤정의 과거/현재/미래의 모든 것을 담는 위키"**
- **"완벽한 무인 자동화"**

## 먼저 읽기

1. 자동화 전체 흐름: [`ux-automation-system.md`](ux-automation-system.md)
2. 운영 절차: [`OPERATION_GUIDE.md`](OPERATION_GUIDE.md)
3. 시스템 구조: [`ARCHITECTURE.md`](ARCHITECTURE.md)
4. 점수 체계: [`scoring.md`](scoring.md)

## Perfect Scorecard 관련 문서

- 결과 페이지: [`../pages/perfect-scorecard.md`](../pages/perfect-scorecard.md)
- 계산 스크립트: `../scripts/compute_perfect_scorecard.py`
- 건강 점검: `../scripts/check_automation_health.sh`

핵심 해석:

- A/B는 시스템 준비도에 가깝습니다.
- C는 실제 축적량이라 시간이 지날수록 달라집니다.
- D는 품질/링크/출처 체계 건강도를 보여줍니다.
- **True 100% completeness cannot be proven.**

## 자동화 파이프라인 문서 연결

- Daily update + backfill + observability 개요: [`ux-automation-system.md`](ux-automation-system.md)
- 운영 체크리스트/실행 절차: [`OPERATION_GUIDE.md`](OPERATION_GUIDE.md)

## 정확성 원칙

- 문서에 적는 명령은 **실제로 존재하는 스크립트만** 사용합니다.
- 저장소 구조/링크가 바뀌면 `README.md`, `index.md`, `index.en.md`, `pages/hub*.md`까지 함께 동기화합니다.
- 외부 링크는 변할 수 있으므로, 기본은 **공식/1차 링크 우선 + 링크 건강검진**으로 관리합니다.
