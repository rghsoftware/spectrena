---
description: Analyze project structure and spectrena configuration
arguments: []
---

# Analyze

Analyze the current project's spectrena setup, configuration, and spec status.

## Execution

### 1. Verify Spectrena Project

```bash
if [ ! -d ".spectrena" ]; then
    echo "❌ Not a spectrena project (no .spectrena/ directory)"
    echo "Run 'spectrena init' to initialize"
    exit 1
fi
echo "✓ Spectrena project detected"
```

### 2. Configuration Summary

```bash
echo ""
echo "=== Configuration ==="
if [ -f ".spectrena/config.yml" ]; then
    cat .spectrena/config.yml
else
    echo "⚠️ No config.yml found"
fi
```

### 3. Project Structure

```bash
echo ""
echo "=== Project Structure ==="
echo ""
echo ".spectrena/"
ls -la .spectrena/ 2>/dev/null | tail -n +2

if [ -d ".spectrena/templates" ]; then
    echo ""
    echo ".spectrena/templates/"
    ls -la .spectrena/templates/ 2>/dev/null | tail -n +2
fi

if [ -d ".spectrena/memory" ]; then
    echo ""
    echo ".spectrena/memory/"
    ls -la .spectrena/memory/ 2>/dev/null | tail -n +2
fi
```

### 4. Specs Status

```bash
echo ""
echo "=== Specs ==="

if [ -d "specs" ]; then
    SPEC_COUNT=$(find specs -maxdepth 1 -type d | tail -n +2 | wc -l)
    echo "Total specs: $SPEC_COUNT"
    echo ""

    for spec_dir in specs/*/; do
        if [ -d "$spec_dir" ]; then
            SPEC_ID=$(basename "$spec_dir")

            # Check which files exist
            HAS_SPEC=""
            HAS_PLAN=""
            HAS_TASKS=""

            [ -f "${spec_dir}spec.md" ] && HAS_SPEC="✓" || HAS_SPEC="○"
            [ -f "${spec_dir}plan.md" ] && HAS_PLAN="✓" || HAS_PLAN="○"
            [ -f "${spec_dir}tasks.md" ] && HAS_TASKS="✓" || HAS_TASKS="○"

            # Count task completion if tasks.md exists
            if [ -f "${spec_dir}tasks.md" ]; then
                TOTAL=$(grep -c '^\s*- \[' "${spec_dir}tasks.md" 2>/dev/null || echo "0")
                DONE=$(grep -c '^\s*- \[x\]' "${spec_dir}tasks.md" 2>/dev/null || echo "0")
                TASK_STATUS="${DONE}/${TOTAL}"
            else
                TASK_STATUS="-"
            fi

            echo "  $SPEC_ID"
            echo "    spec:$HAS_SPEC  plan:$HAS_PLAN  tasks:$HAS_TASKS  progress:$TASK_STATUS"
        fi
    done
else
    echo "No specs/ directory found"
fi
```

### 5. Git Branch Status

```bash
echo ""
echo "=== Git Status ==="

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
echo "Current branch: $CURRENT_BRANCH"

# Check if on a spec branch
if [[ "$CURRENT_BRANCH" == spec/* ]]; then
    SPEC_ID="${CURRENT_BRANCH#spec/}"
    echo "Active spec: $SPEC_ID"

    # Show commits on this branch
    COMMIT_COUNT=$(git rev-list --count main..$CURRENT_BRANCH 2>/dev/null || echo "?")
    echo "Commits ahead of main: $COMMIT_COUNT"
fi

# List spec branches
echo ""
echo "Spec branches:"
git branch --list 'spec/*' 2>/dev/null | while read branch; do
    echo "  $branch"
done

if [ -z "$(git branch --list 'spec/*' 2>/dev/null)" ]; then
    echo "  (none)"
fi
```

### 6. Backlog Status (if enabled)

```bash
echo ""
echo "=== Backlog ==="

# Check config for backlog path
if [ -f ".spectrena/config.yml" ]; then
    BACKLOG_ENABLED=$(grep -A1 "^backlog:" .spectrena/config.yml | grep "enabled:" | grep -o "true\|false")

    if [ "$BACKLOG_ENABLED" = "true" ]; then
        BACKLOG_PATH=$(grep -A2 "^backlog:" .spectrena/config.yml | grep "path:" | sed 's/.*path: *"\?\([^"]*\)"\?/\1/')
        BACKLOG_PATH=${BACKLOG_PATH:-.spectrena/backlog.md}

        if [ -f "$BACKLOG_PATH" ]; then
            echo "Backlog: $BACKLOG_PATH"

            # Count by status
            NOT_STARTED=$(grep -c "⬜" "$BACKLOG_PATH" 2>/dev/null || echo "0")
            IN_PROGRESS=$(grep -c "🟨" "$BACKLOG_PATH" 2>/dev/null || echo "0")
            COMPLETE=$(grep -c "🟩" "$BACKLOG_PATH" 2>/dev/null || echo "0")
            BLOCKED=$(grep -c "🚫" "$BACKLOG_PATH" 2>/dev/null || echo "0")

            echo "  ⬜ Not started: $NOT_STARTED"
            echo "  🟨 In progress: $IN_PROGRESS"
            echo "  🟩 Complete: $COMPLETE"
            echo "  🚫 Blocked: $BLOCKED"
        else
            echo "Backlog enabled but file not found: $BACKLOG_PATH"
        fi
    else
        echo "Backlog: disabled"
    fi
else
    echo "Backlog: (no config)"
fi
```

### 7. Lineage Status (if enabled)

```bash
echo ""
echo "=== Lineage Database ==="

if [ -f ".spectrena/config.yml" ]; then
    LINEAGE_ENABLED=$(grep -A1 "^lineage:" .spectrena/config.yml | grep "enabled:" | grep -o "true\|false")

    if [ "$LINEAGE_ENABLED" = "true" ]; then
        if [ -d ".spectrena/lineage.db" ]; then
            DB_SIZE=$(du -sh .spectrena/lineage.db 2>/dev/null | cut -f1)
            echo "Lineage DB: .spectrena/lineage.db ($DB_SIZE)"
        else
            echo "Lineage enabled but database not found"
        fi
    else
        echo "Lineage: disabled"
    fi
else
    echo "Lineage: (no config)"
fi
```

### 8. Version Info

```bash
echo ""
echo "=== Version ==="

if [ -f ".spectrena/.version" ]; then
    echo "Template version: $(cat .spectrena/.version)"
else
    echo "Template version: unknown (no .version file)"
fi

# Check spectrena CLI version
if command -v spectrena &> /dev/null; then
    echo "CLI version: $(spectrena --version 2>/dev/null || echo 'unknown')"
else
    echo "CLI: not installed"
fi
```

## Summary Report

After running all checks, provide a summary:

### Analysis Summary

| Component | Status |
|-----------|--------|
| Config | (Valid/Missing) |
| Templates | (count) files |
| Specs | (count) total |
| Backlog | (status) |
| Lineage | (status) |
| Git | (branch info) |

### Recommendations

Based on the analysis, provide actionable recommendations:

- If specs are incomplete, suggest next steps (e.g., `/spectrena.plan`, `/spectrena.tasks`)
- If tasks are complete, suggest `/spectrena.spec.finish`
- If no specs exist, suggest `/spectrena.specify` to create one
