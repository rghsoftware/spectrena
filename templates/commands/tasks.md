---
description: Generate actionable tasks from plan
arguments: []
---

# Tasks

Generate actionable tasks from the current spec's plan.

## Usage

```
/spectrena.tasks
```

## Behavior

1. Detect current spec from branch `spec/{SPEC-ID}`
2. **Git: Ensure on spec branch:**
   ```bash
   git checkout spec/{SPEC-ID}
   ```
3. Read `specs/{SPEC-ID}/plan.md`
4. Extract phases and high-level tasks
5. Break into atomic, actionable tasks
6. Write to `specs/{SPEC-ID}/tasks.md`
7. **Git: Commit:**
   ```bash
   git add specs/{SPEC-ID}/tasks.md
   git commit -m "tasks({SPEC-ID}): Generate implementation tasks"
   ```

## Task Format

```markdown
# Tasks: SPEC-ID

## Phase 1: [Name]

- [ ] Task 1 description
  - Acceptance: [How to verify complete]
  - Files: [Expected files to create/modify]

- [ ] Task 2 description
  ...
```

## Example

```
User: /spectrena.tasks

Claude: Current branch: spec/CORE-001-oauth-login
Reading specs/CORE-001-oauth-login/plan.md...

Generating tasks:

## Phase 1: OAuth Provider Setup

- [ ] Create Google Cloud project and OAuth credentials
  - Acceptance: Client ID and secret in .env
  - Files: .env.example, docs/oauth-setup.md

- [ ] Create GitHub OAuth app
  - Acceptance: Client ID and secret in .env
  - Files: .env.example

[writes tasks.md]

$ git add specs/CORE-001-oauth-login/tasks.md
$ git commit -m "tasks(CORE-001-oauth-login): Generate implementation tasks"

Created specs/CORE-001-oauth-login/tasks.md
```
