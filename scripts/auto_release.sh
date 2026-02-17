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

SEMVER_REGEX='^v([0-9]+)\.([0-9]+)\.([0-9]+)$'

latest_semver_tag() {
  git tag -l 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | head -n 1 || true
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
  if echo "$files" | grep -qE '^(scripts/run_daily_update\.sh|config/allowlist-domains\.txt|config/google-news-queries\.txt|config/google-news-sites\.txt)$'; then
    # treat as minor by default (not necessarily breaking), major only if commit flagged
    echo minor; return 0
  fi

  # features: new scripts/config/docs schema
  if echo "$files" | grep -qE '^(scripts/auto_collect_|scripts/promote_|scripts/build_|scripts/compute_|config/|docs/content_schema\.md|pages/perfect-scorecard\.md|pages/promotion-queue\.md)'; then
    echo minor; return 0
  fi

  echo patch
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

  read -r major minor patch <<<"$(parse_semver "$last_tag")"
  bump=$(detect_bump "$last_tag")
  read -r nmajor nminor npatch <<<"$(bump_version "$major" "$minor" "$patch" "$bump")"
  new_tag="v${nmajor}.${nminor}.${npatch}"

  notes=$(git log --format='- %s (%h)' "${last_tag}..HEAD" | head -n 80)
  msg="Release ${new_tag} (${bump})"

  git tag -a "$new_tag" -m "$msg"
  git push origin "$new_tag" >/dev/null

  # Best-effort GitHub release
  if command -v gh >/dev/null 2>&1; then
    export GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
    if [ -n "${GH_TOKEN:-}" ] || gh auth status >/dev/null 2>&1; then
      gh release create "$new_tag" --title "$new_tag" --notes "$notes" >/dev/null 2>&1 || true
    fi
  fi

  echo "auto_release: tagged $new_tag (bump=$bump)" >&2
}

main "$@"
