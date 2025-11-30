---
description: Create implementation plan for current spec
arguments: []
---

# Plan

Create an implementation plan for the current specification.

## Usage

```
/spectrena.plan
```

## Behavior

1. Detect current spec:
   - Check current git branch for `spec/{SPEC-ID}` pattern
   - Or find spec directory in current path
2. **Git: Ensure on spec branch:**
   ```bash
   git checkout spec/{SPEC-ID}
   ```
3. Read `specs/{SPEC-ID}/spec.md`
4. Copy template: `.spectrena/templates/plan-template.md` -> `specs/{SPEC-ID}/plan.md`
5. Generate implementation plan based on spec content
6. Write to `specs/{SPEC-ID}/plan.md`
7. **Git: Commit:**
   ```bash
   git add specs/{SPEC-ID}/plan.md
   git commit -m "plan({SPEC-ID}): Create implementation plan"
   ```

## Content Generation

| Section | Source |
|---------|--------|
| **Overview** | From spec Problem + Solution |
| **Phases** | Break solution into sequential phases |
| **Tasks** | Concrete implementation tasks per phase |
| **Dependencies** | External deps, order constraints |
| **Risks** | Technical risks and mitigations |

## Example

```
User: /spectrena.plan

Claude: Current branch: spec/CORE-001-oauth-login
Reading specs/CORE-001-oauth-login/spec.md...

Generating implementation plan:

Phase 1: OAuth Provider Setup
- Configure Google OAuth credentials
- Configure GitHub OAuth credentials
- Set up environment variables

Phase 2: Auth Flow Implementation
- Create OAuth redirect endpoints
- Implement token exchange
- Store refresh tokens

[writes plan.md]

$ git add specs/CORE-001-oauth-login/plan.md
$ git commit -m "plan(CORE-001-oauth-login): Create implementation plan"

Created specs/CORE-001-oauth-login/plan.md
```
