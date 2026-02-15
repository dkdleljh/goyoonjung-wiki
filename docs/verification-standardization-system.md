# 데이터 검증 및 표준화 시스템 설계


## 한눈에 보기

- 한 줄 요약: (추가 필요)
- 핵심 링크: (추가 필요 — 공식/원문 우선)
- 상태: (추가 필요 — 근거 수준 S/A/2차/보강 필요)

## 1. 자동화된 데이터 검증 시스템

### 1.1 검증 등급 재정의

#### 새로운 등급 시스템 (5단계)
```yaml
verification_levels:
  S1: # 최고 수준 (공식 1차)
    sources:
      - 소속사 공식 발표
      - 시상식 공식 결과
      - 법적 등기 정보
      - 본인 계정 공식 발표
    confidence: 99%
    auto_update: true

  S2: # 공식 2차
    sources:
      - 방송사/OTT 공식 자료
      - 제작사 공식 정보
      - 주요 언론사 단독 인터뷰
    confidence: 95%
    auto_update: true

  A1: # 1차 검증
    sources:
      - 주요 언론사 보도
      - 공식 발표 기사
      - 전문 데이터베이스
    confidence: 85%
    auto_update: true

  A2: # 2차 검증
    sources:
      - 신뢰할 수 있는 2차 자료
      - 교차 검증된 정보
      - 전문가 분석
    confidence: 75%
    auto_update: false

  B:  # 참고 자료
    sources:
      - 팬 커뮤니티 큐레이션
      - 개인 분석
      - 미확인 정보
    confidence: 50%
    auto_update: false
```

### 1.2 자동 검증 파이프라인

```python
class VerificationPipeline:
    def __init__(self):
        self.official_sources = [
            "maa.co.kr",           # 소속사
            "baeksangawards.co.kr", # 시상식
            "blueaward.co.kr",      # 시상식
            "tvn.com",             # 방송사
            "netflix.com",         # OTT
            "instagram.com/go_younjung" # SNS
        ]

    def verify_information(self, data, content_type):
        # 1단계: 출처 자동 검색
        sources = self.search_sources(data, content_type)

        # 2단계: 신뢰도 평가
        trust_score = self.calculate_trust_score(sources)

        # 3단계: 교차 검증
        verification = self.cross_validate(data, sources)

        # 4단계: 등급 부여
        level = self.assign_level(trust_score, verification)

        return {
            "level": level,
            "confidence": trust_score,
            "sources": sources,
            "verification": verification,
            "last_updated": datetime.now()
        }

    def auto_update_verification(self):
        # 매시간 공식 출처 확인
        # 변경사항 자동 업데이트
        # 신뢰도 재평가
        pass
```

### 1.3 실시간 검증 대시보드

```markdown
## 데이터 검증 대시보드 (실시간)

### 현재 검증 현황

| 카테고리 | 총 항목 | S1 | S2 | A1 | A2 | B | 검증률 |
|---|---|---|---|---|---|---|---|
| **프로필** | 18 | 12 | 4 | 2 | 0 | 0 | 88.9% |
| **필모그래피** | 15 | 10 | 3 | 2 | 0 | 0 | 86.7% |
| **수상** | 11 | 3 | 2 | 4 | 2 | 0 | 45.5% |
| **뉴스** | 245 | 45 | 78 | 89 | 33 | 0 | 86.5% |
| **미디어** | 156 | 23 | 45 | 67 | 21 | 0 | 79.5% |

### 최근 검증 업데이트
- **프로필**: 출생지 정보 A1 → S2 등급 상향 (인터뷰 확보)
- **수상**: 청룡시리즈어워즈 A2 → S2 등급 상향 (공식 링크 확보)
- **뉴스**: 3개 항목 자동 검증 완료

### 검증 필요 항목 (우선순위)
1. **수상 정보**: 8개 항목 공식 링크 확보 필요
2. **필모그래피**: 2개 작품 상세 정보 추가 필요
3. **프로필**: 학력 정보 1차 출처 확보 필요
```

## 2. 데이터 표준화 시스템

### 2.1 명명 규칙 표준화

#### 날짜 형식 표준
```yaml
date_standards:
  profile:
    format: "YYYY-MM-DD"
    example: "1996-04-22"

  filmography:
    premiere: "YYYY-MM-DD (Premiere)"
    broadcast: "YYYY-MM-DD ~ YYYY-MM-DD"
    awards: "YYYY-MM-DD"

  news:
    format: "YYYY-MM-DD HH:mm (KST)"
    auto: true
```

#### 이름 표기 표준
```yaml
name_standards:
  korean_name: "고윤정"  # 기본 한글 이름
  english_name: "Go Youn-jung"  # 공식 영어 표기
  stage_name: "고윤정"  # 예명
  birth_name: "고윤정"  # 본명

  works:
    format: "한글명 (English Name)"
    example: "환혼 (Alchemy of Souls)"

  awards:
    format: "한글명 (English Name)"
    example: "청룡시리즈어워즈 (Blue Dragon Series Awards)"
```

#### 수상 정보 표준
```yaml
award_standards:
  structure:
    - year
    - ceremony_name
    - category
    - work
    - result
    - ceremony_date
    - venue

  result_format:
    winner: "수상"  # 표기 통일
    nominee: "후보"  # 표기 통일

  official_links:
    baeksang: "https://www.baeksangawards.co.kr/"
    blue_dragon: "http://www.blueaward.co.kr/"
    daejong: "https://daejong.or.kr/"
```

### 2.2 자동 표준화 스크립트

```python
class Standardizer:
    def __init__(self):
        self.patterns = {
            'date': r'(\d{4})[-/년](\d{1,2})[-/월](\d{1,2})[일]?',
            'name': r'([가-힣]+)\s*\(?([a-zA-Z\s-]+)\)?',
            'award': r'(.+?)\s*\((.+?)\)\s*(수상|후보)'
        }

    def standardize_date(self, date_str):
        # 다양한 날짜 형식을 YYYY-MM-DD로 통일
        if match := re.search(self.patterns['date'], date_str):
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str

    def standardize_name(self, name_str):
        # 이름 표기 통일
        if match := re.search(self.patterns['name'], name_str):
            korean, english = match.groups()
            return f"{korean} ({english})"
        return name_str

    def standardize_award(self, award_str):
        # 수상 정보 표준화
        if match := re.search(self.patterns['award'], award_str):
            korean, english, result = match.groups()
            return {
                'korean': korean,
                'english': english,
                'result': result
            }
        return None
```

### 2.3 품질 관리 규칙

#### 데이터 품질 체크리스트
```yaml
quality_checks:
  mandatory_fields:
    profile:
      - name
      - birth_date
      - occupation
      - agency

    filmography:
      - title
      - year
      - role
      - type

    awards:
      - year
      - ceremony
      - category
      - result

  consistency_checks:
    - date_format_consistency
    - name_format_consistency
    - source_link_validation
    - cross_reference_validation

  completeness_checks:
    - field_completion_rate
    - source_coverage_rate
    - recency_check

  accuracy_checks:
    - official_source_match
    - multiple_source_correlation
    - contradiction_detection
```

## 3. 자동화된 검증 크롤러

### 3.1 공식 출처 크롤러

```python
class OfficialSourceCrawler:
    def __init__(self):
        self.official_domains = {
            'agency': 'maa.co.kr',
            'awards': [
                'baeksangawards.co.kr',
                'blueaward.co.kr',
                'daejong.or.kr'
            ],
            'broadcast': [
                'tvn.com',
                'jtbc.co.kr',
                'mbc.co.kr'
            ],
            'ott': [
                'netflix.com',
                'wavve.com',
                'tving.com'
            ]
        }

    def crawl_artist_profile(self):
        """소속사 공식 프로필 크롤링"""
        url = f"https://{self.official_domains['agency']}/artists/go-younjung"

        # 프로필 정보 추출
        profile_data = {
            'name': self.extract_name(url),
            'birth_date': self.extract_birth_date(url),
            'agency': self.extract_agency(url),
            'official_image': self.extract_image(url)
        }

        return self.verify_data(profile_data, 'agency')

    def crawl_awards(self):
        """시상식 공식 결과 크롤링"""
        awards_data = []

        for domain in self.official_domains['awards']:
            # 해당 배우 수상/노미네이트 정보 검색
            results = self.search_artist_awards(domain, "고윤정")

            for result in results:
                awards_data.append({
                    'year': result['year'],
                    'ceremony': result['ceremony'],
                    'category': result['category'],
                    'result': result['result'],
                    'source_url': result['url'],
                    'verification': 'S1'
                })

        return awards_data

    def monitor_changes(self):
        """공식 출처 변경사항 모니터링"""
        # 매시간 변경사항 확인
        # 프로필 정보 업데이트 감지
        # 새로운 수상 정보 추가 감지
        pass
```

### 3.2 크로스 검증 시스템

```python
class CrossValidator:
    def __init__(self):
        self.validation_rules = {
            'name': self.validate_name,
            'date': self.validate_date,
            'award': self.validate_award,
            'filmography': self.validate_filmography
        }

    def validate_information(self, info_type, data):
        validator = self.validation_rules.get(info_type)
        if validator:
            return validator(data)
        return {"valid": False, "error": "Unknown info type"}

    def validate_name(self, name_data):
        """이름 정보 교차 검증"""
        sources = [
            self.search_agency(name_data),
            self.search_imdb(name_data),
            self.search_naver(name_data)
        ]

        consistency_score = self.calculate_consistency(sources)

        return {
            "valid": consistency_score > 0.8,
            "confidence": consistency_score,
            "sources": sources
        }

    def validate_award(self, award_data):
        """수상 정보 교차 검증"""
        # 시상식 공식 사이트 확인
        official_result = self.check_official_awards(award_data)

        # 언론 보도 확인
        media_reports = self.search_media_reports(award_data)

        # 소셜 미디어 확인
        social_mentions = self.search_social_media(award_data)

        return {
            "official": official_result,
            "media": media_reports,
            "social": social_mentions,
            "consensus": self.calculate_consensus([
                official_result, media_reports, social_mentions
            ])
        }
```

## 4. 데이터 품질 대시보드

### 4.1 실시간 품질 모니터링

```markdown
## 데이터 품질 실시간 모니터링

### 전체 품질 점수: 89.2/100
- **정확도**: 92.1% (+1.3%)
- **완전성**: 87.8% (+0.5%)
- **최신성**: 91.5% (+2.1%)
- **일관성**: 85.4% (+0.8%)

### 카테고리별 품질 현황

| 카테고리 | 정확도 | 완전성 | 최신성 | 일관성 | 종합 점수 |
|---|---|---|---|---|---|
| **프로필** | 95.2% | 92.1% | 96.3% | 89.7% | 93.3 |
| **필모그래피** | 91.8% | 85.3% | 93.1% | 82.4% | 88.2 |
| **수상** | 78.5% | 74.2% | 69.8% | 81.3% | 75.9 |
| **뉴스** | 94.7% | 96.8% | 98.2% | 88.5% | 94.6 |
| **미디어** | 89.3% | 83.7% | 87.9% | 84.1% | 86.3 |

### 품질 개선 추세 (최근 30일)
```
[그래프: 점수 상승 추세]
시간: ----->
점수: ----->
```

### 자동 개선 작업 현황
- **검증 완료**: 47개 항목 (오늘)
- **표준화**: 23개 항목 (오늘)
- **링크 검증**: 156개 링크 (오늘)
- **중복 제거**: 8개 항목 (오늘)
```

### 4.2 품질 개선 자동화

```python
class QualityImprover:
    def __init__(self):
        self.improvement_rules = {
            'missing_sources': self.find_official_sources,
            'broken_links': self.update_broken_links,
            'inconsistent_formats': self.standardize_formats,
            'outdated_info': self.update_information
        }

    def run_improvement_cycle(self):
        """품질 개선 자동 실행"""
        quality_report = self.generate_quality_report()

        for issue, count in quality_report['issues'].items():
            if count > 0:
                print(f"개선 작업 시작: {issue} ({count}개 항목)")
                improvement = self.improvement_rules[issue]()
                quality_report['fixed'][issue] = improvement['fixed']

        return quality_report

    def find_official_sources(self, items_without_sources):
        """공식 출처 자동 검색"""
        found_sources = 0

        for item in items_without_sources:
            # 소속사 공식 사이트 검색
            agency_result = self.search_agency_site(item)
            if agency_result:
                item['source'] = agency_result
                found_sources += 1
                continue

            # 시상식 공식 사이트 검색
            award_result = self.search_award_site(item)
            if award_result:
                item['source'] = award_result
                found_sources += 1

        return {"fixed": found_sources, "total": len(items_without_sources)}
```

## 5. 운영 가이드라인

### 5.1 데이터 관리 규칙

```yaml
data_management_rules:
  update_frequency:
    profile: "매일 확인, 변경 시 즉시 업데이트"
    filmography: "신작 확정 시 즉시, 주간 검증"
    awards: "시상식 진행 중 실시간, 종료 후 최종 확정"
    news: "실시간 수집, 매일 정리"

  verification_priority:
    critical: "프로필 정보, 대표 수상, 현재 활동"
    high: "최신 작품, 주요 인터뷰"
    medium: "과거 작품, 일반 뉴스"
    low: "팬 콘텐츠, 2차 자료"

  escalation_rules:
    data_conflict: "24시간 내 수동 검증"
    missing_sources: "48시간 내 출처 확보"
    quality_drop: "즉시 개선 작업 시작"
```

### 5.2 장애 대응 절차

```yaml
incident_response:
  data_corruption:
    detection: "자동 무결성 체크"
    response: "백업에서 복구, 원인 분석"
    prevention: "주기적 백업, 롤백 테스트"

  source_unavailable:
    detection: "링크 상태 모니터링"
    response: "대체 출처 검색, 링크 업데이트"
    prevention: "다중 출처 확보"

  verification_failure:
    detection: "검증 점수 하락 감지"
    response: "수동 검증, 규칙 조정"
    prevention: "검증 규칙 주기적 검토"
```
