---
description: Verify spec completion, review implementation against requirements, and create a pull/merge request.
arguments:
  - name: spec-id
    description: Spec ID to finish (optional - detects from branch)
    required: false
  - name: draft
    description: Create as draft PR/MR
    required: false
    flag: -d,--draft
  - name: skip-review
    description: Skip AI compliance review (only check tasks)
    required: false
    flag: --skip-review
---

# Spec Finish

Verify a spec is complete and create a pull/merge request.

## Usage

```bash
# On spec branch (auto-detect)
/spectrena.spec.finish

# Explicit spec
/spectrena.spec.finish core-001-project-setup

# Create as draft
/spectrena.spec.finish --draft

# Quick mode (skip AI review)
/spectrena.spec.finish --skip-review
```

---

## Execution Steps

### 1. Environment Detection

First, detect the current environment and spec:

```bash
# Get current branch
BRANCH=$(git branch --show-current)

# Extract SPEC-ID from branch name (spec/{SPEC-ID})
if [[ "$BRANCH" == spec/* ]]; then
    SPEC_ID="${BRANCH#spec/}"
else
    # Check if spec-id provided as argument
    if [ -n "{ARGS}" ] && [ "{ARGS}" != "--draft" ] && [ "{ARGS}" != "--skip-review" ]; then
        SPEC_ID="{ARGS}"
    else
        echo "❌ Error: Not on a spec branch and no spec-id provided"
        echo "Usage: /spectrena.spec.finish [spec-id]"
        exit 1
    fi
fi

echo "Finishing spec: $SPEC_ID"
```

Verify required files exist:

```bash
if [ ! -f "specs/$SPEC_ID/spec.md" ]; then
    echo "❌ Error: Spec not found: specs/$SPEC_ID/spec.md"
    exit 1
fi

if [ ! -f "specs/$SPEC_ID/tasks.md" ]; then
    echo "❌ Error: Tasks not found: specs/$SPEC_ID/tasks.md"
    echo "Run /spectrena.tasks first"
    exit 1
fi
```

Read config:

```bash
# Read git provider from config
if [ -f ".spectrena/config.yml" ]; then
    PROVIDER=$(grep -A 5 "^git:" .spectrena/config.yml | grep "provider:" | sed 's/.*provider: *"\?\([^"]*\)"\?.*/\1/')
    DEFAULT_BRANCH=$(grep -A 5 "^git:" .spectrena/config.yml | grep "default_branch:" | sed 's/.*default_branch: *"\?\([^"]*\)"\?.*/\1/')
    AUTO_DELETE=$(grep -A 5 "^git:" .spectrena/config.yml | grep "auto_delete_branch:" | sed 's/.*auto_delete_branch: *"\?\([^"]*\)"\?.*/\1/')
else
    PROVIDER="github"
    DEFAULT_BRANCH="main"
    AUTO_DELETE="true"
fi

# Parse flags from arguments
DRAFT_FLAG=""
SKIP_REVIEW=""
if [[ "{ARGS}" == *"--draft"* ]] || [[ "{ARGS}" == *"-d"* ]]; then
    DRAFT_FLAG="--draft"
fi
if [[ "{ARGS}" == *"--skip-review"* ]]; then
    SKIP_REVIEW="true"
fi

echo "Provider: $PROVIDER"
echo "Default branch: $DEFAULT_BRANCH"
```

### 2. Task Completion Check (Quick Fail)

Parse `specs/${SPEC_ID}/tasks.md` and verify all checkboxes checked:

```bash
# Count unchecked tasks
UNCHECKED=$(grep -c '^\s*- \[ \]' "specs/$SPEC_ID/tasks.md" 2>/dev/null || echo "0")

if [ "$UNCHECKED" -gt "0" ]; then
    echo ""
    echo "❌ Cannot finish: $UNCHECKED tasks incomplete"
    echo ""
    echo "Unchecked tasks:"
    grep '^\s*- \[ \]' "specs/$SPEC_ID/tasks.md"
    echo ""
    echo "Complete these tasks with /spectrena.implement or mark them manually."
    exit 1
fi

TOTAL=$(grep -c '^\s*- \[' "specs/$SPEC_ID/tasks.md" 2>/dev/null || echo "0")
echo "✓ All tasks complete ($TOTAL/$TOTAL)"
```

### 3. Spec Compliance Review (Unless --skip-review)

If `--skip-review` is NOT set, review the implementation:

1. **Load spec.md** - Extract requirements and acceptance criteria
2. **Identify changed files** - Compare against default branch
3. **Review implementation** - For each requirement, verify it's implemented

**AI Task:** Read the spec file and review the implementation:

- Read `specs/${SPEC_ID}/spec.md` to understand requirements
- Run: `git diff ${DEFAULT_BRANCH}...HEAD --name-only` to see changed files
- For each major requirement in the spec, identify evidence in the code
- Report any discrepancies between spec and implementation

**Output format:**

```markdown
## Spec Compliance Review

### ✅ Requirements Met

| Requirement | Evidence |
|-------------|----------|
| [requirement 1] | [file:line or description] |
| [requirement 2] | [file:line or description] |

### ⚠️ Discrepancies Found (if any)

#### 1. [Discrepancy name]

**Spec says:** [what the spec requires]
**Implementation:** [what was actually implemented]

**Suggested action:** Update code to match spec / Update spec to match code / Defer to follow-up
```

If discrepancies are found, ask the user how to proceed:
- **Update code** - Make changes to match spec (user should re-run after fixes)
- **Update spec** - Modify spec to document actual implementation
- **Defer** - Note in PR description for future work

If user chooses "Update code", exit with message to fix and re-run. If "Update spec", make the changes and continue.

### 4. Pre-Submit Verification

Check for uncommitted changes and branch status:

```bash
echo ""
echo "## Pre-Submit Checklist"
echo ""

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  Uncommitted changes detected"
    echo ""
    git status --short
    echo ""
    echo "Commit or stash changes before finishing:"
    echo "  git add ."
    echo "  git commit -m 'your message'"
    exit 1
fi
echo "✓ No uncommitted changes"

# Check branch is up to date
git fetch origin "$DEFAULT_BRANCH" 2>/dev/null || true
BEHIND=$(git rev-list HEAD..origin/"$DEFAULT_BRANCH" --count 2>/dev/null || echo "0")
if [ "$BEHIND" -gt "0" ]; then
    echo "⚠️  Branch is $BEHIND commits behind $DEFAULT_BRANCH"
    echo ""
    echo "Consider rebasing:"
    echo "  git rebase origin/$DEFAULT_BRANCH"
    echo ""
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Branch is up to date with $DEFAULT_BRANCH"
fi

echo "✓ All tasks complete ($TOTAL/$TOTAL)"
echo "✓ All requirements verified"
echo ""
echo "Ready to create pull request."
echo ""
```

### 5. Generate PR/MR Content

Extract spec title and generate PR body:

```bash
# Extract spec title from spec.md
SPEC_TITLE=$(grep "^# " "specs/$SPEC_ID/spec.md" | head -n 1 | sed 's/^# //')

# Generate PR title
PR_TITLE="$SPEC_ID: $SPEC_TITLE"

# Generate changed files list
CHANGED_FILES=$(git diff --name-only "$DEFAULT_BRANCH"...HEAD)

# Extract requirements from spec
REQUIREMENTS=$(grep -E "^[-*] " "specs/$SPEC_ID/spec.md" | grep -v "^[-*] \[ \]" | head -n 10)

# Create PR body
PR_BODY="## Summary

Implements $SPEC_ID: $SPEC_TITLE

## Changes

\`\`\`
$CHANGED_FILES
\`\`\`

## Requirements

$REQUIREMENTS

## Spec Reference

See: \`specs/$SPEC_ID/spec.md\`
"
```

### 6. Create Pull/Merge Request

Create PR/MR based on provider:

**For GitHub:**

```bash
if [ "$PROVIDER" = "github" ]; then
    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        echo "❌ Error: gh CLI not found"
        echo "Install from: https://cli.github.com/"
        echo ""
        echo "Or set git.provider to 'other' in .spectrena/config.yml"
        exit 1
    fi

    # Check if PR already exists
    EXISTING_PR=$(gh pr list --head "spec/$SPEC_ID" --json number --jq '.[0].number' 2>/dev/null || echo "")

    if [ -n "$EXISTING_PR" ]; then
        PR_URL=$(gh pr view "$EXISTING_PR" --json url --jq '.url')
        echo "✓ PR #$EXISTING_PR already exists for this branch"
        echo ""
        echo "View: $PR_URL"
        exit 0
    fi

    # Create PR
    echo "Creating GitHub pull request..."
    gh pr create \
        --base "$DEFAULT_BRANCH" \
        --head "spec/$SPEC_ID" \
        --title "$PR_TITLE" \
        --body "$PR_BODY" \
        $DRAFT_FLAG

    # Get PR URL
    PR_URL=$(gh pr view --json url --jq '.url')

    echo ""
    echo "---"
    echo "## Spec Finished"
    echo ""
    echo "**Spec:** $SPEC_ID"
    echo "**PR:** $PR_URL"
    echo ""
    echo "### Summary"
    echo "- Tasks: $TOTAL/$TOTAL complete"
    echo "- Files changed: $(echo "$CHANGED_FILES" | wc -l)"
    echo ""
    echo "### Next Steps"
    echo "1. Request review on PR"
    echo "2. Address review feedback"
    echo "3. Merge when approved"
    echo ""

    if [ "$AUTO_DELETE" = "true" ]; then
        echo "After merge, the spec branch will be automatically deleted."
    else
        echo "After merge, delete the branch: \`git branch -d spec/$SPEC_ID\`"
    fi
fi
```

**For GitLab:**

```bash
if [ "$PROVIDER" = "gitlab" ]; then
    # Check if glab CLI is available
    if ! command -v glab &> /dev/null; then
        echo "❌ Error: glab CLI not found"
        echo "Install from: https://gitlab.com/gitlab-org/cli"
        echo ""
        echo "Or set git.provider to 'other' in .spectrena/config.yml"
        exit 1
    fi

    # Check if MR already exists
    EXISTING_MR=$(glab mr list --source-branch "spec/$SPEC_ID" 2>/dev/null | grep -oE "![0-9]+" | head -n 1 | tr -d '!')

    if [ -n "$EXISTING_MR" ]; then
        MR_URL=$(glab mr view "$EXISTING_MR" --json web_url --jq '.web_url' 2>/dev/null)
        echo "✓ MR !$EXISTING_MR already exists for this branch"
        echo ""
        echo "View: $MR_URL"
        exit 0
    fi

    # Create MR
    echo "Creating GitLab merge request..."
    glab mr create \
        --source-branch "spec/$SPEC_ID" \
        --target-branch "$DEFAULT_BRANCH" \
        --title "$PR_TITLE" \
        --description "$PR_BODY" \
        $DRAFT_FLAG

    # Get MR URL
    MR_URL=$(glab mr view --json web_url --jq '.web_url')

    echo ""
    echo "---"
    echo "## Spec Finished"
    echo ""
    echo "**Spec:** $SPEC_ID"
    echo "**MR:** $MR_URL"
    echo ""
    echo "### Summary"
    echo "- Tasks: $TOTAL/$TOTAL complete"
    echo "- Files changed: $(echo "$CHANGED_FILES" | wc -l)"
    echo ""

    if [ -n "$DRAFT_FLAG" ]; then
        echo "Mark ready for review: \`glab mr update <number> --ready\`"
    fi
fi
```

**For Other (manual):**

```bash
if [ "$PROVIDER" = "other" ]; then
    # Save PR description to file
    echo "$PR_BODY" > "specs/$SPEC_ID/pr-description.md"
    git add "specs/$SPEC_ID/pr-description.md"
    git commit -m "spec($SPEC_ID): Add PR description for manual submission"

    echo "Git provider set to 'other'. Create PR manually."
    echo ""
    echo "Branch: spec/$SPEC_ID"
    echo "Target: $DEFAULT_BRANCH"
    echo ""
    echo "PR description saved to: specs/$SPEC_ID/pr-description.md"
fi
```

### 7. Update Backlog Status

If backlog enabled and spec exists in backlog:

```bash
# Check if backlog is enabled
if [ -f ".spectrena/config.yml" ]; then
    BACKLOG_ENABLED=$(grep -A 5 "^backlog:" .spectrena/config.yml | grep "enabled:" | grep -i "true" || echo "")

    if [ -n "$BACKLOG_ENABLED" ]; then
        BACKLOG_PATH=$(grep -A 5 "^backlog:" .spectrena/config.yml | grep "path:" | sed 's/.*path: *"\?\([^"]*\)"\?.*/\1/')

        if [ -f "$BACKLOG_PATH" ]; then
            # Update status from 🟨 to 🟩
            # Use case-insensitive search for the spec ID
            if grep -qi "### $SPEC_ID" "$BACKLOG_PATH"; then
                # Update the status in the table
                sed -i.bak -E "s/(### $SPEC_ID.*Status.*\|[[:space:]]*)🟨/\1🟩/gI" "$BACKLOG_PATH"
                rm -f "$BACKLOG_PATH.bak"

                git add "$BACKLOG_PATH"
                git commit -m "backlog: Mark $SPEC_ID complete"
                git push origin "spec/$SPEC_ID" 2>/dev/null || true

                echo "✓ Backlog status updated: 🟨 → 🟩"
            fi
        fi
    fi
fi
```

---

## Error Handling

| Error | Response |
|-------|----------|
| Not on spec branch, no spec-id given | "Not on a spec branch. Provide spec-id: `/spectrena.spec.finish SPEC-ID`" |
| Spec not found | "Spec `${SPEC_ID}` not found. Run `/spectrena.specify` first." |
| tasks.md missing | "No tasks.md found. Run `/spectrena.tasks` first." |
| Incomplete tasks | List unchecked tasks, abort |
| Uncommitted changes | "Commit or stash changes before finishing" |
| gh/glab not installed | "Install `${CLI}` or set git.provider to 'other' in config" |
| PR/MR already exists | Show existing PR URL |

---

## Notes

- The `--skip-review` flag skips the AI compliance review and only checks task completion
- The `--draft` flag creates a draft PR/MR that requires manual marking as ready
- If discrepancies are found during review, you can update the spec, update code, or defer
- Backlog status is automatically updated from 🟨 (in progress) to 🟩 (complete)
