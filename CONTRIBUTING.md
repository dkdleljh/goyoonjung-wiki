# CONTRIBUTING.md

## 고윤정 위키에 기여하기

이 프로젝트는 고윤정 배우의 작품/화보/광고/인터뷰/출연 기록을 수집·정리하는 자동화 위키 시스템입니다.

---

## 개발 환경 설정

```bash
# 저장소 클론

git clone <repo-url>
cd goyoonjung-wiki

# 가상환경 생성

python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치

pip install -r requirements.txt -r requirements-dev.txt
```

---

## 코드 스타일

- **Python**: 3.12+, Ruff 린트 사용
- **마크다운**: 링크 중심 (저작권 안전)
- **테스트**: pytest 사용

### 린트 실행

```bash
make lint    # Ruff check
make bandit  # 보안 스캔
make test    # pytest
make check   # 전체 검사
```

---

## 스크립트 추가 방법

1. `scripts/` 디렉토리에 스크립트 추가
2. `BASE` 경로 상수 정의
3. `main()` 함수 구현
4. 테스트 파일 추가 (`tests/test_<module>.py`)

### 스크립트 템플릿

```python
#!/usr/bin/env python3
"""Script description."""

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    # Your logic here
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 테스트 작성

```bash
# 테스트 실행

pytest tests/

# 특정 테스트 파일

pytest tests/test_cache.py -v
```

### 테스트 패턴

```python
def test_example(tmp_path):
    import scripts.example as example
    result = example.function()
    assert result == expected
```

---

## 커밋 규칙

- **한글** 또는 **영어**로 명확하게 설명
- 의미 있는 변경만 커밋
- 자동화: 가능하면 하루 1커밋

---

## 문제 해결

### 테스트 실패 시

1. 에러 메시지 확인
2. 테스트 환경 확인
3. 모듈 임포트 확인

### 빌드 실패 시

```bash
make venv    # 가상환경 재생성
make check   # 전체 검사
```

---

## 질문이 있다면

- GitHub Issues 사용
- Discord 웹훅으로 알림 설정 가능
