# Contributing

고윤정 위키에 기여해 주셔서 감사합니다.

이 프로젝트의 핵심 목표는 아래 두 가지입니다.

- **"고윤정의 과거/현재/미래의 모든 것을 담는 위키"**
- **"완벽한 무인 자동화"**

## 기본 원칙

- 공식/1차 출처를 우선합니다.
- 루머/사생활/추측은 기록하지 않습니다.
- 원문 대량 복사 대신 링크 + 메타데이터를 사용합니다.
- 한글/영문 문서가 충돌하지 않도록 유지합니다.

## 개발 환경

```bash
git clone <repo-url>
cd goyoonjung-wiki
make venv
```

## 변경 전 점검

```bash
make check
./scripts/check_automation_health.sh
python3 scripts/compute_perfect_scorecard.py
```

## 문서 기여 우선 파일

- 메인 소개: `README.md`, `index.md`, `index.en.md`, `docs/README.md`
- 자동화 설명: `docs/ux-automation-system.md`, `docs/OPERATION_GUIDE.md`, `docs/ARCHITECTURE.md`
- 점수 체계: `docs/scoring.md`, `pages/perfect-scorecard.md`

문서 수정 시 확인할 항목:

- 스크립트/경로/명령이 실제 저장소와 일치하는지
- 한글/영문 설명이 의미상 일치하는지
- "100점"을 절대 완전성으로 오해하지 않도록 주석이 있는지

## 커밋 기준

- 변경 이유가 드러나는 커밋 메시지 사용
- 불필요한 대규모 포맷 변경 지양
- 자동 생성 산출물 수정 시 관련 문서/설명도 함께 업데이트

## 참고 문서

- 문서 포털: [`docs/README.md`](docs/README.md)
- 자동화 시스템: [`docs/ux-automation-system.md`](docs/ux-automation-system.md)
- Perfect Scorecard: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)
