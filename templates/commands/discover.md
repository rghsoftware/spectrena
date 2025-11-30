---
description: Explore project idea before committing to architecture
arguments:
  - name: idea
    description: Project idea to explore
    required: false
---

# Discover

Explore a project idea through conversation before committing to architecture.

## Usage

```
/spectrena.discover "My project idea"
/spectrena.discover
```

## Behavior

1. If idea provided, start exploration conversation
2. Ask probing questions about:
   - Problem being solved
   - Target users
   - Key features
   - Technical constraints
   - Scale expectations
3. Summarize findings to `.spectrena/discovery.md`
4. Suggest initial components and spec structure
5. **Git: Commit:**
   ```bash
   git add .spectrena/discovery.md
   git commit -m "docs: Project discovery - [idea summary]"
   ```

## Output

Creates `.spectrena/discovery.md`:

```markdown
# Project Discovery

## Problem Space
[What problem is being solved]

## Target Users
[Who will use this]

## Key Features
[Core functionality]

## Technical Constraints
[Platform, language, integrations]

## Recommended Components
- CORE: Core functionality
- API: Backend services
- UI: User interface

## Suggested First Specs
1. Project setup and tooling
2. [Based on discovery]
```

## Example

```
User: /spectrena.discover "Task manager for ADHD users"

Claude: Let's explore this idea. A few questions:

1. What makes this different from existing task managers?
2. Mobile, desktop, or both?
3. Any specific ADHD strategies to incorporate? (timeboxing, body doubling, etc.)

User: Focus on reducing overwhelm - hide future tasks, show only 1-3 at a time. Mobile first, Flutter.

Claude: [continues exploration, writes discovery.md]

$ git add .spectrena/discovery.md
$ git commit -m "docs: Project discovery - ADHD task manager"

Created .spectrena/discovery.md
```
