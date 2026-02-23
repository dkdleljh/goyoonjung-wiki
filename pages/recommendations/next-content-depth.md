# 다음 콘텐츠 보강(추천) — 커버리지/품질/내용

> 목적: 커버리지(깊이)와 내용 품질을 함께 올리는 다음 작업 후보를 자동 리포트로 정리합니다.

## 1) Works: 공식 링크 2개 미만(보강 필요)
- `pages/works/everyone-fights-worthlessness.md`
  - 현재: MAA 1개
  - 대기: JTBC/TVING/Netflix 작품 공식 페이지(공개/확정 시 추가)

## 2) 인터뷰/광고/화보: ‘공식 근거로 치환 가능한 것’ 체크 가이드
- 인터뷰(기사)는 공식 대체가 없는 경우가 많습니다.
  - 대신 **원문 링크 + 키워드 중심 요약(2~3줄, 패러프레이즈)** 로 품질을 올립니다.
- 광고/캠페인은 대체로 ‘공식 채널’이 존재합니다.
  - 우선순위: 브랜드 공식 사이트/보도자료 → 공식 YouTube 업로드 → 공식 Instagram 포스트
- 화보는 매체(Elle/Vogue 등) 자체가 원문(1차)에 가까우므로, ‘공식’ 치환보다 **연도/브랜드/캠페인 페이지 연결**로 깊이를 올립니다.

## 3) ALT-PROOF 정리 원칙(안전)
- 본문 링크가 이미 플랫폼/방송사/소속사 등 **명백한 공식(1차)** 인 경우: ALT-PROOF 제거(가독성↑)
- 본문 링크가 언론/2차이거나, 공식 링크가 없어서 검증 흔적이 필요하면: ALT-PROOF 유지

## 4) 추천 루틴(주 2~3회)
1) micro backfill: gnews-sites → gnews-queries → youtube → i18n → promote → score
2) update_indexes + wiki_score
3) lint + quality_report + quality_alerts
4) 변경 있으면 1커밋
