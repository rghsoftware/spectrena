---
description: Create or generate content for a specification
arguments:
  - name: description
    description: Brief title/description for the spec
    required: false
  - name: component
    description: Component prefix (CORE, API, UI, etc.)
    required: false
    flag: -c,--component
---

# Specify

Create or generate content for a specification.

## Usage

```
/spectrena.specify "Brief description" -c COMPONENT
/spectrena.specify
```

## Input Expectations

**Brief is fine.** If the description lacks detail, ask 2-3 clarifying questions before generating.

| Input | Action |
|-------|--------|
| `"User auth"` | Ask: "OAuth? Username/password? What providers?" |
| `"Monorepo setup"` | Ask: "What tools? Melos? Nx? What's being shared?" |
| Detailed paragraph | Generate directly |

**Max 3 clarification rounds.** Then generate with stated assumptions.

## Behavior

### Mode 1: With Description (Create New)

1. Validate component (prompt if required but missing)
2. If description brief (< 20 words), ask 2-3 clarifying questions
3. Read `.spectrena/config.yml` for spec ID template
4. Find next spec number by scanning `specs/` directory
5. Generate spec ID: apply template (e.g., `CORE-001-user-auth`)
6. **Git: Ensure clean working tree** (warn if uncommitted changes)
7. Create directory: `specs/{SPEC-ID}/`
8. Copy template: `.spectrena/templates/spec-template.md` -> `specs/{SPEC-ID}/spec.md`
9. **Git: Create and checkout branch:**
   ```bash
   git checkout -b spec/{SPEC-ID}
   ```
10. Generate full spec content based on description + clarifications
11. Write content to `specs/{SPEC-ID}/spec.md`
12. **Git: Stage and commit:**
    ```bash
    git add specs/{SPEC-ID}/
    git commit -m "spec({SPEC-ID}): Initialize specification"
    ```

### Mode 2: Without Arguments (Fill Existing)

1. Detect current spec:
   - Check current git branch for `spec/{SPEC-ID}` pattern
   - Or find spec directory in current path
2. **Git: Ensure on correct branch:**
   ```bash
   # If not on spec branch, checkout it
   git checkout spec/{SPEC-ID}
   ```
3. Read existing `spec.md`
4. If description brief, ask clarifying questions
5. Generate content for empty sections
6. Update `spec.md` in place
7. **Git: Commit changes:**
   ```bash
   git add specs/{SPEC-ID}/spec.md
   git commit -m "spec({SPEC-ID}): Expand specification content"
   ```

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
- `{component}` -> provided component (e.g., CORE)
- `{NNN}` -> next number, zero-padded (e.g., 001)
- `{slug}` -> slugified description (e.g., user-auth)

## Content Generation

Fill sections based on description:

| Section | Source |
|---------|--------|
| **Title** | From description |
| **Problem** | Infer from description + clarifications |
| **Solution** | Proposed approach |
| **Scope** | What's in/out |
| **Dependencies** | Other specs this depends on |
| **Acceptance Criteria** | Testable requirements |

## Example

```
User: /spectrena.specify "OAuth login" -c CORE

Claude: I'll create the CORE auth spec. Quick questions:
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
