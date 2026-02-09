# 항목 메타데이터 템플릿 (권장)

아래 YAML 프론트매터(또는 YAML 블록)는 항목을 데이터화하기 위한 권장 형식입니다.

> 원칙: B(2차)로 항목을 발견하더라도, 최종 기록은 S/A(1차/준1차) 링크로 확정합니다.

```yaml
---
id: ""                 # 필수: 내부 고유 ID(보통 normalize_url 기반 해시)
date: "YYYY-MM-DD"       # 필수
kind: ""               # interview|appearance|pictorial|endorsement|work|award|schedule
status: ""             # 공식확정|공식예고|보도(1차)|보도(2차)
source_tier: ""        # S|A|B
source_url: ""         # 필수(확정 항목은 S/A 권장)
source_name: ""        # 예: Marie Claire Korea, Netflix Korea

# 선택(상황에 따라)
title: ""
work: ""               # 작품명
character: ""          # 배역
brand: ""              # 브랜드/회사
platform: ""           # Netflix|Disney+|tvN 등
people: []              # 함께 언급되는 인물
keywords: []
notes: ""              # 1~3줄 요약
---
```
