#!/bin/bash
# create-pr.sh - Automatically create and merge PR using standard merge

# Ensure the GitHub CLI (installed in ~/.local/bin) is found regardless of the terminal's PATH
export PATH="$HOME/.local/bin:$PATH"

BASE_BRANCH="main"
HEAD_BRANCH="develop"
ORG="dvconsultores"

printf '%s\n' "╔════════════════════════════════════════════════════════════╗"
printf '%s\n' "║      AUTO CREATE & MERGE PULL REQUEST                      ║"
printf '%s\n' "╠════════════════════════════════════════════════════════════╣"
printf '%s\n' "║  📌 base:    $BASE_BRANCH                                  ║"
printf '%s\n' "║  📌 compare: $HEAD_BRANCH                                  ║"
printf '%s\n' "║  🔀 merge:   STANDARD (merge commit)                       ║"
printf '%s\n' "║  🏢 Organization: $ORG                                     ║"
printf '%s\n' "╚════════════════════════════════════════════════════════════╝"
echo ""

REPO_NAME="$ORG/GlobalAvicola"

echo ""
echo "📁 Repository: $REPO_NAME"
echo "🔄 Comparing: $HEAD_BRANCH → $BASE_BRANCH"
echo ""

read -r -p "📝 PR Title: " TITLE
TITLE=${TITLE:-"Merge develop into main"}

echo ""
read -r -p "📝 PR Description: " BODY
BODY=${BODY:-"Merging develop into main"}

# Create the PR
echo ""
echo "🚀 Creating pull request..."
PR_URL=$(gh pr create --repo "$REPO_NAME" --base "$BASE_BRANCH" --head "$HEAD_BRANCH" --title "$TITLE" --body "$BODY")
if [ $? -ne 0 ]; then
    echo "❌ PR creation failed"
    exit 1
fi

# Extract PR number
PR_NUMBER=$(echo "$PR_URL" | grep -o '[0-9]*$')
echo "✅ PR #$PR_NUMBER created: $PR_URL"
echo ""

# Automatically merge using standard merge (same as clicking the green button)
echo "🔀 Merging PR #$PR_NUMBER using standard merge..."
gh pr merge "$PR_NUMBER" --repo "$REPO_NAME" --merge
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ PR #$PR_NUMBER merged successfully!"
    echo "📊 Summary:"
    echo "   Base:    $BASE_BRANCH"
    echo "   Compare: $HEAD_BRANCH"
    echo "   Merge:   Standard merge commit ✓"
else
    echo ""
    echo "❌ Merge failed"
    exit 1
fi
