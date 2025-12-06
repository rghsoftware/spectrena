"""Spectrena project update logic."""

from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import hashlib
import shutil
import json
import difflib
import tempfile
import zipfile
import io
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer

console = Console()

# GitHub repository for template downloads
GITHUB_REPO_OWNER = "rghsoftware"
GITHUB_REPO_NAME = "spectrena"


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


def get_latest_version() -> str:
    """Fetch latest release version from GitHub."""
    import urllib.request
    import ssl

    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

    try:
        # Create SSL context
        context = ssl.create_default_context()

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "spectrena-cli",
            }
        )

        with urllib.request.urlopen(request, timeout=30, context=context) as response:
            data = json.loads(response.read().decode())
            tag = data.get("tag_name", "")
            # Strip 'v' prefix if present
            return tag.lstrip("v") if tag else "latest"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            console.print("[yellow]Warning:[/yellow] No releases found, using 'latest' tag")
        else:
            console.print(f"[yellow]Warning:[/yellow] Could not fetch latest version: HTTP {e.code}")
        return "latest"
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not fetch latest version: {e}")
        return "latest"


def detect_agent_and_script(project_path: Path) -> tuple[str, str]:
    """Detect which AI agent and script type the project uses."""
    # Agent detection based on folder presence
    agent = "claude"  # default
    agent_folders = {
        ".claude": "claude",
        ".cursor": "cursor-agent",
        ".github": "copilot",
        ".gemini": "gemini",
        ".qwen": "qwen",
        ".opencode": "opencode",
        ".codex": "codex",
        ".windsurf": "windsurf",
        ".kilocode": "kilocode",
        ".augment": "auggie",
        ".codebuddy": "codebuddy",
        ".roo": "roo",
        ".amazonq": "q",
        ".agents": "amp",
        ".shai": "shai",
        ".bob": "bob",
    }

    for folder, agent_name in agent_folders.items():
        if (project_path / folder).exists():
            # Check if it has commands folder (indicates it's the primary agent)
            commands_path = project_path / folder / "commands"
            if commands_path.exists() or folder == ".github":
                agent = agent_name
                break

    # Script type detection
    script_type = "sh"  # default
    scripts_dir = project_path / ".spectrena" / "scripts"
    if scripts_dir.exists():
        if (scripts_dir / "powershell").exists():
            script_type = "ps"
        elif (scripts_dir / "bash").exists():
            script_type = "sh"

    return agent, script_type


def download_template(
    version: str,
    dest_path: Path,
    agent: str = "claude",
    script_type: str = "sh",
) -> None:
    """Download template files from GitHub release."""
    import urllib.request
    import ssl

    # Construct download URL
    # Filename format: spectrena-template-{agent}-{script_type}-v{version}.zip
    if version == "latest":
        base_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest/download"
        filename = f"spectrena-template-{agent}-{script_type}.zip"
    else:
        base_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/download/v{version}"
        filename = f"spectrena-template-{agent}-{script_type}-v{version}.zip"

    url = f"{base_url}/{filename}"

    console.print(f"  [dim]Downloading from {url}[/dim]")

    context = ssl.create_default_context()

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "spectrena-cli"}
        )

        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            total_size = int(response.headers.get("content-length", 0))
            zip_data = io.BytesIO()

            if total_size > 0:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Downloading...", total=total_size)
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        zip_data.write(chunk)
                        progress.update(task, advance=len(chunk))
            else:
                zip_data.write(response.read())

        # Extract to destination
        dest_path.mkdir(parents=True, exist_ok=True)
        zip_data.seek(0)

        with zipfile.ZipFile(zip_data, 'r') as zf:
            # Extract all files, stripping top-level directory if present
            namelist = zf.namelist()

            # Detect if there's a single top-level directory
            top_dirs = set()
            for name in namelist:
                parts = name.split('/')
                if len(parts) > 1:
                    top_dirs.add(parts[0])

            strip_prefix = ""
            if len(top_dirs) == 1:
                strip_prefix = list(top_dirs)[0] + "/"

            for member in namelist:
                # Skip directories
                if member.endswith('/'):
                    continue

                # Strip leading directory if needed
                if strip_prefix and member.startswith(strip_prefix):
                    relative_path = member[len(strip_prefix):]
                else:
                    relative_path = member

                if not relative_path:
                    continue

                # Extract file
                target = dest_path / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(member) as src, open(target, 'wb') as dst:
                    dst.write(src.read())

        console.print(f"  [green]✓[/green] Downloaded template")

    except urllib.error.HTTPError as e:
        if e.code == 404:
            console.print(f"[red]Error:[/red] Version {version} not found for {agent}-{script_type}")
            console.print(f"Check available versions: https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases")
        else:
            console.print(f"[red]Error:[/red] Download failed: HTTP {e.code}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Download failed: {e}")
        raise typer.Exit(1)


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
        f"[bold]Spectrena Update[/bold]\n"
        f"Current version: {current_version}",
        title="Update",
        border_style="cyan"
    ))

    # Detect agent and script type from existing project
    agent, script_type = detect_agent_and_script(project_path)
    console.print(f"[dim]Detected: {agent} + {script_type}[/dim]")

    # Resolve target version
    if version:
        target_version = version
    else:
        console.print("[cyan]Fetching latest version...[/cyan]")
        target_version = get_latest_version()

    if target_version == current_version and not force:
        console.print(f"[green]✓[/green] Already at version {current_version}")
        return

    console.print(f"Target version: {target_version}")

    # Download new template to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        new_template_path = Path(temp_dir) / "template"

        console.print(f"\n[cyan]Downloading template...[/cyan]")
        download_template(target_version, new_template_path, agent, script_type)

        # Create update plan
        console.print(f"[cyan]Analyzing changes...[/cyan]")
        plan = create_update_plan(
            project_path,
            new_template_path,
            current_version,
            target_version,
        )

        # Show plan
        display_update_plan(plan)

        if dry_run:
            console.print("\n[yellow]Dry run - no changes made[/yellow]")
            return

        if plan.update_count == 0 and plan.add_count == 0 and plan.merge_count == 0:
            console.print("\n[green]✓[/green] No updates needed")
            save_version(project_path, target_version)
            return

        if not force:
            console.print("")
            if not typer.confirm("Apply updates?"):
                console.print("[yellow]Cancelled[/yellow]")
                return

        # Apply updates
        console.print(f"\n[cyan]Applying updates...[/cyan]")
        apply_update_plan(plan, project_path, new_template_path)

        # Save new version
        save_version(project_path, target_version)

    # Check and run database migrations if lineage is enabled
    lineage_db_path = project_path / ".spectrena" / "lineage.db"
    if lineage_db_path.exists():
        console.print("\n[cyan]Checking database schema...[/cyan]")
        try:
            import asyncio
            from spectrena.lineage.db import LineageDB

            async def run_migrations():
                db = LineageDB(lineage_db_path)
                async with db.connect(run_migrations=True) as _:
                    pass  # Migrations run automatically on connect

            asyncio.run(run_migrations())
            console.print("[green]✓[/green] Database schema up to date")
        except ImportError:
            console.print("[dim]Lineage DB found but surrealdb not installed - skipping migration[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Database migration check failed: {e}")
            console.print("[dim]Run 'spectrena db migrate' manually if needed[/dim]")

    console.print(f"\n[green]✓ Updated to version {target_version}[/green]")

    if plan.merge_count > 0:
        console.print(f"\n[yellow]Note:[/yellow] {plan.merge_count} files need manual review")
        console.print("Run [cyan]/spectrena.review-updates[/cyan] to merge changes")
