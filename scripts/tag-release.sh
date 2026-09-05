#!/usr/bin/env bash
set -euo pipefail

version="${1:?Usage: tag-release.sh vMAJOR.MINOR.PATCH[-PRERELEASE]}"
[[ "${version}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]

test -z "$(git status --porcelain)"
head_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse origin/main)"
test "${head_sha}" = "${remote_sha}"
git rev-parse --verify --quiet "refs/tags/${version}" >/dev/null && {
  printf 'Tag already exists: %s\n' "${version}" >&2
  exit 2
}

git tag -a "${version}" -m "CyberSentinel AI ${version}"
printf 'TAG_CREATED %s %s\n' "${version}" "${head_sha}"
printf 'Review locally, then push with: git push origin %s\n' "${version}"
