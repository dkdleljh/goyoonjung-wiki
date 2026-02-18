# Scoring Model

이 프로젝트는 운영 상태를 `A/B/C/D` 4축으로 점검합니다.

실제 결과는 [`../pages/perfect-scorecard.md`](../pages/perfect-scorecard.md)에 기록되며,
`python3 scripts/compute_perfect_scorecard.py`로 갱신합니다.

## A/B/C/D 정의

- **A. Perfect wiki coverage system**: 채널 다양성, 랜딩 페이지, 탐지 리포트 준비도
- **B. Perfect unmanned automation**: 일일 러너, 복원력, 관측성 준비도
- **C. Unbeatable information volume**: 실제 누적량과 확장 잠재력(시간에 따라 증가)
- **D. Perfect quality**: 품질 부채, 링크 건강, 린트, 출처 체계

## 중요한 해석 주의

- 점수 100은 "현 시점의 지표상 상태"를 뜻합니다.
- **현실 세계 정보의 절대 100% 완전성은 증명할 수 없습니다.**
- 따라서 장기 누적, 안정성, 감사 가능성(auditable)을 핵심 목표로 둡니다.

## 관련 경로

- 결과 페이지: `../pages/perfect-scorecard.md`
- 계산 스크립트: `scripts/compute_perfect_scorecard.py`
- 건강 점검: `scripts/check_automation_health.sh`
- 자동화 개요: [`ux-automation-system.md`](ux-automation-system.md)
