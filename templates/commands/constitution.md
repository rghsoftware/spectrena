---
description: Establish project principles and guidelines
arguments: []
---

# Constitution

Establish foundational project principles and coding guidelines.

## Usage

```
/spectrena.constitution
```

## Behavior

1. Check if `.spectrena/memory/constitution.md` exists
2. If not, ask about:
   - Project goals and values
   - Tech stack decisions
   - Coding standards
   - Architecture principles
   - Testing requirements
3. Generate constitution document
4. Write to `.spectrena/memory/constitution.md`
5. **Git: Commit:**
   ```bash
   git add .spectrena/memory/constitution.md
   git commit -m "docs: Establish project constitution"
   ```

## Output

Creates `.spectrena/memory/constitution.md`:

```markdown
# Project Constitution

## Mission
[What this project aims to achieve]

## Principles
1. [Core principle]
2. [Core principle]

## Tech Stack
- Language: [e.g., Dart/Flutter]
- Backend: [e.g., Supabase]
- Database: [e.g., PostgreSQL]

## Code Standards
- [Linting rules]
- [Naming conventions]
- [File organization]

## Testing Requirements
- [Unit test coverage]
- [Integration test approach]

## Architecture Decisions
- [Key ADRs]
```

## Example

```
User: /spectrena.constitution

Claude: Let's establish your project's foundation.

1. What's the core mission of this project?
2. What tech stack are you using?
3. Any strong opinions on code style?

User: ADHD productivity app, Flutter + Supabase, clean architecture

Claude: [generates constitution.md]

$ git add .spectrena/memory/constitution.md
$ git commit -m "docs: Establish project constitution"

Created .spectrena/memory/constitution.md
```
