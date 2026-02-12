# Wikipedia 인포박스 구조 벤치마킹 분석

## 1. Wikipedia 인포박스 표준 구조

### 핵심 필드 (Infobox person 기준)
```
- Name (이름)
- Photo (사진)
- Caption (사진 설명)
- Birth Name (본명)
- Birth Date (출생일)
- Birth Place (출생지)
- Death Date (사망일) [해당시]
- Death Place (사망지) [해당시]
- Cause of Death (사망 원인) [해당시]
- Nationality (국적)
- Citizenship (시민권)
- Education (학력)
- Alma Mater (출신 대학)
- Occupation (직업)
- Years Active (활동 기간)
- Employer (고용주)
- Known For (대표작)
- Height (신장)
- Weight (체중) [해당시]
- Spouse (배우자)
- Children (자녀)
- Parents (부모)
- Relatives (친척)
- Family (가족)
- Awards (수상)
- Website (공식 웹사이트)
- Module (확장 모듈)
```

### Wikipedia 검증 원칙
1. **검증 가능성 (Verifiability)**: 모든 정보는 신뢰할 수 있는 출처에서 제공되어야 함
2. **中立性 (Neutrality)**: 모든 정보를 중립적 관점에서 제시
3. **No Original Research**: 출처 없는 독자 연구 금지
4. **Biographies of Living Persons (BLP)**: 생존 인물에 대한 엄격한 기준
   - 출처 없는 정보 즉시 삭제
   - 논란적 정보는 신중하게 처리
   - 명예훼손 가능성 최소화

### 데이터 일관성 기준
1. **출처 우선순위**:
   - 1순위: 공식 출처 (공식 웹사이트, 소속사 프로필)
   - 2순위: 주요 언론사 보도 (중앙일보, 조선일보 등)
   - 3순위: 전문 데이터베이스 (한국영화데이터베이스, 시네21 등)
   - 4순위: 기타 출처 (2차 자료)

2. **표기 통일**:
   - 날짜: YYYY-MM-DD 형식
   - 이름: 한국어 우선, 영어 병기
   - 작품명: 원제 우선, 부제 병기
   - 수상명: 공식 명칭 사용

## 2. Fandom 위키 팬덤 콘텐츠 조직

### 특징
1. **팬 중심 정보 구성**: 팬들이 관심 있는 정보 우선
2. **시각적 요소 강조**: 이미지, 동영상, 팬아트
3. **빠른 업데이트**: 최신 소식, 루머(단, 출처 표시)
4. **커뮤니티 참여**: 편집, 토론, 팬 활동 기록

### 콘텐츠 구조
```
- 프로필 (Profile)
- 필모그래피 (Filmography)
- 갤러리 (Gallery)
- 트리비아 (Trivia)
- 팬 이론 (Fan Theories)
- 관계 망 (Relationships)
- 인용구/명대사 (Quotes)
- SNS/미디어 (Social Media)
```

## 3. IMDb 데이터베이스 필드 구조

### 핵심 데이터 필드
```json
{
  "nameId": "고유 식별자",
  "name": "기본 이름",
  "birthDate": "출생일",
  "deathDate": "사망일",
  "birthPlace": "출생지",
  "deathPlace": "사망지",
  "nationality": "국적",
  "awards": [
    {
      "year": "수상년도",
      "awardName": "시상식명",
      "category": "부문",
      "titles": ["관련작품"],
      "winner": "수상여부",
      "event": "주최"
    }
  ],
  "filmography": [
    {
      "titleId": "작품ID",
      "category": "역할구분",
      "roles": ["역할"],
      "billing": "크레딧 순서",
      "attributes": ["특이사항"]
    }
  ],
  "knownFor": [
    {
      "titleId": "대표작ID",
      "category": "역할구분"
    }
  ],
  "trademarks": ["특징/트레이드마크"]
}
```

### IMDb 검증 시스템
1. **자동화된 데이터 수집**: 공식 출처, 제작사, 배급사
2. **교차 검증**: 다중 출처 비교
3. **신뢰도 등급**: 출처에 따른 신뢰도 분류
4. **실시간 업데이트**: 새로운 정보 즉시 반영

## 4. 공식 웹사이트 정보 구성

### 최고의 배우 공식 사이트 특징
1. **전문적 브랜딩**: 일관된 디자인, 톤앤매너
2. **핵심 정보 최우선**: 프로필, 연락처, 대표작
3. **포트폴리오 중심**: 화보, 영상, 작품 스틸
4. **최신 정보 유지**: 스케줄, 소식, SNS 연동
5. **모바일 최적화**: 반응형 디자인

### 필수 정보 항목
```
- 헤드샷/프로필 사진
- 간단한 자기소개
- 대표작 필모그래피
- 수상 내역
- 연락처/에이전트 정보
- SNS 링크
- 최근 소식/업데이트
- 언론/인터뷰 링크
```
