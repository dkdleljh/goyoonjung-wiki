# 사용자 경험 최적화 및 자동화 시스템 설계


## 한눈에 보기

- 한 줄 요약: (추가 필요)
- 핵심 링크: (추가 필요 — 공식/원문 우선)
- 상태: (추가 필요 — 근거 수준 S/A/2차/보강 필요)

## 1. 사용자 경험(UX) 최적화 설계

### 1.1 시각적 개선 (인포박스 + 대시보드)

#### 향상된 메인 레이아웃
```html
<!-- 메인 페이지 구조 -->
<div class="wiki-main">
  <!-- 상단 인포박스 -->
  <div class="infobox-hero">
    <div class="profile-section">
      <img src="profile-main.jpg" class="profile-image" alt="고윤정">
      <div class="basic-info">
        <h1>고윤정 (Go Youn-jung)</h1>
        <div class="status-badge">촬영 중</div>
        <p>대한민국의 배우 (1996-04-22 ~)</p>
      </div>
    </div>

    <div class="quick-stats">
      <div class="stat-item">
        <span class="stat-number">15</span>
        <span class="stat-label">작품</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">11</span>
        <span class="stat-label">수상/후보</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">682만</span>
        <span class="stat-label">인스타 팔로워</span>
      </div>
    </div>
  </div>

  <!-- 네비게이션 메뉴 -->
  <nav class="main-nav">
    <div class="nav-section">
      <h3>핵심 정보</h3>
      <a href="#profile" class="nav-link">프로필</a>
      <a href="#filmography" class="nav-link">필모그래피</a>
      <a href="#awards" class="nav-link">수상</a>
    </div>
    <div class="nav-section">
      <h3>콘텐츠</h3>
      <a href="#interviews" class="nav-link">인터뷰</a>
      <a href="#pictorials" class="nav-link">화보</a>
      <a href="#news" class="nav-link">최신 소식</a>
    </div>
  </nav>

  <!-- 최신 활동 피드 -->
  <div class="activity-feed">
    <h2>최신 활동</h2>
    <div class="feed-item">
      <span class="timestamp">2시간 전</span>
      <span class="activity-type">인스타그램</span>
      <p>새로운 화보 스틸 컷 공개</p>
    </div>
  </div>
</div>
```

#### 인터랙티브 인포박스
```javascript
class InteractiveInfobox {
    constructor() {
        this.data = {
            name: '고윤정',
            birthDate: '1996-04-22',
            occupation: '배우',
            agency: 'MAA',
            filmography: 15,
            awards: 11,
            socialMedia: {
                instagram: '682만',
                youtube: '58만'
            }
        };

        this.render();
        this.setupInteractions();
    }

    render() {
        const template = `
            <div class="enhanced-infobox">
                ${this.renderProfileSection()}
                ${this.renderQuickStats()}
                ${this.renderRecentActivity()}
                ${this.renderQuickActions()}
            </div>
        `;

        document.querySelector('.infobox-container').innerHTML = template;
    }

    setupInteractions() {
        // 실시간 업데이트
        this.setupRealTimeUpdates();

        // 검색 기능
        this.setupQuickSearch();

        // 다크모드
        this.setupDarkMode();

        // 공유 기능
        this.setupSharing();
    }

    setupRealTimeUpdates() {
        // WebSocket으로 실시간 데이터 업데이트
        const ws = new WebSocket('ws://localhost:8080/updates');

        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            this.updateDisplay(update);
        };
    }
}
```

### 1.2 모바일 최적화

#### 반응형 디자인
```css
/* 모바일 우선 디자인 */
.wiki-main {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
}

.infobox-hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 1.5rem;
    color: white;
}

.profile-section {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.profile-image {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(255, 255, 255, 0.2);
}

/* 데스크톱 */
@media (min-width: 768px) {
    .wiki-main {
        grid-template-columns: 1fr 3fr;
        gap: 2rem;
        padding: 2rem;
    }

    .infobox-hero {
        position: sticky;
        top: 1rem;
    }

    .profile-image {
        width: 120px;
        height: 120px;
    }
}

/* 태블릿 */
@media (min-width: 1024px) {
    .profile-image {
        width: 150px;
        height: 150px;
    }

    .quick-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
}
```

#### 터치 최적화
```css
/* 터치 영역 확대 */
.nav-link, .stat-item, .feed-item {
    padding: 12px 16px;
    min-height: 44px; /* iOS 최소 터치 영역 */
    cursor: pointer;
    transition: all 0.2s ease;
}

.nav-link:active {
    transform: scale(0.98);
    background-color: rgba(255, 255, 255, 0.1);
}

/* 스와이프 제스처 */
.activity-feed {
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
}

.feed-item {
    scroll-snap-align: start;
    flex: 0 0 85%;
}
```

### 1.3 검색 및 내비게이션 개선

#### 고급 검색 기능
```javascript
class AdvancedSearch {
    constructor() {
        this.searchIndex = this.buildSearchIndex();
        this.setupSearchInterface();
    }

    buildSearchIndex() {
        // 전체 데이터 검색 인덱스 생성
        return {
            profiles: this.indexProfiles(),
            filmography: this.indexFilmography(),
            awards: this.indexAwards(),
            news: this.indexNews(),
            media: this.indexMedia()
        };
    }

    search(query, filters = {}) {
        const results = [];

        // 텍스트 검색
        const textResults = this.searchText(query);

        // 필터 적용
        const filteredResults = this.applyFilters(textResults, filters);

        // 관련도 정렬
        return this.sortByRelevance(filteredResults, query);
    }

    setupSearchInterface() {
        const searchBox = document.querySelector('#search-input');

        searchBox.addEventListener('input', (e) => {
            const query = e.target.value;
            if (query.length >= 2) {
                const suggestions = this.getSuggestions(query);
                this.displaySuggestions(suggestions);
            }
        });

        // 실시간 검색 결과
        searchBox.addEventListener('search', (e) => {
            this.performSearch(e.target.value);
        });
    }

    getSuggestions(query) {
        // 자동 완성 제안
        return [
            `${query} 필모그래피`,
            `${query} 수상`,
            `${query} 인터뷰`,
            `최신 ${query}`
        ].filter(suggestion =>
            this.searchIndex[suggestion.toLowerCase()]
        );
    }
}
```

#### 빠른 내비게이션
```html
<!-- 빠른 접근 메뉴 -->
<div class="quick-nav">
    <button class="quick-nav-btn" data-target="profile">
        <i class="icon-profile"></i>
        <span>프로필</span>
    </button>
    <button class="quick-nav-btn" data-target="filmography">
        <i class="icon-film"></i>
        <span>작품</span>
    </button>
    <button class="quick-nav-btn" data-target="awards">
        <i class="icon-award"></i>
        <span>수상</span>
    </button>
    <button class="quick-nav-btn" data-target="news">
        <i class="icon-news"></i>
        <span>소식</span>
    </button>
</div>
```

## 2. 자동화 시스템 강화

### 2.1 AI 기반 콘텐츠 생성

#### 자동 요약 시스템
```python
class ContentGenerator:
    def __init__(self):
        self.openai_client = OpenAI()
        self.templates = self.load_templates()

    def generate_profile_summary(self, profile_data):
        """프로필 자동 요약 생성"""
        prompt = f"""
        배우 고윤정의 프로필 정보를 바탕으로 매력적인 소개글을 작성해주세요:

        데이터:
        - 이름: {profile_data['name']}
        - 출생: {profile_data['birth_date']}
        - 대표작: {', '.join(profile_data['notable_works'])}
        - 수상: {profile_data['awards_count']}개 수상
        - 특징: {profile_data['characteristics']}

        요구사항:
        1. 매력적이고 전문적인 톤
        2. 핵심 강점 강조
        3. 팬들이 관심 가질 내용 포함
        4. 100-150자 내외
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        return response.choices[0].message.content

    def generate_work_description(self, work_data):
        """작품 설명 자동 생성"""
        # 작품 정보 기반 설명 생성
        # 시놉시스, 캐릭터, 평가 등 조합
        pass

    def generate_timeline_summary(self, period_data):
        """특정 기간 활동 요약 생성"""
        # 기간별 주요 활동 자동 요약
        pass
```

#### 자동 태깅 시스템
```python
class AutoTagger:
    def __init__(self):
        self.tag_patterns = {
            'interview': ['인터뷰', 'talk', 'conversation', '대담'],
            'pictorial': ['화보', 'pictorial', 'photo shoot', '화촬'],
            'award': ['수상', 'award', '시상식', '수상소감'],
            'event': ['행사', 'event', '팬미팅', '제작발표'],
            'drama': ['드라마', 'drama', 'series', '시리즈'],
            'movie': ['영화', 'movie', 'film', '개봉']
        }

    def auto_tag_content(self, title, content, category):
        """콘텐츠 자동 태깅"""
        tags = set()

        # 제목 기반 태깅
        tags.update(self.extract_tags_from_text(title))

        # 내용 기반 태깅
        tags.update(self.extract_tags_from_text(content))

        # 카테고리 기반 태깅
        tags.add(category)

        # 작품명 태깅
        work_tags = self.extract_work_tags(content)
        tags.update(work_tags)

        # 연도 태깅
        year_tags = self.extract_year_tags(content)
        tags.update(year_tags)

        return sorted(list(tags))

    def extract_tags_from_text(self, text):
        tags = []
        for tag, patterns in self.tag_patterns.items():
            for pattern in patterns:
                if pattern in text.lower():
                    tags.append(tag)
                    break
        return tags
```

### 2.2 실시간 데이터 수집

#### SNS 모니터링 시스템
```python
class SocialMediaMonitor:
    def __init__(self):
        self.platforms = {
            'instagram': InstagramClient(),
            'youtube': YouTubeClient(),
            'twitter': TwitterClient()
        }

    def monitor_all_platforms(self):
        """모든 플랫폼 실시간 모니터링"""
        while True:
            for platform_name, client in self.platforms.items():
                try:
                    updates = client.get_recent_updates("go_younjung")
                    self.process_updates(platform_name, updates)
                except Exception as e:
                    self.handle_error(platform_name, e)

            time.sleep(1800)  # 30분마다 확인

    def process_updates(self, platform, updates):
        """업데이트 처리 및 저장"""
        for update in updates:
            # 중복 체크
            if not self.is_duplicate(update):
                # 내용 분석
                analysis = self.analyze_content(update)

                # 저장
                self.save_update(update, analysis)

                # 알림
                self.notify_update(update, analysis)

                # 위키 업데이트
                self.update_wiki_content(update, analysis)

    def analyze_content(self, update):
        """업데이트 내용 분석"""
        analysis = {
            'type': self.classify_content(update),
            'importance': self.calculate_importance(update),
            'tags': self.auto_tagger.auto_tag_content(
                update['title'],
                update['content'],
                update['category']
            ),
            'media_type': self.detect_media_type(update)
        }

        return analysis
```

#### 뉴스 자동 수집 및 분류
```python
class NewsCollector:
    def __init__(self):
        self.news_sources = [
            'https://news.naver.com',
            'https://news.daum.net',
            'https://www.dispatch.co.kr',
            'https://www.sportschosun.com'
        ]

        self.keywords = [
            '고윤정', 'Go Youn-jung',
            'MAA', '환혼', '스위트홈'
        ]

    def collect_news(self):
        """뉴스 자동 수집"""
        all_news = []

        for source in self.news_sources:
            news_from_source = self.scrape_news_source(source)
            all_news.extend(news_from_source)

        # 중복 제거
        unique_news = self.remove_duplicates(all_news)

        # 분류
        classified_news = self.classify_news(unique_news)

        # 저장
        self.save_news(classified_news)

        return classified_news

    def classify_news(self, news_items):
        """뉴스 자동 분류"""
        for item in news_items:
            # 카테고리 분류
            category = self.classify_category(item['title'], item['content'])
            item['category'] = category

            # 중요도 평가
            importance = self.calculate_news_importance(item)
            item['importance'] = importance

            # 태깅
            tags = self.auto_tagger.auto_tag_content(
                item['title'],
                item['content'],
                category
            )
            item['tags'] = tags

        return news_items

    def classify_category(self, title, content):
        """뉴스 카테고리 분류"""
        categories = {
            'interview': ['인터뷰', '단독', 'talk'],
            'pictorial': ['화보', 'pictorial', '화촬'],
            'award': ['수상', '시상식', '수상소감'],
            'event': ['행사', '참석', '제작발표'],
            'drama': ['드라마', '시리즈', '방영'],
            'movie': ['영화', '개봉', '흥행'],
            'promotion': ['광고', '브랜드', '엠버서더']
        }

        for category, keywords in categories.items():
            if any(keyword in title for keyword in keywords):
                return category

        return 'general'
```

### 2.3 자동화된 품질 관리

#### 링크 유효성 검사
```python
class LinkValidator:
    def __init__(self):
        self.session = requests.Session()
        self.broken_links = []
        self.redirected_links = []

    def validate_all_links(self):
        """모든 링크 유효성 검사"""
        all_links = self.extract_all_links()

        for link_data in all_links:
            result = self.validate_link(link_data)
            self.process_validation_result(link_data, result)

        self.generate_validation_report()

    def validate_link(self, link_data):
        """개별 링크 검증"""
        try:
            response = self.session.head(
                link_data['url'],
                timeout=10,
                allow_redirects=True
            )

            return {
                'status_code': response.status_code,
                'final_url': response.url,
                'is_valid': 200 <= response.status_code < 400,
                'content_type': response.headers.get('content-type', ''),
                'response_time': response.elapsed.total_seconds()
            }

        except requests.RequestException as e:
            return {
                'status_code': None,
                'final_url': None,
                'is_valid': False,
                'error': str(e)
            }

    def process_validation_result(self, link_data, result):
        """검증 결과 처리"""
        if not result['is_valid']:
            self.broken_links.append({
                'url': link_data['url'],
                'page': link_data['page'],
                'context': link_data['context'],
                'error': result.get('error', f"HTTP {result['status_code']}")
            })

            # 대체 링크 검색
            alternative = self.find_alternative(link_data)
            if alternative:
                self.suggest_replacement(link_data, alternative)

        elif result['final_url'] != link_data['url']:
            self.redirected_links.append({
                'original': link_data['url'],
                'redirected': result['final_url'],
                'page': link_data['page']
            })
```

#### 자동 개선 추천
```python
class ImprovementRecommender:
    def __init__(self):
        self.improvement_rules = self.load_improvement_rules()

    def analyze_improvements(self):
        """개선 필요 항목 분석"""
        improvements = []

        # 콘텐츠 완성도 분석
        content_gaps = self.analyze_content_gaps()
        improvements.extend(content_gaps)

        # 검증 상태 분석
        verification_gaps = self.analyze_verification_gaps()
        improvements.extend(verification_gaps)

        # 사용자 경험 분석
        ux_issues = self.analyze_ux_issues()
        improvements.extend(ux_issues)

        return self.prioritize_improvements(improvements)

    def analyze_content_gaps(self):
        """콘텐츠 부족 항목 분석"""
        gaps = []

        # 필수 필드 체크
        required_fields = ['name', 'birth_date', 'agency', 'filmography']
        for field in required_fields:
            if not self.has_complete_field(field):
                gaps.append({
                    'type': 'missing_field',
                    'field': field,
                    'priority': 'high',
                    'suggestion': f'{field} 정보 추가 필요'
                })

        # 최신 정보 체크
        if self.needs_update():
            gaps.append({
                'type': 'outdated_info',
                'priority': 'medium',
                'suggestion': '최신 정보 업데이트 필요'
            })

        return gaps

    def auto_improve(self, improvement):
        """자동 개선 실행"""
        if improvement['type'] == 'missing_field':
            return self.fill_missing_field(improvement)
        elif improvement['type'] == 'broken_link':
            return self.fix_broken_link(improvement)
        elif improvement['type'] == 'inconsistency':
            return self.standardize_format(improvement)

        return None
```

## 3. 운영 대시보드

### 3.1 관리자용 대시보드

```html
<!-- 관리자 대시보드 -->
<div class="admin-dashboard">
    <div class="dashboard-header">
        <h1>goyoonjung-wiki 관리 대시보드</h1>
        <div class="system-status">
            <span class="status-indicator online">시스템 정상</span>
            <span class="last-update">최신 업데이트: 5분 전</span>
        </div>
    </div>

    <!-- 핵심 지표 -->
    <div class="metrics-grid">
        <div class="metric-card">
            <h3>전체 콘텐츠</h3>
            <div class="metric-value">1,247</div>
            <div class="metric-change positive">+12 (오늘)</div>
        </div>
        <div class="metric-card">
            <h3>데이터 품질</h3>
            <div class="metric-value">89.2%</div>
            <div class="metric-change positive">+1.3%</div>
        </div>
        <div class="metric-card">
            <h3>방문자 수</h3>
            <div class="metric-value">2,341</div>
            <div class="metric-change positive">+18.7%</div>
        </div>
    </div>

    <!-- 활동 로그 -->
    <div class="activity-log">
        <h2>최근 활동</h2>
        <div class="log-entry">
            <span class="timestamp">14:23</span>
            <span class="type">자동 업데이트</span>
            <span class="description">인스타그램 새 포스트 3개 수집</span>
        </div>
        <div class="log-entry">
            <span class="timestamp">14:15</span>
            <span class="type">품질 개선</span>
            <span class="description">수상 정보 2개 항목 공식 링크 확보</span>
        </div>
        <div class="log-entry">
            <span class="timestamp">14:00</span>
            <span class="type">뉴스 수집</span>
            <span class="description">관련 뉴스 5개 자동 분류</span>
        </div>
    </div>

    <!-- 개선 작업 -->
    <div class="improvements">
        <h2>자동 개선 작업</h2>
        <div class="improvement-item">
            <span class="priority high">높음</span>
            <span class="description">수상 정보 공식 링크 확보 (5개 항목)</span>
            <button class="action-btn">실행</button>
        </div>
        <div class="improvement-item">
            <span class="priority medium">중간</span>
            <span class="description">과거 뉴스 태그 재분류 (23개 항목)</span>
            <button class="action-btn">실행</button>
        </div>
    </div>
</div>
```

### 3.2 실시간 모니터링

```javascript
class DashboardMonitor {
    constructor() {
        this.websocket = new WebSocket('ws://localhost:8080/dashboard');
        this.setupWebSocket();
        this.startPeriodicUpdates();
    }

    setupWebSocket() {
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateDashboard(data);
        };

        this.websocket.onclose = () => {
            console.log('WebSocket 연결 종료, 5초 후 재연결...');
            setTimeout(() => this.reconnect(), 5000);
        };
    }

    updateDashboard(data) {
        switch(data.type) {
            case 'content_update':
                this.updateContentMetrics(data.metrics);
                break;
            case 'quality_score':
                this.updateQualityScore(data.score);
                break;
            case 'system_alert':
                this.showAlert(data.alert);
                break;
            case 'activity_log':
                this.addActivityLog(data.log);
                break;
        }
    }

    updateContentMetrics(metrics) {
        // 콘텐츠 지표 실시간 업데이트
        document.querySelector('.content-count').textContent = metrics.total_content;
        document.querySelector('.today-updates').textContent = metrics.today_updates;

        // 애니메이션 효과
        this.animateUpdate('.content-count');
    }

    showAlert(alert) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alert.severity}`;
        alertDiv.textContent = alert.message;

        document.querySelector('.alerts-container').appendChild(alertDiv);

        // 5초 후 자동 제거
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}
```

## 4. 사용자 피드백 및 참여 시스템

### 4.1 피드백 수집

```javascript
class FeedbackSystem {
    constructor() {
        this.feedbackTypes = [
            'error_report',
            'suggestion',
            'content_request',
            'general_feedback'
        ];

        this.setupFeedbackUI();
    }

    setupFeedbackUI() {
        // 피드백 버튼
        const feedbackBtn = document.createElement('button');
        feedbackBtn.className = 'feedback-btn';
        feedbackBtn.innerHTML = '피드백';
        feedbackBtn.onclick = () => this.showFeedbackModal();

        document.body.appendChild(feedbackBtn);
    }

    showFeedbackModal() {
        const modal = this.createFeedbackModal();
        document.body.appendChild(modal);

        // 모달 표시
        setTimeout(() => modal.classList.add('show'), 10);
    }

    submitFeedback(feedbackData) {
        // 서버로 피드백 전송
        fetch('/api/feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(feedbackData)
        })
        .then(response => response.json())
        .then(data => {
            this.showConfirmation(data);
            this.trackFeedback(feedbackData);
        });
    }

    trackFeedback(feedbackData) {
        // 피드백 분석 및 추적
        this.analytics.track('feedback_submitted', {
            type: feedbackData.type,
            page: feedbackData.page,
            urgency: feedbackData.urgency
        });
    }
}
```

### 4.2 커뮤니티 기능

```javascript
class CommunityFeatures {
    constructor() {
        this.setupCommentSystem();
        this.setupContributionTools();
    }

    setupCommentSystem() {
        // 각 콘텐츠에 댓글 시스템 추가
        const contentSections = document.querySelectorAll('.content-section');

        contentSections.forEach(section => {
            const commentSection = this.createCommentSection(section);
            section.appendChild(commentSection);
        });
    }

    setupContributionTools() {
        // 사용자 기여 도구
        const tools = {
            'suggest-edit': this.suggestEdit.bind(this),
            'report-issue': this.reportIssue.bind(this),
            'add-info': this.addInformation.bind(this)
        };

        Object.entries(tools).forEach(([toolName, toolFunc]) => {
            this.addToolButton(toolName, toolFunc);
        });
    }

    suggestEdit(contentId) {
        // 편집 제안 기능
        const editor = new ContentEditor(contentId);
        editor.open();

        editor.onSave = (editData) => {
            this.submitEditSuggestion(contentId, editData);
        };
    }
}
```
