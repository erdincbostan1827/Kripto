#!/usr/bin/env bash
set -euo pipefail

BUNDLE="${1:-crypto_trading_platform_v5_1_phase218_git.bundle}"
REMOTE="${2:-https://github.com/erdincbostan1827/Kripto.git}"
EXPECTED_BUNDLE_SHA="ee81b54d496a124cc75c2d49b150ffab63cfdab9704fce11e72b46d16e4f6861"
EXPECTED_HEAD="82c7a7b7f621f488422fb549af3ea32356a0c63d"
EXPECTED_TAG="v0.3.0-phase218-local"

actual_sha="$(sha256sum "$BUNDLE" | awk '{print $1}')"
[[ "$actual_sha" == "$EXPECTED_BUNDLE_SHA" ]] || {
  echo "Bundle checksum mismatch" >&2
  exit 2
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git clone "$BUNDLE" "$work/repo"
cd "$work/repo"

[[ "$(git rev-parse continuation-phase218)" == "$EXPECTED_HEAD" ]]
[[ "$(git rev-parse "$EXPECTED_TAG^{}")" == "$EXPECTED_HEAD" ]]
[[ "$(git rev-list --all --count)" == "24" ]]
[[ "$(git tag | wc -l | tr -d ' ')" == "18" ]]
[[ "$(git ls-tree -r --name-only "$EXPECTED_HEAD" | wc -l | tr -d ' ')" == "739" ]]

git remote remove origin
git remote add origin "$REMOTE"

echo "Exact Phase 218 Git object graph verified. Pushing exact branch and annotated tags..."
git push --force-with-lease origin continuation-phase218:main
git push origin --tags

echo "Import completed. Expected main HEAD: $EXPECTED_HEAD"
