---
description: Create or generate content for a specification
arguments:
  - name: description
    description: Brief title/description for the spec OR spec-id from backlog
    required: false
  - name: component
    description: Component prefix (CORE, API, UI, etc.)
    required: false
    flag: -c,--component
---

# Specify

Create or generate content for a specification, optionally pulling context from backlog.

## Usage

```
/spectrena.specify core-001-project-setup    # From backlog
/spectrena.specify "Brief description" -c COMPONENT  # Custom spec
/spectrena.specify                            # Interactive mode
```

## Backlog Support

**When backlog is enabled** (check `.spectrena/config.yml`):

1. **Check if argument matches backlog entry** (case-insensitive)
2. If found in backlog:
   - Load scope, dependencies, references, covers/does-not-cover
   - Check dependency status, warn if incomplete
   - Read reference docs (expand abbreviations via config)
   - Generate spec from backlog context
   - Update backlog status ⬜ → 🟨
3. If NOT in backlog: Fall back to custom mode

## Modes

### Mode 1: From Backlog

**When:** Argument matches a spec-id in backlog

**Steps:**

1. Read `.spectrena/config.yml` to get backlog path
2. Parse backlog file
3. Find matching entry (case-insensitive)
4. **Check dependencies:**
   - List depends_on specs with their status
   - Warn if any are not 🟩 (complete)
   - Ask user to confirm proceeding
5. **Load reference docs:**
   - Expand abbreviations (e.g., `REQ` → `docs/requirements.md`)
   - Support §Section syntax (e.g., `ARCH §Database`)
   - Read doc content for context
6. **Git: Ensure clean working tree**
7. Create directory: `specs/{SPEC-ID}/`
8. Copy template: `.spectrena/templates/spec-template.md`
9. **Git: Create and checkout branch:**
   ```bash
   git checkout -b spec/{SPEC-ID}
   ```
10. **Generate spec content** using:
    - Scope from backlog
    - Covers / Does NOT cover lists
    - Reference doc content
    - Weight (LIGHTWEIGHT/STANDARD/FORMAL)
11. Write to `specs/{SPEC-ID}/spec.md`
12. **Update backlog status** ⬜ → 🟨
13. **Git: Commit:**
    ```bash
    git add specs/{SPEC-ID}/ .spectrena/backlog.md
    git commit -m "spec({SPEC-ID}): Initialize specification from backlog"
    ```

**Example backlog entry:**

```markdown
### core-001-project-setup

**Scope:** Project structure, build system, tooling configuration

| Attribute | Value |
|-----------|-------|
| **Weight** | STANDARD |
| **Status** | ⬜ |
| **Depends On** | (none) |
| **References** | ARCH §Project Structure |

**Covers:**
- Repository structure
- Build tooling setup

**Does NOT cover:**
- Application implementation
```

**Reference doc expansion:**

- `ARCH §Project Structure` → Read `docs/architecture.md`, extract "Project Structure" section
- `REQ, DOM` → Read `docs/requirements.md` and `docs/domain-model.md`

### Mode 2: Custom Spec (Fallback)

**When:** Backlog disabled OR argument doesn't match backlog entry

**Steps:**

1. Validate component (prompt if required but missing)
2. If description brief (< 20 words), ask 2-3 clarifying questions
3. Read `.spectrena/config.yml` for spec ID template
4. Find next spec number by scanning `specs/` directory
5. Generate spec ID: apply template (e.g., `CORE-001-user-auth`)
6. **Git: Ensure clean working tree**
7. Create directory: `specs/{SPEC-ID}/`
8. Copy template: `.spectrena/templates/spec-template.md`
9. **Git: Create and checkout branch:**
   ```bash
   git checkout -b spec/{SPEC-ID}
   ```
10. Generate full spec content based on description + clarifications
11. Write to `specs/{SPEC-ID}/spec.md`
12. **Git: Commit:**
    ```bash
    git add specs/{SPEC-ID}/
    git commit -m "spec({SPEC-ID}): Initialize specification"
    ```

### Mode 3: Interactive (No Arguments)

**Steps:**

1. Detect current spec:
   - Check git branch for `spec/{SPEC-ID}` pattern
   - Or find spec directory in current path
2. If on spec branch, fill existing spec (Mode 2 flow)
3. If NOT on spec branch:
   - If backlog enabled: Show available backlog entries (⬜ status)
   - Ask user to select OR provide custom description
4. Proceed with Mode 1 or Mode 2 accordingly

## Dependency Status Warnings

**When loading from backlog:**

| Dependency Status | Action |
|-------------------|--------|
| All 🟩 | Proceed normally |
| Some 🟨 | Warn, ask to confirm |
| Some ⬜ | Warn strongly, ask to confirm |
| Some 🚫 | Error, suggest unblocking first |

**Example warning:**

```
⚠️  Dependencies not complete:
  • core-001-database ⬜ (not started)
  • core-002-auth 🟨 (in progress)

Proceeding may result in rework. Continue? (y/N)
```

## Reference Doc Sections

**Format:** `ABBREV §Section`

**Behavior:**

1. Read full doc from path
2. If `§Section` specified:
   - Find markdown heading `## Section` or `# Section`
   - Extract content until next heading at same level
3. If NOT specified, use full doc

**Example:**

```yaml
# .spectrena/config.yml
backlog:
  reference_docs:
    ARCH: "docs/architecture.md"
```

```markdown
# In backlog
**References:** ARCH §Database, REQ
```

**Result:**

- Read `docs/architecture.md`, extract "Database" section
- Read `docs/requirements.md` (full doc)

## Spec ID Generation

Read from `.spectrena/config.yml`:

```yaml
spec_id:
  template: "{component}-{NNN}-{slug}"
  padding: 3
  components:
    - CORE
    - API
    - UI
```

Apply template:

- `{component}` → provided component (e.g., CORE)
- `{NNN}` → next number, zero-padded (e.g., 001)
- `{slug}` → slugified description (e.g., user-auth)

## Content Generation

Fill sections based on description or backlog:

| Section | Source |
|---------|--------|
| **Title** | From description or backlog scope |
| **Problem** | Infer from description/scope |
| **Solution** | Proposed approach |
| **Scope** | Covers / Does NOT cover from backlog |
| **Dependencies** | From backlog depends_on |
| **Acceptance Criteria** | Testable requirements |

## Examples

### Example 1: From Backlog

```
User: /spectrena.specify core-001-project-setup

Claude: Found core-001-project-setup in backlog.
✓ No dependencies
✓ Loading reference: ARCH §Project Structure

Creating CORE-001-project-setup...

$ git checkout -b spec/core-001-project-setup
Switched to a new branch 'spec/core-001-project-setup'

[creates directory, writes spec.md]
[updates backlog status ⬜ → 🟨]

$ git add specs/core-001-project-setup/ .spectrena/backlog.md
$ git commit -m "spec(core-001-project-setup): Initialize specification from backlog"

Created specs/core-001-project-setup/spec.md
On branch spec/core-001-project-setup
```

### Example 2: Custom Spec

```
User: /spectrena.specify "OAuth login" -c CORE

Claude: Not found in backlog, creating custom spec.

I'll create the CORE auth spec. Quick questions:
1. Which OAuth providers? (Google, GitHub, etc.)
2. Need refresh tokens?
3. Any role-based access?

User: Google and GitHub, yes refresh tokens, no roles yet

Claude: Creating CORE-001-oauth-login...

$ git checkout -b spec/CORE-001-oauth-login
Switched to a new branch 'spec/CORE-001-oauth-login'

[creates directory, writes spec.md]

$ git add specs/CORE-001-oauth-login/
$ git commit -m "spec(CORE-001-oauth-login): Initialize specification"

Created specs/CORE-001-oauth-login/spec.md
On branch spec/CORE-001-oauth-login
```

### Example 3: Dependency Warning

```
User: /spectrena.specify core-003-authentication

Claude: Found core-003-authentication in backlog.

⚠️  Dependencies not complete:
  • core-001-project-setup 🟩 (complete)
  • core-002-database ⬜ (not started)

Proceeding may result in rework. Continue? (y/N)

User: n

Claude: Cancelled. Consider running /spectrena.specify core-002-database first.
```

## Notes

- **Max 3 clarification rounds** for custom specs
- Backlog lookup is case-insensitive
- Status updates are atomic (file write)
- Reference docs are optional context, not required
- Weight field from backlog guides formality level
