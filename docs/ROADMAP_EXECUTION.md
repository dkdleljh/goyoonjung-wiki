# Roadmap Execution Tracker


## 한눈에 보기

- 한 줄 요약: (추가 필요)
- 핵심 링크: (추가 필요 — 공식/원문 우선)
- 상태: (추가 필요 — 근거 수준 S/A/2차/보강 필요)

이 파일은 ‘1~5단계 로드맵’을 실제 작업 단위로 쪼개서 체크하는 실행용 체크리스트입니다.

> 원칙: 한 번에 너무 크게 바꾸지 않고, **단계별로 (1)정책/구조 → (2)수집확장 → (3)정리/정확도 → (4)점수 → (5)운영자동화** 순서로 진행합니다.

## Stage 1) 기준 고정 (스키마/정책)
- [x] 콘텐츠 맵 문서화: `docs/content_map.md`
- [x] 편집/출처 정책: `docs/editorial_policy.md`
- [x] 점수 체계 초안: `docs/scoring.md`
- [ ] 위키 내에서 정책 문서 링크 연결(README / index에 링크)

## Stage 2) 커버리지 중심 수집 확장
- [ ] 공식/1차 출처 리스트를 config로 정리(도메인 allowlist/priority)
- [ ] 수집 스크립트에 ‘type/source_tier/status’ 메타데이터 부여
- [ ] 이벤트/화보/브랜드/인터뷰 소스 수집 경로 점검 및 누락 채우기

## Stage 3) 중복 제거/정리(품질)
- [ ] URL 정규화 규칙 강화(UTM 제거, mobile→canonical 등)
- [ ] 중복 탐지(제목/날짜/도메인 기반) + 대표 링크 선택
- [ ] 링크 헬스체크 강화(리다이렉트 추적, 재시도/타임아웃/백오프)

## Stage 4) 신뢰도/완성도 점수 고도화
- [ ] `wiki_score.py`를 `docs/scoring.md` 기준으로 재정렬
- [ ] S/A/B/C 출처 가중치 반영
- [ ] 메타데이터 누락/정책 위반 페널티 반영
- [ ] 리포트에 ‘검수 큐’(수동 확인 필요) 섹션 추가

## Stage 5) 운영 자동화/검수 루프
- [ ] run_daily_update.sh 파이프라인에 dedupe/link-health/score 단계 확실히 연결
- [ ] weekly link health + 품질 리포트 자동 생성 고정
- [ ] (선택) GitHub Action 스케줄링(크론) 또는 로컬 크론 가이드 정리
