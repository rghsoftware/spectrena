"""Spectrena project update logic."""

from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import hashlib
import shutil
import json
import difflib
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import typer

console = Console()


class UpdateAction(Enum):
    """Action to take for a file during update."""
    PRESERVE = "preserve"   # Don't touch
    UPDATE = "update"       # Overwrite
    MERGE = "merge"         # Needs review
    ADD = "add"             # New file
    DEPRECATED = "deprecated"  # Should remove


# File categorization rules
PRESERVE_PATTERNS = [
    ".spectrena/memory/*",
    ".spectrena/config.yml",
    ".spectrena/backlog.md",
    ".spectrena/lineage.db/*",
    ".spectrena/discovery.md",
    "specs/*",
]

UPDATE_PATTERNS = [
    ".spectrena/scripts/**",
    ".claude/commands/*",
    ".cursor/commands/*",
    ".github/copilot-instructions.md",
    ".windsurf/commands/*",
    ".cline/commands/*",
    ".roo-cline/commands/*",
]

MERGE_PATTERNS = [
    ".spectrena/templates/*",
]


@dataclass
class FileUpdate:
    """Represents a single file update."""
    path: str
    action: UpdateAction
    reason: str
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    diff: Optional[str] = None


@dataclass
class UpdatePlan:
    """Complete update plan."""
    from_version: str
    to_version: str
    files: list[FileUpdate] = field(default_factory=list)

    @property
    def preserve_count(self) -> int:
        return sum(1 for f in self.files if f.action == UpdateAction.PRESERVE)

    @property
    def update_count(self) -> int:
        return sum(1 for f in self.files if f.action == UpdateAction.UPDATE)

    @property
    def merge_count(self) -> int:
        return sum(1 for f in self.files if f.action == UpdateAction.MERGE)

    @property
    def add_count(self) -> int:
        return sum(1 for f in self.files if f.action == UpdateAction.ADD)


def file_hash(path: Path) -> Optional[str]:
    """Get SHA256 hash of file contents."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def matches_pattern(path: str, patterns: list[str]) -> bool:
    """Check if path matches any glob pattern."""
    from fnmatch import fnmatch
    return any(fnmatch(path, p) for p in patterns)


def categorize_file(rel_path: str, exists: bool, modified: bool) -> tuple[UpdateAction, str]:
    """Determine action for a file."""

    if matches_pattern(rel_path, PRESERVE_PATTERNS):
        return UpdateAction.PRESERVE, "User content - never modified"

    if matches_pattern(rel_path, UPDATE_PATTERNS):
        if exists:
            return UpdateAction.UPDATE, "Framework file - will be updated"
        else:
            return UpdateAction.ADD, "New framework file"

    if matches_pattern(rel_path, MERGE_PATTERNS):
        if not exists:
            return UpdateAction.ADD, "New template"
        if modified:
            return UpdateAction.MERGE, "Template modified - needs review"
        else:
            return UpdateAction.UPDATE, "Template unchanged - safe to update"

    # Default: add new, preserve existing
    if exists:
        return UpdateAction.PRESERVE, "Unknown file - preserving"
    return UpdateAction.ADD, "New file"


def load_original_hashes(project_path: Path) -> dict[str, str]:
    """Load original template hashes from last update."""
    hash_file = project_path / ".spectrena" / ".template-hashes.json"
    if hash_file.exists():
        return json.loads(hash_file.read_text())
    return {}


def save_original_hashes(
    project_path: Path,
    plan: UpdatePlan,
    new_template_path: Path,
) -> None:
    """Save template hashes for detecting future modifications."""
    hashes = {}
    for file_update in plan.files:
        if file_update.action in (UpdateAction.UPDATE, UpdateAction.ADD):
            hashes[file_update.path] = file_update.new_hash

    hash_file = project_path / ".spectrena" / ".template-hashes.json"
    hash_file.write_text(json.dumps(hashes, indent=2))


def generate_diff(old_file: Path, new_file: Path) -> str:
    """Generate unified diff between files."""
    old_lines = old_file.read_text().splitlines(keepends=True)
    new_lines = new_file.read_text().splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"current/{old_file.name}",
        tofile=f"updated/{new_file.name}",
    )

    return "".join(diff)


def create_update_plan(
    project_path: Path,
    new_template_path: Path,
    current_version: str,
    new_version: str,
) -> UpdatePlan:
    """Create plan for updating project."""

    plan = UpdatePlan(from_version=current_version, to_version=new_version)

    # Track original template hashes for detecting modifications
    original_hashes = load_original_hashes(project_path)

    # Scan new template files
    for new_file in new_template_path.rglob("*"):
        if new_file.is_dir():
            continue

        rel_path = str(new_file.relative_to(new_template_path))
        existing_file = project_path / rel_path

        exists = existing_file.exists()
        old_hash = file_hash(existing_file)
        new_hash = file_hash(new_file)

        # Check if user modified the file from original
        original_hash = original_hashes.get(rel_path)
        modified = exists and old_hash != original_hash

        action, reason = categorize_file(rel_path, exists, modified)

        update = FileUpdate(
            path=rel_path,
            action=action,
            reason=reason,
            old_hash=old_hash,
            new_hash=new_hash,
        )

        # Generate diff for merge candidates
        if action == UpdateAction.MERGE and exists:
            update.diff = generate_diff(existing_file, new_file)

        plan.files.append(update)

    return plan


def display_update_plan(plan: UpdatePlan) -> None:
    """Display update plan as a table."""
    table = Table(title=f"Update Plan: {plan.from_version} → {plan.to_version}")

    table.add_column("Action", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Preserve", str(plan.preserve_count), style="dim")
    table.add_row("Update", str(plan.update_count), style="green")
    table.add_row("Add", str(plan.add_count), style="cyan")
    table.add_row("Merge (review needed)", str(plan.merge_count), style="yellow")

    console.print(table)
    console.print()

    # Show files that need review
    if plan.merge_count > 0:
        console.print("[yellow]Files requiring review:[/yellow]")
        for f in plan.files:
            if f.action == UpdateAction.MERGE:
                console.print(f"  • {f.path}")
        console.print()


def write_pending_updates(
    project_path: Path,
    pending: list[FileUpdate],
    new_template_path: Path,
) -> None:
    """Write pending updates for Claude review."""

    output = project_path / ".spectrena" / "pending-updates.md"

    lines = [
        "# Pending Template Updates",
        "",
        "These files have been modified from the original template.",
        "Use `/spectrena.review-updates` to review and merge changes.",
        "",
        "---",
        "",
    ]

    for update in pending:
        lines.extend([
            f"## {update.path}",
            "",
            f"**Your version hash:** `{update.old_hash}`",
            f"**New version hash:** `{update.new_hash}`",
            "",
            "### Diff",
            "",
            "```diff",
            update.diff or "(diff not available)",
            "```",
            "",
            "### New Version Content",
            "",
            "```markdown",
            (new_template_path / update.path).read_text(),
            "```",
            "",
            "---",
            "",
        ])

    output.write_text("\n".join(lines))
    console.print(f"\n[yellow]Review needed:[/yellow] {len(pending)} files")
    console.print(f"Run [cyan]/spectrena.review-updates[/cyan] to merge changes")


def apply_update_plan(plan: UpdatePlan, project_path: Path, new_template_path: Path) -> None:
    """Apply the update plan."""

    pending_merges = []

    for file_update in plan.files:
        src = new_template_path / file_update.path
        dst = project_path / file_update.path

        if file_update.action == UpdateAction.PRESERVE:
            console.print(f"  [dim]SKIP[/dim] {file_update.path}")

        elif file_update.action == UpdateAction.UPDATE:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            console.print(f"  [green]UPDATE[/green] {file_update.path}")

        elif file_update.action == UpdateAction.ADD:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            console.print(f"  [cyan]ADD[/cyan] {file_update.path}")

        elif file_update.action == UpdateAction.MERGE:
            pending_merges.append(file_update)
            console.print(f"  [yellow]REVIEW[/yellow] {file_update.path}")

    # Write pending merges for Claude review
    if pending_merges:
        write_pending_updates(project_path, pending_merges, new_template_path)

    # Save new hashes for future updates
    save_original_hashes(project_path, plan, new_template_path)


def get_current_version(project_path: Path) -> str:
    """Get current spectrena version from project."""
    version_file = project_path / ".spectrena" / ".version"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"


def save_version(project_path: Path, version: str) -> None:
    """Save spectrena version to project."""
    version_file = project_path / ".spectrena" / ".version"
    version_file.write_text(version)


def run_update(
    version: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """Main update entry point."""

    project_path = Path.cwd()
    spectrena_dir = project_path / ".spectrena"

    if not spectrena_dir.exists():
        console.print("[red]Error:[/red] Not a spectrena project (no .spectrena/ directory)")
        raise typer.Exit(1)

    # Get current version
    current_version = get_current_version(project_path)

    console.print(Panel(
        f"[cyan]Spectrena Update[/cyan]\n"
        f"Current version: {current_version}",
        title="Update",
        border_style="cyan"
    ))

    # For now, this is a placeholder implementation
    # In a real implementation, we would:
    # 1. Download new template from GitHub release
    # 2. Create update plan
    # 3. Apply updates

    new_version = version or "latest"
    console.print(f"\n[yellow]Note:[/yellow] Full update implementation requires:")
    console.print("  1. Template download from GitHub releases")
    console.print("  2. Integration with existing init download logic")
    console.print("  3. Version resolution (latest vs specific)")
    console.print()
    console.print("[dim]This is a framework implementation.[/dim]")

    # Example of what the full implementation would look like:
    # new_template_path = download_template(version)
    # plan = create_update_plan(project_path, new_template_path, current_version, new_version)
    # display_update_plan(plan)
    #
    # if dry_run:
    #     console.print("\n[yellow]Dry run - no changes made[/yellow]")
    #     return
    #
    # if not force:
    #     if not typer.confirm("Apply updates?"):
    #         console.print("[yellow]Cancelled[/yellow]")
    #         return
    #
    # apply_update_plan(plan, project_path, new_template_path)
    # save_version(project_path, new_version)
    # console.print("\n[green]Update complete![/green]")
