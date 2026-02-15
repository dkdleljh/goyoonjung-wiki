# ARCHITECTURE.md

## 고윤정 위키 아키텍처

이 문서는 고윤정 위키 프로젝트의 시스템 아키텍처를 설명합니다.

---

## 전체 구조

```
goyoonjung-wiki/
├── pages/          # 위키 페이지 (마크다운)
├── news/           # 날짜별 로그
├── sources/        # 출처/모니터링
├── scripts/        # 자동화 스크립트
├── data/           # SQLite DB
├── backups/        # 백업
├── config/         # 설정
├── tests/          # 테스트
└── .cache/         # 캐시
```

---

## 모듈 설계

### 1. 수집 모듈 (`scripts/auto_collect_*.py`)

| 모듈 | 역할 | 데이터 소스 |
|------|------|------------|
| `auto_collect_visual_links.py` | 화보/이미지 링크 | 웹 스크래핑 |
| `auto_collect_google_news.py` | 뉴스 수집 | Google News RSS |
| `auto_collect_agency.py` | 소속사 정보 | MAA |
| `auto_collect_encyclopedia.py` | 백과사전 | Wikipedia API |
| `auto_collect_schedule.py` | 일정 추정 | 뉴스 분석 |

### 2. 처리 모듈 (`scripts/rebuild_*.py`)

| 모듈 | 역할 |
|------|------|
| `rebuild_work_link_candidates.py` | 작품 링크 후보 생성 |
| `rebuild_timeline_narrative.py` | 타임라인 내레이션 |
| `rebuild_interviews_year_index.py` | 인터뷰 연도별 인덱스 |
| `rebuild_awards_official_cache.py` | 수상 캐시 |

### 3. 승격 모듈 (`scripts/promote_*.py`)

| 모듈 | 역할 |
|------|------|
| `promote_safe_metadata.py` | 안전한 메타데이터 승격 |
| `promote_endorsement_dates.py` | 광고 날짜 승격 |
| `promote_youtube_dates.py` | YouTube 날짜 승격 |

### 4. 유틸리티 모듈

| 모듈 | 역할 |
|------|------|
| `cache.py` | TTL 캐시 + Rate Limiter |
| `db_manager.py` | SQLite 관리 |
| `lock_manager.py` | 실행 잠금 |
| `security.py` | 입력 검증/샌티제이션 |

---

## 데이터 흐름

```
[수집] → [처리] → [승격] → [인덱스] → [출력]
  ↓        ↓        ↓        ↓
 RSS/     파싱/   필터링/  정렬/
 스크래핑  변환     검증     생성
```

---

## 실행 스케줄

| 시간 | 작업 |
|------|------|
| 09:00 | 일일 자동 업데이트 |
| 09:10 | 백업 생성 |
| 21:00 | Discord 요약 |
| 매주 일 | 링크 건강검진 |

---

## 주요 설계 결정

### 1. 링크 중심 아카이빙
- 원문 복사 대신 링크 + 메타데이터
- 저작권 이슈 회피

### 2. 근거 수준 표시
- S/A급: 공식/원문
- 2차 참고: 언론 등
- 보강 필요: 미확인

### 3. 무인 운영
- Lock 기반 동시 실행 방지
- 디바운스 (10분)
- 자동 재시도

---

## 보안 설계

- 입력 검증: `security.py`
- URL 샌티제이션
- 경로 탐색 방지
- Rate Limiting

---

## 성능 최적화

- TTL 캐시 (30분 기본)
- Rate Limiter
- SQLite 인덱싱
- 배치 처리

---

## 테스트 전략

- pytest 기반
- Mock을 통한 단위 테스트
- 임시 디렉토리 활용
