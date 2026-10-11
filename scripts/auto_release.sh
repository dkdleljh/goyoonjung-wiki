#!/usr/bin/env bash
set -euo pipefail

# Release only the exact commit validated by CI; never commit or merge in this job.
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

main() {
  : "${RELEASE_SHA:?RELEASE_SHA must identify the tested commit}"
  : "${CI_RUN_ID:?CI_RUN_ID must identify a successful ci run}"
  if [ "$(git rev-parse HEAD)" != "$RELEASE_SHA" ]; then
    echo "release: checkout differs from tested SHA" >&2; exit 1
  fi
  if [ -n "$(git status --porcelain)" ]; then
    echo "release: working tree is not clean" >&2; exit 1
  fi
  git fetch --quiet origin main --tags
  if [ "$(git rev-parse origin/main)" != "$RELEASE_SHA" ]; then
    echo "release: newer main exists; waiting for its CI"; exit 0
  fi
  local evidence
  evidence=$(gh run view "$CI_RUN_ID" --repo "$OWNER_REPO" --json headSha,headBranch,conclusion,workflowName,event)
  python3 - "$RELEASE_SHA" "$evidence" <<'PYVERIFY'
import json
import sys
run = json.loads(sys.argv[2])
valid = (run.get("headSha") == sys.argv[1] and run.get("headBranch") == "main"
         and run.get("conclusion") == "success" and run.get("workflowName") == "ci"
         and run.get("event") in {"push", "workflow_dispatch"})
if not valid:
    raise SystemExit("release: CI evidence does not match the tested main commit")
PYVERIFY
  local tag last_tag bump major minor patch nmajor nminor npatch
  tag=$(git tag --points-at "$RELEASE_SHA" --list 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | head -n 1)
  last_tag=$(latest_semver_tag)
  if [ -z "$tag" ]; then
    if [ -z "$last_tag" ]; then
      tag="v1.0.0"
    else
      read -r major minor patch <<<"$(parse_semver "$last_tag")"
      bump=$(detect_bump "$last_tag")
      read -r nmajor nminor npatch <<<"$(bump_version "$major" "$minor" "$patch" "$bump")"
      tag="v${nmajor}.${nminor}.${npatch}"
    fi
    git tag -a "$tag" "$RELEASE_SHA" -m "Release $tag (CI $CI_RUN_ID)"
  fi
  # Also retry a tag push that failed in an earlier invocation. Never force tags.
  git push origin "refs/tags/$tag"
  RELEASE_NOTES_FILE=$(mktemp)
  trap 'rm -f "$RELEASE_NOTES_FILE"' EXIT
  {
    echo "# $tag"
    echo
    echo "Tested commit: $RELEASE_SHA"
    echo "CI run: $CI_RUN_ID"
    echo
    if [ -n "$last_tag" ] && [ "$last_tag" != "$tag" ]; then
      git log --format='- %s (%h)' "$last_tag..$RELEASE_SHA"
    else
      git log -1 --format='- %s (%h)' "$RELEASE_SHA"
    fi
  } > "$RELEASE_NOTES_FILE"
  if ! gh release view "$tag" --repo "$OWNER_REPO" >/dev/null 2>&1; then
    gh release create "$tag" --repo "$OWNER_REPO" --verify-tag --title "$tag" --notes-file "$RELEASE_NOTES_FILE"
  fi
  rm -f "$RELEASE_NOTES_FILE"
  trap - EXIT
  echo "release: $tag -> $RELEASE_SHA"
}

main "$@"
