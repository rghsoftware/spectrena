---
description: Review and merge pending template updates
arguments: []
---

# Review and Merge Pending Template Updates

After running `spectrena update`, some files may require manual review because they have been customized from the original template. This command helps you review and merge those changes.

## Your Task

1. **Check for pending updates**: Look for `.spectrena/pending-updates.md`
   - If the file doesn't exist or is empty, inform the user there are no pending updates

2. **For each pending file**, show:
   - Current version (what the user has now)
   - New version (what the template update provides)
   - Unified diff highlighting the changes
   - Ask the user what they want to do

3. **User options for each file**:
   - **A: Keep mine** - Preserve the user's current version (lose template updates)
   - **B: Take theirs** - Use the new template version (lose user customizations)
   - **C: Merge** - Intelligently combine both (recommended when possible)
   - **D: Skip** - Decide later (leave in pending-updates.md)

4. **When user chooses "Merge"**:
   - Identify what the user customized (their additions/changes from original)
   - Identify what the template updated (new features/fixes)
   - Combine both:
     - Keep user's customizations
     - Add new template features
     - If there are conflicts, ask the user to resolve them
   - Write the merged result to the file

5. **After processing all files**:
   - Update `.spectrena/pending-updates.md` to remove resolved items
   - If there are still pending items, keep them in the file
   - If all items are resolved, delete the file
   - Commit the changes with a descriptive message

## Merge Strategy

When merging template updates with user customizations:

1. **Non-conflicting changes**: Simply combine them
   - User added section A → Keep it
   - Template added section B → Add it
   - Result: Both sections present

2. **Conflicting changes**: Ask user to decide
   - User modified line X to Y
   - Template modified line X to Z
   - Show both versions and ask which to keep or how to combine

3. **Structural changes**: Use the new structure, preserve content
   - Template reorganized sections
   - Keep user's content items in the new structure

## Example Interaction

```
## Pending Updates Review

Found 2 files requiring review in .spectrena/pending-updates.md

---

### 1/2: .spectrena/templates/spec-template.md

**Your customization**: Added "## Security Considerations" section at line 45
**Template update**: Added "## Performance Requirements" section, fixed typo in header

**Diff**:
@@ -12,7 +12,7 @@
-## Requiremnts
+## Requirements

+## Performance Requirements
+
+- Response time targets
+- Resource constraints

These changes don't conflict. Recommended action: **Merge**

**Options**:
- A: Keep mine (lose Performance Requirements section)
- B: Take theirs (lose Security Considerations section)
- C: Merge (keep both sections) ✓ Recommended
- D: Skip for now

[Wait for user response]

User selects: C

✓ Merged successfully:
  - Kept your "Security Considerations" section
  - Added new "Performance Requirements" section
  - Fixed header typo

---

### 2/2: .spectrena/templates/plan-template.md

**Your customization**: None detected (hash matches original)
**Template update**: Added "## Rollback Plan" section

Since you haven't customized this file, it's safe to update directly.

**Options**:
- A: Keep mine
- B: Take theirs ✓ Recommended
- C: Skip

[Wait for user response]

User selects: B

✓ Updated .spectrena/templates/plan-template.md

---

## Summary

- Merged: 1 file
- Updated: 1 file
- Skipped: 0 files

All pending updates resolved!

Committing changes...

$ git add .spectrena/templates/
$ git commit -m "chore: merge spectrena template updates

- Merged spec-template.md (kept custom Security section, added Performance section)
- Updated plan-template.md (added Rollback Plan section)"

✓ Changes committed
```

## Conflict Resolution Example

When changes conflict:

```
### Conflicting Changes Detected

**Your version** (line 15-20):
```markdown
## Requirements
- Functional requirements
- User stories
```

**New template version** (line 15-22):
```markdown
## Functional Requirements
- User-facing requirements
- System requirements

## Non-Functional Requirements
- Performance
- Security
```

The template restructured this section into two separate sections.

**Options**:
1. Keep your simpler structure
2. Use the new detailed structure
3. Merge - I'll move your content into the new structure

User selects: 3

✓ Merged - Kept your requirement items organized into the new two-section structure.
```

## Important Notes

- **Always preserve user content** - When in doubt, merge rather than replace
- **Explain your reasoning** - Help users understand what changed and why
- **Test merge results** - Make sure merged content is valid Markdown
- **Commit atomically** - Group related changes in a single commit
- **Update hashes** - After merging, update `.spectrena/.template-hashes.json`

## Error Handling

If you encounter issues:
- File not found → Skip and warn user
- Cannot parse diff → Show both versions and ask user to manually merge
- Git commit fails → Show error and let user commit manually

Begin by checking for `.spectrena/pending-updates.md` now.
