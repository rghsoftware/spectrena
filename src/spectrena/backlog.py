#!/usr/bin/env python3
"""
Spec backlog parser.

Created: 2025-12-06
Author: Robert Hamilton
"""

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class BacklogEntry:
    """Parsed backlog entry."""

    spec_id: str
    scope: str
    weight: str  # LIGHTWEIGHT, STANDARD, FORMAL
    status: str  # ⬜, 🟨, 🟩, 🚫
    depends_on: list[str]
    references: list[str]
    covers: list[str]
    does_not_cover: list[str]
    raw_content: str


def parse_backlog(path: Path) -> dict[str, BacklogEntry]:
    """Parse backlog file into entries keyed by spec-id."""
    if not path.exists():
        return {}

    content = path.read_text()
    entries = {}

    # Split by ### headings (spec entries)
    pattern = r"^### ([a-z0-9-]+)\s*\n(.*?)(?=^### |\Z)"
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    for spec_id, body in matches:
        entry = _parse_entry(spec_id, body)
        entries[spec_id.lower()] = entry

    return entries


def _parse_entry(spec_id: str, body: str) -> BacklogEntry:
    """Parse a single backlog entry."""

    # Extract scope line
    scope_match = re.search(r"\*\*Scope:\*\*\s*(.+)", body)
    scope = scope_match.group(1).strip() if scope_match else ""

    # Extract table attributes
    weight = _extract_table_value(body, "Weight") or "STANDARD"
    status = _extract_table_value(body, "Status") or "⬜"
    depends_on_raw = _extract_table_value(body, "Depends On") or "(none)"
    references_raw = _extract_table_value(body, "References") or ""

    # Parse depends_on
    if depends_on_raw.lower() in ("(none)", "none", "-", ""):
        depends_on = []
    else:
        depends_on = [
            d.strip() for d in re.split(r"[,\s]+", depends_on_raw) if d.strip()
        ]

    # Parse references (split by comma only, preserve spaces for §Section syntax)
    if references_raw:
        references = [r.strip() for r in references_raw.split(",") if r.strip()]
    else:
        references = []

    # Extract covers list
    covers = _extract_bullet_list(body, "Covers")

    # Extract does not cover list
    does_not_cover = _extract_bullet_list(body, "Does NOT cover")

    return BacklogEntry(
        spec_id=spec_id,
        scope=scope,
        weight=weight,
        status=status,
        depends_on=depends_on,
        references=references,
        covers=covers,
        does_not_cover=does_not_cover,
        raw_content=body,
    )


def _extract_table_value(body: str, key: str) -> str | None:
    """Extract value from markdown table row."""
    pattern = rf"\|\s*\*\*{key}\*\*\s*\|\s*(.+?)\s*\|"
    match = re.search(pattern, body)
    return match.group(1).strip() if match else None


def _extract_bullet_list(body: str, heading: str) -> list[str]:
    """Extract bullet list after a **Heading:** marker."""
    pattern = rf"\*\*{heading}:\*\*\s*\n((?:- .+\n?)+)"
    match = re.search(pattern, body)
    if not match:
        return []

    bullets = match.group(1)
    return [line[2:].strip() for line in bullets.strip().split("\n") if line.startswith("- ")]


def update_backlog_status(path: Path, spec_id: str, new_status: str) -> None:
    """Update a spec's status in the backlog file."""
    content = path.read_text()

    # Find the spec section and update its status
    pattern = rf"(### {re.escape(spec_id)}.*?\|\s*\*\*Status\*\*\s*\|\s*)([⬜🟨🟩🚫])(\s*\|)"

    replacement = rf"\g<1>{new_status}\g<3>"
    new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.DOTALL)

    if new_content != content:
        path.write_text(new_content)


def get_dependency_status(
    entries: dict[str, BacklogEntry], spec_id: str
) -> dict[str, str]:
    """Get status of all dependencies for a spec."""
    entry = entries.get(spec_id.lower())
    if not entry:
        return {}

    result = {}
    for dep_id in entry.depends_on:
        # Try exact match first
        dep_entry = entries.get(dep_id.lower())

        # If not found, try to find by prefix (e.g., "core-001" matches "core-001-project-setup")
        if not dep_entry:
            for full_id, candidate in entries.items():
                if full_id.startswith(dep_id.lower()):
                    dep_entry = candidate
                    break

        if dep_entry:
            result[dep_id] = dep_entry.status
        else:
            result[dep_id] = "❓"  # Unknown

    return result
