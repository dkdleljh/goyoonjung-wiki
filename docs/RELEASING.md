# RELEASING

이 문서는 고윤정 위키 저장소의 **태그 생성, changelog 갱신, GitHub Release 발행 정책**을 설명합니다.

현재 이 저장소는 사람이 매번 릴리즈 버튼을 누르지 않아도 되도록, 가능한 범위를 자동화해 두었습니다.

또한 GitHub Actions의 [`release.yml`](../.github/workflows/release.yml)이
`main` 브랜치 푸시마다 한 번 더 `scripts/auto_release.sh`를 실행해,
수동 푸시/로컬 환경 편차가 있어도 **태그/릴리즈 노트/CHANGELOG 동기화**를 보증합니다.

## 목표

---

## 1. 현재 릴리즈 방식

이 저장소는 `scripts/auto_release.sh`를 통해 다음을 자동으로 수행합니다.

1. 원격 태그 fetch
2. 마지막 canonical semver tag 탐색
3. 변경 범위 분석
4. bump 계산
5. `CHANGELOG.md` 갱신
6. release notes 파일 생성
7. git tag 생성
8. GitHub Release create/edit(upsert)
9. release notes 파일을 자산으로 업로드

---

## 2. 태그 규칙

정식 릴리즈 태그는 다음 형식을 사용합니다.

```text
vMAJOR.MINOR.PATCH
```

예:
- `v1.3.0`
- `v1.3.1`

과거 태그가 혼재할 수 있으나, 앞으로의 canonical 흐름은 **SemVer 라인**으로 유지합니다.

---

## 3. bump 규칙

### major
- 커밋 메시지에 `BREAKING CHANGE`
- 또는 `!:` 포함

### minor
- 기능/수집기/승격/설정/스키마 성격의 변경
- 파일 휴리스틱상 의미 있는 운영 확장

### patch
- 버그 수정
- 문서 보강
- 운영 안정화
- 파이프라인 보수

---

## 4. release notes 구성

현재 릴리즈 노트 파일은 아래 섹션으로 생성됩니다.

- 제목 / 생성시각 / bump / base tag / head
- Summary
- Impact
- Validation
- Risk
- Rollback
- Changes
- Assets

생성 위치:
```text
logs/releases/release-notes-<tag>.md
```

GitHub Release 본문도 같은 파일을 기반으로 생성 또는 수정됩니다.

또한 이 파일은 **GitHub Release asset으로도 업로드**됩니다.

---

## 5. changelog와의 관계

`auto_release.sh`는 릴리즈 직전에 아래를 수행합니다.

```bash
python3 ./scripts/generate_changelog.py --next-tag "$new_tag"
```

즉, changelog는 릴리즈와 분리된 수동 문서가 아니라,  
**릴리즈 직전 자동으로 동기화되는 문서**입니다.

---

## 6. 실행 조건

릴리즈 자동화는 아래 조건을 기본으로 합니다.

- 현재 브랜치가 `main`
- working tree가 clean
- 마지막 릴리즈 이후 새로운 커밋 존재

이 조건을 만족하지 않으면 안전하게 skip 합니다.

---

## 7. 문제 상황 대응

### 태그 충돌
원격에 이미 같은 태그가 있으면 충돌합니다.  
현재는 실행 전 `git fetch --tags`를 수행해 충돌 가능성을 줄였습니다.

### GitHub Release만 실패
- 태그는 생성됐지만 `gh release`만 실패할 수 있습니다.
- 이 경우 `gh auth status`를 먼저 확인합니다.

### release notes 자산 누락
- 본문 생성은 성공했지만 asset upload만 실패할 수 있습니다.
- 필요하면 아래로 수동 업로드 가능합니다.

```bash
gh release upload <tag> logs/releases/release-notes-<tag>.md --clobber
```

---

## 8. 수동 검증 명령

```bash
cd /Users/zenith/Documents/My-Second-Brain/20_Projects/Goyoonjung-Wiki
git tag --sort=-creatordate | sed -n '1,5p'
gh release list --repo dkdleljh/goyoonjung-wiki --limit 5
ls logs/releases/ | tail -n 5
```

---

## 9. 문서 동기화 원칙

다음 중 하나가 바뀌면 이 문서를 반드시 같이 봐야 합니다.

- `scripts/auto_release.sh`
- `scripts/generate_changelog.py`
- 태그 포맷
- 릴리즈 노트 섹션 구조
- GitHub Release 업로드 정책

---

## 10. 한 줄 요약

이 저장소의 릴리즈는 “버전 번호만 찍는 절차”가 아니라,
**운영 상태와 변경 내용을 사람이 이해할 수 있게 남기는 자동 기록 체계**입니다.

- main 브랜치 + clean working tree 일 때만 태그를 생성합니다.
- 태그 생성/푸시는 실패해도 daily run 전체를 실패로 만들지 않습니다(베스트에포트).
- GitHub Actions는 `contents: write` 권한으로 `main` 기준 릴리즈 동기화를 수행합니다.
- 릴리즈 노트는 `logs/releases/release-notes-vX.Y.Z.md`와 GitHub Release 본문에 함께 반영됩니다.
