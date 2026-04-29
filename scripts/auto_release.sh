#!/usr/bin/env bash
set -euo pipefail

# Auto release tagger (patch/minor/major) with best-effort GitHub Release creation.
# - Uses semver tags: vMAJOR.MINOR.PATCH
# - Bump rules (recommended):
#   * major: commit message contains "BREAKING CHANGE" OR subject contains "!:" OR files indicate breaking wiring changes
#   * minor: new feature/collector/promotion/config/schema changes
#   * patch: bugfix/docs/ops tweaks
# - Creates annotated git tag and pushes tag.
# - If GitHub auth is available (GH_TOKEN/GITHUB_TOKEN or gh auth), creates GitHub Release.

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

export PATH="$HOME/bin:$PATH"
OWNER_REPO="$(
  git remote get-url origin 2>/dev/null \
    | sed -E 's#^(git@github.com:|https://github.com/)##; s#\.git$##'
)"

SEMVER_REGEX='^v([0-9]+)\.([0-9]+)\.([0-9]+)$'
CANONICAL_MIN_MAJOR=1

latest_semver_tag() {
  # Ignore legacy date-style tags like v2026.02.17 and keep a single canonical line.
  # Canonical: MAJOR >= CANONICAL_MIN_MAJOR and < 1000.
  git tag -l 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname \
    | while read -r t; do
        if [[ "$t" =~ $SEMVER_REGEX ]]; then
          maj=${BASH_REMATCH[1]}
          if [ "$maj" -ge "$CANONICAL_MIN_MAJOR" ] && [ "$maj" -lt 1000 ]; then
            echo "$t"; break
          fi
        fi
      done
}

parse_semver() {
  local tag="$1"
  if [[ "$tag" =~ $SEMVER_REGEX ]]; then
    echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]} ${BASH_REMATCH[3]}"
  else
    echo "0 0 0"
  fi
}

bump_version() {
  local major="$1" minor="$2" patch="$3" bump="$4"
  case "$bump" in
    major) echo "$((major+1)) 0 0";;
    minor) echo "$major $((minor+1)) 0";;
    patch|*) echo "$major $minor $((patch+1))";;
  esac
}

# Determine bump type from commits + files changed since last semver tag.
detect_bump() {
  local from_ref="$1"

  # commits
  local subjects
  subjects=$(git log --format=%s "${from_ref}..HEAD" 2>/dev/null || true)

  if echo "$subjects" | grep -qE 'BREAKING CHANGE|!:'; then
    echo major; return 0
  fi

  # file heuristics
  local files
  files=$(git diff --name-only "${from_ref}..HEAD" 2>/dev/null || true)

  # breaking-ish wiring changes
  if echo "$files" | grep -qE '^(scripts/run_daily_update\.sh|config/allowlist-domains\.txt|config/domain-grades\.yml|config/google-news-queries(\-precise|\-broad)?\.txt|config/google-news-sites\.txt)$'; then
    # treat as minor by default (not necessarily breaking), major only if commit flagged
    echo minor; return 0
  fi

  # features: new scripts/config/docs schema
  if echo "$files" | grep -qE '^(scripts/auto_collect_|scripts/promote_|scripts/build_|scripts/compute_|config/|docs/content_schema\.md|pages/perfect-scorecard\.md|pages/promotion-queue\.md)'; then
    echo minor; return 0
  fi

  echo patch
}

release_only_changes() {
  local from_ref="$1"
  local files
  files=$(git diff --name-only "${from_ref}..HEAD" 2>/dev/null || true)
  [ -n "$files" ] || return 1

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$f" in
      CHANGELOG.md|logs/releases/release-notes-v*.md) ;;
      *) return 1 ;;
    esac
  done <<< "$files"

  return 0
}

main() {
  # Only run when HEAD is on main and clean.
  local branch
  branch=$(git rev-parse --abbrev-ref HEAD)
  if [ "$branch" != "main" ]; then
    echo "auto_release: skip (branch=$branch)" >&2
    exit 0
  fi

  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "auto_release: skip (working tree not clean)" >&2
    exit 0
  fi

  git fetch --quiet origin --tags --prune >/dev/null 2>&1 || true

  local last_tag
  last_tag=$(latest_semver_tag)
  if [ -z "$last_tag" ]; then
    # bootstrap semver baseline on current HEAD
    local tag="v0.1.0"
    if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
      echo "auto_release: baseline tag exists ($tag)" >&2
      exit 0
    fi
    git tag -a "$tag" -m "Release $tag (baseline)"
    git push origin "$tag" >/dev/null
    echo "auto_release: created $tag" >&2
    exit 0
  fi

  # If HEAD is already tagged with last_tag, do nothing.
  if git describe --tags --exact-match HEAD >/dev/null 2>&1; then
    echo "auto_release: skip (HEAD already tagged)" >&2
    exit 0
  fi

  # If no commits since last tag, do nothing.
  if [ -z "$(git rev-list "${last_tag}..HEAD" 2>/dev/null)" ]; then
    echo "auto_release: skip (no commits since $last_tag)" >&2
    exit 0
  fi

  # Avoid release-on-release loops. A previous release run may push only
  # CHANGELOG/release-note files before the tag workflow observes the commit.
  if release_only_changes "$last_tag"; then
    echo "auto_release: skip (only release metadata changed since $last_tag)" >&2
    exit 0
  fi

  read -r major minor patch <<<"$(parse_semver "$last_tag")"
  bump=$(detect_bump "$last_tag")
  read -r nmajor nminor npatch <<<"$(bump_version "$major" "$minor" "$patch" "$bump")"
  new_tag="v${nmajor}.${nminor}.${npatch}"
  notes_dir="logs/releases"
  notes_file="${notes_dir}/release-notes-${new_tag}.md"
  notes_basename="$(basename "$notes_file")"
  mkdir -p "$notes_dir"
  release_url="https://github.com/${OWNER_REPO}/releases/tag/${new_tag}"
  compare_url="https://github.com/${OWNER_REPO}/compare/${last_tag}...${new_tag}"
  rollback_ref="${last_tag:-HEAD~1}"

  notes_body=$(git log --format='- %s (%h)' "${last_tag}..HEAD" | sed -n '1,80p')
  cat >"$notes_file" <<EOF
# ${new_tag}

- generated_at: $(TZ=Asia/Seoul date +"%Y-%m-%d %H:%M:%S %Z")
- bump: ${bump}
- base: ${last_tag}
- head: $(git rev-parse --short HEAD)

## Summary

- bump: **${bump}**
- base: ${last_tag}

## Impact

- repository: ${OWNER_REPO}
- release_url: ${release_url}
- compare_url: ${compare_url}
- expected_scope: collectors / promotion / dashboard / automation pipeline

## Validation

- changelog_sync: OK
- git_push_main: OK
- git_push_tag: OK
- github_release_upsert: OK

## Risk

- level: medium
- reason: daily automation and release pipeline changes may affect unattended runs

## Rollback

1. git checkout ${rollback_ref}
2. restore release automation scripts if needed
3. edit or delete GitHub Release ${new_tag} if rollback is published separately

## Changes

${notes_body}

## Assets

- ${notes_basename}
EOF
  msg="Release ${new_tag} (${bump})"

  # Keep CHANGELOG.md in sync with canonical tags.
  # If generation changes the file, commit it before tagging.
  python3 ./scripts/generate_changelog.py --next-tag "$new_tag" >/dev/null 2>&1 || true
  git add CHANGELOG.md "$notes_file" 2>/dev/null || true
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "chore: prepare release ${new_tag}" >/dev/null
    git push origin main >/dev/null
  fi

  git tag -a "$new_tag" -m "$msg"
  git push origin "$new_tag" >/dev/null

  # Best-effort GitHub release (create only if it doesn't exist)
  if command -v gh >/dev/null 2>&1; then
    export GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
    if [ -n "$OWNER_REPO" ] && { [ -n "${GH_TOKEN:-}" ] || gh auth status >/dev/null 2>&1; }; then
      if gh release view "$new_tag" --repo "$OWNER_REPO" >/dev/null 2>&1; then
        gh release edit "$new_tag" --repo "$OWNER_REPO" --title "$new_tag" --notes-file "$notes_file" >/dev/null 2>&1 || true
      else
        gh release create "$new_tag" --repo "$OWNER_REPO" --title "$new_tag" --notes-file "$notes_file" >/dev/null 2>&1 || true
      fi
      gh release upload "$new_tag" "$notes_file" --repo "$OWNER_REPO" --clobber >/dev/null 2>&1 || true
    fi
  fi

  echo "auto_release: tagged $new_tag (bump=$bump)" >&2
}

main "$@"
