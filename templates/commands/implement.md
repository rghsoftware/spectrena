---
description: Execute implementation for current task
arguments:
  - name: task
    description: Task number or description to implement
    required: false
---

# Implement

Execute implementation for a specific task or next uncompleted task.

## Usage

```
/spectrena.implement
/spectrena.implement 3
/spectrena.implement "OAuth callback endpoint"
```

## Behavior

1. Detect current spec from branch `spec/{SPEC-ID}`
2. **Git: Ensure on spec branch:**
   ```bash
   git checkout spec/{SPEC-ID}
   ```
3. Read `specs/{SPEC-ID}/tasks.md`
4. Find target task (next unchecked, by number, or by search)
5. Implement the task:
   - Create/modify files as specified
   - Follow spec requirements
   - Write tests if applicable
6. Mark task complete in `tasks.md` (change `- [ ]` to `- [x]`)
7. **Git: Stage all changes and commit:**
   ```bash
   git add .
   git commit -m "feat({SPEC-ID}): [task description]"
   ```

## Commit Message Format

```
feat({SPEC-ID}): {task description}

Task: {task number from tasks.md}
Spec: specs/{SPEC-ID}/spec.md
```

## Example

```
User: /spectrena.implement

Claude: Current branch: spec/CORE-001-oauth-login
Reading specs/CORE-001-oauth-login/tasks.md...

Next task: #3 - Create OAuth callback endpoint

Implementing...

[creates src/auth/oauth_callback.py]
[creates tests/test_oauth_callback.py]
[updates tasks.md - marks #3 complete]

$ git add .
$ git commit -m "feat(CORE-001-oauth-login): Create OAuth callback endpoint"

Task #3 complete
Committed: feat(CORE-001-oauth-login): Create OAuth callback endpoint
```
