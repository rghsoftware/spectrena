---
description: Refine the current spec through structured clarifying questions.
handoffs:
  - label: Build Technical Plan
    agent: spectrena.plan
    prompt: Create a plan for the spec. I am building with...
---

# /spectrena.clarify

Refine the current spec through structured clarifying questions.

## Usage

```
/spectrena.clarify
```

## Behavior

1. **Find and read current spec.md**

2. **Analyze for gaps:**
   - Ambiguous requirements
   - Missing edge cases
   - Unclear success criteria
   - Unstated assumptions

3. **Ask structured questions** (max 5 at a time)

4. **Update spec.md** with clarifications in a `## Clarifications` section

## Question Categories

| Category | Example Questions |
|----------|-------------------|
| Scope | "Should X also handle Y case?" |
| Edge Cases | "What happens when Z fails?" |
| Integration | "How does this interact with existing A?" |
| Performance | "Expected load/scale requirements?" |
| Security | "Authentication/authorization needs?" |

## Example

```
User: /spectrena.clarify

Claude: Reading specs/CORE-001-oauth-authentication/spec.md...

I have a few clarifying questions:

**Scope:**
1. Should we support account linking (multiple OAuth providers per user)?

**Edge Cases:**
2. What happens if a user's email changes on the OAuth provider side?
3. Should we handle provider outages gracefully?

**Security:**
4. Token refresh strategy - silent refresh or require re-auth?

Answer what you can, skip what you're unsure about.

User: 1. Yes, support linking. 2. Keep our email, don't sync. 3. Yes, show friendly error. 4. Silent refresh.

Claude: ✓ Updated specs/CORE-001-oauth-authentication/spec.md

Added clarifications:
- Account linking: supported
- Email sync: disabled (keep local)
- Provider outages: graceful degradation
- Token refresh: silent
```

## Notes

- **Non-blocking** - user can skip questions
- **Iterative** - run multiple times as understanding evolves
- **Updates spec** - clarifications added to spec.md, not separate file
