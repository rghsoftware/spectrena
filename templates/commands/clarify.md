---
description: Ask clarifying questions about current spec
arguments: []
---

# Clarify

Analyze current spec and ask clarifying questions to fill gaps.

## Usage

```
/spectrena.clarify
```

## Behavior

1. Detect current spec from branch `spec/{SPEC-ID}`
2. **Git: Ensure on spec branch:**
   ```bash
   git checkout spec/{SPEC-ID}
   ```
3. Read `specs/{SPEC-ID}/spec.md`
4. Identify gaps or ambiguities:
   - Vague requirements
   - Missing acceptance criteria
   - Undefined edge cases
   - Unclear dependencies
5. Ask focused questions
6. Update spec.md with answers
7. **Git: Commit updates:**
   ```bash
   git add specs/{SPEC-ID}/spec.md
   git commit -m "spec({SPEC-ID}): Clarify requirements"
   ```

## Example

```
User: /spectrena.clarify

Claude: Current branch: spec/CORE-001-oauth-login
Reading specs/CORE-001-oauth-login/spec.md...

I have a few questions to clarify the spec:

1. **Session Duration**: How long should sessions last before requiring re-auth?
2. **Error Handling**: What should happen if OAuth provider is down?
3. **Account Linking**: Can users link multiple OAuth providers to one account?

User: 7 days, show friendly error with retry, yes allow linking

Claude: [updates spec.md with clarified requirements]

$ git add specs/CORE-001-oauth-login/spec.md
$ git commit -m "spec(CORE-001-oauth-login): Clarify requirements"

Updated specs/CORE-001-oauth-login/spec.md
```
