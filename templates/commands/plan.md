---
description: Generate an implementation plan for the current spec.
handoffs:
  - label: Create Tasks
    agent: spectrena.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: spectrena.checklist
    prompt: Create a checklist for the following domain...
---

# /spectrena.plan

Generate an implementation plan for the current spec.

## Usage

```
/spectrena.plan
```

## Behavior

1. **Find current spec:**
   - Check if in a spec directory (has spec.md)
   - If not, check git branch for spec ID pattern (`spec/SPEC-ID`)
   - If neither, ask user which spec to plan

2. **Read spec.md** to understand requirements

3. **Create plan.md** with:
   - Tech stack decisions
   - Architecture overview
   - Component breakdown
   - Implementation phases
   - Risk considerations

4. **Optionally create supporting files** if complexity warrants:
   - `data-model.md` - Entity schemas (if data persistence involved)
   - `contracts/` - API specs (if building APIs)

## Output Format

Create `plan.md` in the spec directory:

```markdown
# Implementation Plan: {SPEC_ID}

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| ... | ... | ... |

## Architecture

[High-level architecture description]

## Components

### Component 1: [Name]
- Purpose:
- Key files:
- Dependencies:

### Component 2: [Name]
...

## Implementation Phases

### Phase 1: [Name]
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Name]
...

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ... | ... | ... |

## Open Questions

- [ ] Question from spec that affects implementation
```

## Example

```
User: /spectrena.plan

Claude: Reading specs/CORE-001-oauth-authentication/spec.md...

Creating implementation plan...

✓ Created: specs/CORE-001-oauth-authentication/plan.md

The plan covers:
- Tech stack: FastAPI + authlib + JWT
- 3 implementation phases
- 2 identified risks with mitigations

Ready for /spectrena.tasks when you want to break this into actionable tasks.
```

## Notes

- **No scaffolding required** - this command creates plan.md directly
- **Reads spec first** - plan is based on spec requirements
- **Idempotent** - running again updates existing plan (ask before overwriting)
