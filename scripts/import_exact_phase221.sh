#!/usr/bin/env bash
set -euo pipefail
REPO_URL="${1:?usage: $0 <git-repo-url> [bundle-path]}"
BUNDLE="${2:-crypto_trading_platform_v5_1_phase220_git.bundle}"
EXPECTED_BUNDLE_SHA="1d8381546a8dfad3bff165b82cea135c8f28092d70fde9f609e5a7e41219cd20"
EXPECTED_HEAD="8f369aaf135ae86d31872353b7c68f2555c18089"
SOURCE_REF="refs/heads/continuation-phase218"

actual_bundle_sha="$(sha256sum "$BUNDLE" | awk '{print $1}')"
[[ "$actual_bundle_sha" == "$EXPECTED_BUNDLE_SHA" ]] || { echo "bundle SHA mismatch: $actual_bundle_sha" >&2; exit 2; }
git bundle verify "$BUNDLE"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
git -C "$work" init -q
git -C "$work" fetch -q "$BUNDLE" "$SOURCE_REF:$SOURCE_REF" 'refs/tags/*:refs/tags/*'
head_sha="$(git -C "$work" rev-parse "$SOURCE_REF")"
[[ "$head_sha" == "$EXPECTED_HEAD" ]] || { echo "HEAD mismatch: $head_sha" >&2; exit 3; }
[[ "$(git -C "$work" rev-list --count "$SOURCE_REF")" == "25" ]] || { echo "commit count mismatch" >&2; exit 4; }
[[ "$(git -C "$work" for-each-ref refs/tags --format='%(objecttype)' | grep -c '^tag$')" == "19" ]] || { echo "annotated tag count mismatch" >&2; exit 5; }

git -C "$work" remote add target "$REPO_URL"
git -C "$work" push --force target "$SOURCE_REF:refs/heads/main"
git -C "$work" push --force target 'refs/tags/*:refs/tags/*'
remote_head="$(git ls-remote "$REPO_URL" refs/heads/main | awk '{print $1}')"
[[ "$remote_head" == "$EXPECTED_HEAD" ]] || { echo "remote main mismatch: $remote_head" >&2; exit 6; }
echo "EXACT_HISTORY_IMPORT=PASS"
echo "REMOTE_MAIN=$remote_head"
