#!/usr/bin/env bash
# Safely create or reuse the develop -> main pull request, then merge it with a
# standard merge commit after explicit confirmation and successful checks.

set -Eeuo pipefail
IFS=$'\n\t'

readonly EXPECTED_REPOSITORY="dvconsultores/GlobalAvicola"
readonly BASE_BRANCH="main"
readonly HEAD_BRANCH="develop"
readonly REMOTE="origin"
readonly MAX_MERGEABILITY_ATTEMPTS=12
readonly MERGEABILITY_DELAY_SECONDS=5

log() {
    printf '%s\n' "$*"
}

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

confirm_exact() {
    local prompt="$1"
    local expected="$2"
    local response

    if [[ ! -t 0 ]]; then
        fail "Interactive confirmation is required; standard input is not a terminal."
    fi

    printf '%s\n' "$prompt"
    printf 'Type %q to continue: ' "$expected"
    IFS= read -r response
    [[ "$response" == "$expected" ]] || fail "Confirmation did not match; no action was taken."
}

normalize_repository() {
    local value="$1"
    value="${value%.git}"
    value="${value%/}"

    case "$value" in
        git@github.com:*) value="${value#git@github.com:}" ;;
        ssh://git@github.com/*) value="${value#ssh://git@github.com/}" ;;
        https://github.com/*) value="${value#https://github.com/}" ;;
        http://github.com/*) value="${value#http://github.com/}" ;;
    esac

    printf '%s\n' "$value"
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "Run this script inside a Git repository."
cd "$repo_root"

require_command git
require_command gh

gh auth status --hostname github.com >/dev/null 2>&1 \
    || fail "GitHub CLI is not authenticated for github.com. Run: gh auth login"

remote_url="$(git remote get-url "$REMOTE" 2>/dev/null)" \
    || fail "Git remote '$REMOTE' does not exist."
remote_repository="$(normalize_repository "$remote_url")"
[[ "$remote_repository" == "$EXPECTED_REPOSITORY" ]] \
    || fail "Remote '$REMOTE' points to '$remote_repository', expected '$EXPECTED_REPOSITORY'."

gh_repository="$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)" \
    || fail "Unable to inspect the current GitHub repository with gh."
[[ "$gh_repository" == "$EXPECTED_REPOSITORY" ]] \
    || fail "gh resolved '$gh_repository', expected '$EXPECTED_REPOSITORY'."

# Local modifications are intentionally ignored: this operation compares and
# merges remote branches only, and never commits or pushes local files.
log "Fetching $BASE_BRANCH and $HEAD_BRANCH from $REMOTE..."
git fetch --prune "$REMOTE" \
    "+refs/heads/$BASE_BRANCH:refs/remotes/$REMOTE/$BASE_BRANCH" \
    "+refs/heads/$HEAD_BRANCH:refs/remotes/$REMOTE/$HEAD_BRANCH"

git show-ref --verify --quiet "refs/remotes/$REMOTE/$BASE_BRANCH" \
    || fail "Remote branch '$REMOTE/$BASE_BRANCH' was not found."
git show-ref --verify --quiet "refs/remotes/$REMOTE/$HEAD_BRANCH" \
    || fail "Remote branch '$REMOTE/$HEAD_BRANCH' was not found."

base_sha="$(git rev-parse "refs/remotes/$REMOTE/$BASE_BRANCH")"
head_sha="$(git rev-parse "refs/remotes/$REMOTE/$HEAD_BRANCH")"

[[ "$base_sha" != "$head_sha" ]] \
    || fail "Branches '$BASE_BRANCH' and '$HEAD_BRANCH' point to the same commit; there is nothing to merge."

git merge-base --is-ancestor "$base_sha" "$head_sha" \
    || fail "'$REMOTE/$HEAD_BRANCH' does not contain '$REMOTE/$BASE_BRANCH'. Resolve the branch divergence before opening a PR."

commit_count="$(git rev-list --count "$REMOTE/$BASE_BRANCH..$REMOTE/$HEAD_BRANCH")"
[[ "$commit_count" -gt 0 ]] || fail "No commits from '$HEAD_BRANCH' are pending on '$BASE_BRANCH'."

log ""
log "Repository: $EXPECTED_REPOSITORY"
log "Base:       $BASE_BRANCH ($base_sha)"
log "Head:       $HEAD_BRANCH ($head_sha)"
log "Commits:    $commit_count"
log ""
log "Commits to merge:"
git log --no-decorate --oneline "$REMOTE/$BASE_BRANCH..$REMOTE/$HEAD_BRANCH"
log ""
log "Diff summary:"
git diff --stat "$REMOTE/$BASE_BRANCH...$REMOTE/$HEAD_BRANCH"
log ""

pr_count="$(gh pr list \
    --repo "$EXPECTED_REPOSITORY" \
    --base "$BASE_BRANCH" \
    --head "$HEAD_BRANCH" \
    --state open \
    --limit 2 \
    --json number \
    --jq 'length')" || fail "Unable to query existing pull requests."

if (( pr_count > 1 )); then
    fail "More than one open '$HEAD_BRANCH' -> '$BASE_BRANCH' PR exists; resolve the ambiguity manually."
elif (( pr_count == 1 )); then
    # Structured gh JSON output avoids parsing the PR URL.
    pr_number="$(gh pr list \
        --repo "$EXPECTED_REPOSITORY" \
        --base "$BASE_BRANCH" \
        --head "$HEAD_BRANCH" \
        --state open \
        --limit 1 \
        --json number \
        --jq '.[0].number')" || fail "Unable to obtain the existing PR number."
    pr_url="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json url --jq '.url')" \
        || fail "Unable to obtain the existing PR URL."
    log "Reusing existing PR #$pr_number: $pr_url"
else
    confirm_exact \
        "This will create a pull request from '$HEAD_BRANCH' into '$BASE_BRANCH'." \
        "CREATE $HEAD_BRANCH->$BASE_BRANCH"

    # gh pr create prints a URL, but the PR number is deliberately obtained from
    # structured JSON after creation rather than extracted with a URL regex.
    gh pr create \
        --repo "$EXPECTED_REPOSITORY" \
        --base "$BASE_BRANCH" \
        --head "$HEAD_BRANCH" \
        --title "Merge develop into main" \
        --body "Promote the certified changes from \`develop\` to \`main\` using a standard merge commit." \
        >/dev/null || fail "Pull request creation failed."
    pr_number="$(gh pr list \
        --repo "$EXPECTED_REPOSITORY" \
        --base "$BASE_BRANCH" \
        --head "$HEAD_BRANCH" \
        --state open \
        --limit 1 \
        --json number \
        --jq '.[0].number')" || fail "PR was created, but its number could not be read from GitHub JSON."
    pr_url="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json url --jq '.url')" \
        || fail "PR was created, but its URL could not be read from GitHub JSON."
    log "Created PR #$pr_number: $pr_url"
fi

[[ "$pr_number" =~ ^[0-9]+$ ]] || fail "Could not obtain a valid PR number from GitHub JSON."

log "Waiting for GitHub to determine mergeability..."
merge_state="UNKNOWN"
mergeable="UNKNOWN"
for (( attempt=1; attempt<=MAX_MERGEABILITY_ATTEMPTS; attempt++ )); do
    merge_state="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json mergeStateStatus --jq '.mergeStateStatus')" \
        || fail "Unable to read PR merge state."
    mergeable="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json mergeable --jq '.mergeable')" \
        || fail "Unable to read PR mergeability."

    if [[ "$mergeable" != "UNKNOWN" && "$merge_state" != "UNKNOWN" ]]; then
        break
    fi

    if (( attempt < MAX_MERGEABILITY_ATTEMPTS )); then
        sleep "$MERGEABILITY_DELAY_SECONDS"
    fi
done

case "$mergeable" in
    MERGEABLE) ;;
    CONFLICTING) fail "PR #$pr_number has merge conflicts." ;;
    *) fail "GitHub did not determine that PR #$pr_number is mergeable (state: $mergeable)." ;;
esac

case "$merge_state" in
    CLEAN|HAS_HOOKS|UNSTABLE|BLOCKED) ;;
    BEHIND) fail "PR #$pr_number is behind '$BASE_BRANCH'; update '$HEAD_BRANCH' first." ;;
    DIRTY) fail "PR #$pr_number has merge conflicts." ;;
    DRAFT) fail "PR #$pr_number is a draft." ;;
    *) fail "PR #$pr_number has unsupported merge state '$merge_state'; refusing to merge." ;;
esac

log "Waiting for CI checks on PR #$pr_number..."
if ! gh pr checks "$pr_number" --repo "$EXPECTED_REPOSITORY" --watch --fail-fast; then
    fail "One or more checks failed, were cancelled, or did not complete successfully; refusing to merge."
fi

post_checks_state="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json mergeStateStatus,mergeable,isDraft --jq '[.isDraft,.mergeable,.mergeStateStatus] | @tsv')" \
    || fail "Unable to refresh mergeability after checks completed."
IFS=$'\t' read -r is_draft mergeable merge_state <<< "$post_checks_state"
[[ "$is_draft" == "false" ]] || fail "PR #$pr_number is a draft."
[[ "$mergeable" == "MERGEABLE" ]] || fail "PR #$pr_number is not mergeable after checks completed."
[[ "$merge_state" == "CLEAN" || "$merge_state" == "HAS_HOOKS" || "$merge_state" == "UNSTABLE" ]] \
    || fail "PR #$pr_number remains blocked after checks completed (merge state: $merge_state)."

pr_head_sha="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json headRefOid --jq '.headRefOid')" \
    || fail "Unable to read the PR head SHA."
[[ "$pr_head_sha" == "$head_sha" ]] \
    || fail "PR head changed from reviewed SHA '$head_sha' to '$pr_head_sha'. Review the new changes before merging."

log ""
log "PR #$pr_number is mergeable and required checks passed."
log "Merge method: standard merge commit (--merge)"
confirm_exact \
    "This will merge PR #$pr_number into '$BASE_BRANCH' on GitHub." \
    "MERGE PR #$pr_number"

# Re-check immediately before the write operation to reduce time-of-check/time-of-use risk.
final_state="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json mergeStateStatus,mergeable,headRefOid,isDraft,state --jq '[.state,.isDraft,.mergeable,.mergeStateStatus,.headRefOid] | @tsv')" \
    || fail "Unable to perform the final PR state check."
IFS=$'\t' read -r pr_state is_draft mergeable merge_state final_head_sha <<< "$final_state"
[[ "$pr_state" == "OPEN" ]] || fail "PR #$pr_number is no longer open."
[[ "$is_draft" == "false" ]] || fail "PR #$pr_number is now a draft."
[[ "$mergeable" == "MERGEABLE" ]] || fail "PR #$pr_number is no longer mergeable."
[[ "$merge_state" == "CLEAN" || "$merge_state" == "HAS_HOOKS" || "$merge_state" == "UNSTABLE" ]] \
    || fail "PR #$pr_number is now blocked (merge state: $merge_state)."
[[ "$final_head_sha" == "$head_sha" ]] || fail "PR head changed after confirmation; refusing to merge."

gh pr checks "$pr_number" --repo "$EXPECTED_REPOSITORY" \
    || fail "Checks changed after confirmation; refusing to merge."

gh pr merge "$pr_number" \
    --repo "$EXPECTED_REPOSITORY" \
    --merge \
    --match-head-commit "$head_sha"

merged_state="$(gh pr view "$pr_number" --repo "$EXPECTED_REPOSITORY" --json state,mergedAt,mergeCommit --jq '[.state,.mergedAt,.mergeCommit.oid] | @tsv')" \
    || fail "Merge command completed, but verification failed."
IFS=$'\t' read -r state merged_at merge_commit <<< "$merged_state"
[[ "$state" == "MERGED" && -n "$merged_at" && -n "$merge_commit" ]] \
    || fail "PR #$pr_number was not confirmed as merged."

log "Merged PR #$pr_number successfully."
log "Merge commit: $merge_commit"
log "Merged at:    $merged_at"
