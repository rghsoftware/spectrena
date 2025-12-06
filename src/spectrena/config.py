#!/usr/bin/env python3
"""
Spectrena Configuration System

Created: 2025-11-28
Author: Robert Hamilton
"""


from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class SpecIdConfig:
    template: str = "{NNN}-{slug}"
    padding: int = 3
    project: Optional[str] = None
    components: list[str] = field(default_factory=list)
    numbering_source: str = "directory"

    @property
    def requires_component(self) -> bool:
        return "{component}" in self.template

    @property
    def requires_project(self) -> bool:
        return "{project}" in self.template

    def build_branch_pattern(self) -> str:
        pattern = "^"
        if self.requires_project:
            pattern += (
                f"{re.escape(self.project)}-" if self.project else r"[A-Z][A-Z0-9_]*-"
            )
        if self.requires_component:
            pattern += r"[A-Z][A-Z0-9_]*-"
        pattern += r"[0-9]{" + str(self.padding) + r"}-"
        return pattern

    def generate_spec_id(
        self, number: int, slug: str, component: Optional[str] = None
    ) -> str:
        padded = str(number).zfill(self.padding)
        result = self.template
        result = result.replace("{NNN}", padded).replace("{slug}", slug)

        if self.project:
            result = result.replace("{project}", self.project)
        else:
            result = result.replace("{project}-", "").replace("{project}", "")

        if component:
            result = result.replace("{component}", component)
        else:
            result = result.replace("{component}-", "").replace("{component}", "")

        return re.sub(r"-+", "-", result).strip("-")

    def validate_component(self, component: str) -> bool:
        if not self.components:
            return True
        return component.upper() in [c.upper() for c in self.components]


@dataclass
class LineageConfig:
    """Lineage tracking configuration."""

    enabled: bool = False
    lineage_db: str = "surrealkv://.spectrena/lineage"
    auto_register: bool = True


@dataclass
class BacklogConfig:
    """Spec backlog configuration."""

    enabled: bool = False
    path: str = ".spectrena/backlog.md"
    reference_docs: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    require_component_flag: bool = True
    validate_components: bool = True
    max_clarifications: int = 3


@dataclass
class GitConfig:
    """Git provider configuration."""

    provider: str = "github"  # github, gitlab, other
    default_branch: str = "main"
    auto_delete_branch: bool = True
    pr_template: Optional[str] = None

    def __post_init__(self):
        valid_providers = ("github", "gitlab", "other")
        if self.provider not in valid_providers:
            raise ValueError(
                f"Invalid git provider: {self.provider}. Must be one of {valid_providers}"
            )


@dataclass
class Config:
    """Project configuration."""

    spec_id: SpecIdConfig = field(default_factory=SpecIdConfig)
    lineage: LineageConfig = field(default_factory=LineageConfig)
    backlog: BacklogConfig = field(default_factory=BacklogConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    git: GitConfig = field(default_factory=GitConfig)

    @classmethod
    def load(cls, project_dir: Optional[Path] = None) -> "Config":
        if project_dir is None:
            project_dir = Path.cwd()
        config_path = project_dir / ".spectrena" / "config.yml"
        if not config_path.exists():
            return cls()
        return cls._parse_yaml(config_path)

    @classmethod
    def _parse_yaml(cls, path: Path) -> "Config":
        content = path.read_text()
        config = cls()

        config.spec_id.template = (
            _yaml_get(content, "spec_id", "template") or config.spec_id.template
        )
        padding = _yaml_get(content, "spec_id", "padding")
        if padding:
            config.spec_id.padding = int(padding)
        config.spec_id.project = _yaml_get(content, "spec_id", "project")
        config.spec_id.numbering_source = (
            _yaml_get(content, "spec_id", "numbering_source")
            or config.spec_id.numbering_source
        )
        config.spec_id.components = (
            _yaml_get_array(content, "spec_id", "components") or []
        )

        # Parse lineage section
        enabled = _yaml_get(content, "lineage", "enabled")
        if enabled:
            config.lineage.enabled = enabled.lower() == "true"
        if config.lineage.enabled:
            db_url = _yaml_get(content, "lineage", "lineage_db")
            if db_url:
                config.lineage.lineage_db = db_url
            auto_reg = _yaml_get(content, "lineage", "auto_register")
            if auto_reg:
                config.lineage.auto_register = auto_reg.lower() == "true"

        # Parse backlog section
        backlog_enabled = _yaml_get(content, "backlog", "enabled")
        if backlog_enabled:
            config.backlog.enabled = backlog_enabled.lower() == "true"
        if config.backlog.enabled:
            backlog_path = _yaml_get(content, "backlog", "path")
            if backlog_path:
                config.backlog.path = backlog_path
            # Parse reference_docs dictionary
            config.backlog.reference_docs = _yaml_get_dict(content, "backlog", "reference_docs")

        # Parse git section
        git_provider = _yaml_get(content, "git", "provider")
        if git_provider:
            config.git.provider = git_provider
        git_default_branch = _yaml_get(content, "git", "default_branch")
        if git_default_branch:
            config.git.default_branch = git_default_branch
        git_auto_delete = _yaml_get(content, "git", "auto_delete_branch")
        if git_auto_delete:
            config.git.auto_delete_branch = git_auto_delete.lower() == "true"
        git_pr_template = _yaml_get(content, "git", "pr_template")
        if git_pr_template:
            config.git.pr_template = git_pr_template

        return config

    def save(self, project_dir: Optional[Path] = None):
        if project_dir is None:
            project_dir = Path.cwd()
        config_dir = project_dir / ".spectrena"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yml").write_text(self._generate_yaml())

    def _generate_yaml(self) -> str:
        lines = [
            "# Spectrena Configuration",
            "",
            "spec_id:",
            f'  template: "{self.spec_id.template}"',
            f"  padding: {self.spec_id.padding}",
        ]
        if self.spec_id.project:
            lines.append(f'  project: "{self.spec_id.project}"')
        if self.spec_id.components:
            lines.append("  components:")
            for c in self.spec_id.components:
                lines.append(f"    - {c}")
        lines.append(f'  numbering_source: "{self.spec_id.numbering_source}"')

        # Add lineage section
        lines.extend(
            [
                "",
                "lineage:",
                f"  enabled: {str(self.lineage.enabled).lower()}",
            ]
        )

        if self.lineage.enabled:
            lines.extend(
                [
                    f'  lineage_db: "{self.lineage.lineage_db}"',
                    f"  auto_register: {str(self.lineage.auto_register).lower()}",
                ]
            )

        # Add backlog section
        lines.extend(
            [
                "",
                "backlog:",
                f"  enabled: {str(self.backlog.enabled).lower()}",
            ]
        )

        if self.backlog.enabled:
            lines.append(f'  path: "{self.backlog.path}"')
            if self.backlog.reference_docs:
                lines.append("  reference_docs:")
                for abbrev, path in self.backlog.reference_docs.items():
                    lines.append(f'    {abbrev}: "{path}"')

        # Add git section
        lines.extend(
            [
                "",
                "git:",
                f'  provider: "{self.git.provider}"',
                f'  default_branch: "{self.git.default_branch}"',
                f"  auto_delete_branch: {str(self.git.auto_delete_branch).lower()}",
            ]
        )

        if self.git.pr_template:
            lines.append(f'  pr_template: "{self.git.pr_template}"')

        return "\n".join(lines) + "\n"


def _yaml_get(content: str, parent: str, child: str) -> Optional[str]:
    in_section = False
    for line in content.split("\n"):
        if re.match(rf"^{parent}:\s*$", line):
            in_section = True
            continue
        if in_section and line and not line[0].isspace():
            in_section = False
        if in_section:
            match = re.match(rf"^\s+{child}:\s*(.+)$", line)
            if match:
                return match.group(1).strip().strip('"').strip("'")
    return None


def _yaml_get_array(content: str, parent: str, key: str) -> list[str]:
    result, in_section, in_array = [], False, False
    for line in content.split("\n"):
        if re.match(rf"^{parent}:\s*$", line):
            in_section = True
            continue
        if in_section and line and not line[0].isspace():
            in_section = in_array = False
        if in_section:
            if re.match(rf"^\s+{key}:\s*$", line):
                in_array = True
                continue
            if in_array and re.match(r"^\s+[a-z_]+:", line):
                in_array = False
            if in_array:
                match = re.match(r"^\s+-\s*(.+)$", line)
                if match:
                    result.append(match.group(1).strip().strip('"').strip("'"))
    return result


def _yaml_get_dict(content: str, parent: str, key: str) -> dict[str, str]:
    """Parse a dictionary from YAML content."""
    result, in_section, in_dict = {}, False, False
    for line in content.split("\n"):
        if re.match(rf"^{parent}:\s*$", line):
            in_section = True
            continue
        if in_section and line and not line[0].isspace():
            in_section = in_dict = False
        if in_section:
            if re.match(rf"^\s+{key}:\s*$", line):
                in_dict = True
                continue
            if in_dict and re.match(r"^\s+[a-z_]+:", line):
                in_dict = False
            if in_dict:
                # Match key: value pairs with proper indentation (4 spaces for nested dict)
                match = re.match(r"^\s{4}([A-Z_]+):\s*(.+)$", line)
                if match:
                    dict_key = match.group(1).strip()
                    dict_val = match.group(2).strip().strip('"').strip("'")
                    result[dict_key] = dict_val
    return result


def _check_lineage_available() -> bool:
    """Check if lineage optional dependencies are installed."""
    try:
        import surrealdb  # noqa: F401
        import fastmcp  # noqa: F401

        return True
    except ImportError:
        return False


def run_config_wizard(project_dir: Optional[Path] = None) -> Config:
    """Interactive configuration wizard."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    import readchar

    console = Console()
    config = Config()

    FORMAT_OPTIONS = [
        ("simple", "{NNN}-{slug}", "001-feature-name", "Basic numbering - good for small projects"),
        ("component", "{component}-{NNN}-{slug}", "CORE-001-feature-name", "Organize by component (e.g., API, UI, DB)"),
        ("project", "{project}-{NNN}-{slug}", "MYAPP-001-feature-name", "Add project prefix for multi-project repos"),
        ("full", "{project}-{component}-{NNN}-{slug}", "MYAPP-CORE-001-feature", "Both project and component organization"),
    ]

    def select_menu(options, title):
        selected = 0
        while True:
            console.clear()
            table = Table.grid(padding=(0, 2))
            table.add_column(width=3)
            table.add_column(width=12)
            table.add_column(style="dim", width=30)
            table.add_column(style="dim")
            for i, (name, _, example, description) in enumerate(options):
                prefix = "▶" if i == selected else " "
                style = "bold cyan" if i == selected else ""
                formatted_name = f"[{style}]{name}[/]" if style else name
                table.add_row(prefix, formatted_name, description, f"→ {example}")
            console.print(Panel(table, title=title, border_style="cyan"))
            console.print("\n[dim]↑/↓ navigate • Enter select[/]")

            key = readchar.readkey()
            if key in (readchar.key.UP, "\x10"):
                selected = (selected - 1) % len(options)
            elif key in (readchar.key.DOWN, "\x0e"):
                selected = (selected + 1) % len(options)
            elif key in (readchar.key.ENTER, "\r"):
                return selected
            elif key in (readchar.key.ESCAPE, "\x1b"):
                return -1

    # Show intro message before format selection
    console.clear()
    intro_panel = Panel(
        "[cyan]Spectrena Configuration Wizard[/cyan]\n\n"
        "This wizard will help you configure how spec IDs are generated.\n"
        "Spec IDs are used to uniquely identify features and track them through\n"
        "the development lifecycle.\n\n"
        "[dim]Press Enter to continue...[/]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(intro_panel)
    _ = console.input("")  # Wait for Enter

    choice = select_menu(FORMAT_OPTIONS, "Spec ID Format")
    if choice == -1:
        return config

    config.spec_id.template = FORMAT_OPTIONS[choice][1]

    if "{component}" in config.spec_id.template:
        console.clear()
        components_panel = Panel(
            "[cyan]Component Configuration[/cyan]\n\n"
            "[bold]What is a component?[/]\n"
            "A component is a logical part of your application that groups related features.\n"
            "Think of it as a module, layer, or functional area of your system.\n\n"
            "[bold]Common approaches:[/]\n"
            "  • By architecture layer: CORE, API, UI, DB\n"
            "  • By feature domain: AUTH, BILLING, REPORTING, NOTIFICATIONS\n"
            "  • By service: FRONTEND, BACKEND, INFRA, MOBILE\n\n"
            "[bold]Note:[/] Components can be discovered during project exploration or added later\n"
            "[dim]Press Enter to define components later (via discover or .spectrena/config.yml)[/]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(components_panel)
        console.print()
        comp_input = console.input("[bold]Components (comma-separated):[/] ")
        if comp_input.strip():
            config.spec_id.components = [
                c.strip().upper() for c in comp_input.split(",")
            ]

    if "{project}" in config.spec_id.template:
        console.clear()
        project_panel = Panel(
            "[cyan]Project Prefix Configuration[/cyan]\n\n"
            "[bold]What is a project prefix?[/]\n"
            "A short identifier that represents your entire project or application.\n"
            "Useful in monorepos or when managing multiple related projects.\n\n"
            "[bold]When to use:[/]\n"
            "  • Monorepo with multiple apps (e.g., WEBUI, MOBILEAPP, ADMINPANEL)\n"
            "  • Multiple microservices in one repo (e.g., USERS, PAYMENTS, CATALOG)\n"
            "  • Organization prefix for open source (e.g., ACME, MYORG)\n\n"
            "[bold]Examples:[/] MYAPP, WEBUI, ACME\n"
            "[dim]Press Enter without typing to skip[/]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(project_panel)
        console.print()
        project = console.input("[bold]Project prefix:[/] ")
        if project.strip():
            config.spec_id.project = project.strip().upper()

    # === LINEAGE CONFIGURATION ===
    console.clear()
    console.print(
        Panel(
            "[cyan]Lineage Tracking[/cyan]\n\n"
            "[bold]What is lineage tracking?[/]\n"
            "Track specs → tasks → code changes for impact analysis.\n"
            "See which specs depend on each other and get velocity metrics.\n\n"
            "[bold]Features:[/]\n"
            "  • Dependency graph between specs\n"
            "  • Task progress tracking\n"
            "  • Code change attribution\n"
            "  • Impact analysis (what breaks if X slips?)\n",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    lineage_available = _check_lineage_available()

    if lineage_available:
        import typer

        enable_lineage = typer.confirm("Enable lineage tracking?", default=False)

        if enable_lineage:
            config.lineage.enabled = True
            config.lineage.lineage_db = "surrealkv://.spectrena/lineage"
            console.print("[green]✓ Lineage enabled[/green]")
        else:
            config.lineage.enabled = False
            console.print("[dim]Lineage tracking disabled[/dim]")
    else:
        console.print("[yellow]Lineage dependencies not installed[/yellow]")
        console.print("[dim]Install with: pip install spectrena[lineage-surreal][/dim]")
        config.lineage.enabled = False

    # === BACKLOG CONFIGURATION ===
    console.clear()
    console.print(
        Panel(
            "[cyan]Spec Backlog[/cyan]\n\n"
            "[bold]What is a spec backlog?[/]\n"
            "Pre-define specs with scope, dependencies, and references.\n"
            "Pull context automatically when starting a spec.\n\n"
            "[bold]Benefits:[/]\n"
            "  • Ordered implementation plan\n"
            "  • Dependency tracking between specs\n"
            "  • Reference docs linked to specs\n"
            "  • Complexity weighting (LIGHTWEIGHT/STANDARD/FORMAL)\n",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    import typer

    enable_backlog = typer.confirm("Enable spec backlog?", default=False)

    if enable_backlog:
        config.backlog.enabled = True

        # Ask for backlog location
        console.print("\n[dim]Where should the backlog file be located?[/dim]")
        backlog_choices = {
            "1": (".spectrena/backlog.md", ".spectrena/backlog.md (default)"),
            "2": ("docs/spec-backlog.md", "docs/spec-backlog.md"),
            "3": ("custom", "Custom path"),
        }

        console.print("  [cyan]1[/cyan] .spectrena/backlog.md (default)")
        console.print("  [cyan]2[/cyan] docs/spec-backlog.md")
        console.print("  [cyan]3[/cyan] Custom path")

        choice = console.input("\n[bold]Choice (1-3):[/] ").strip() or "1"

        if choice in backlog_choices:
            backlog_path = backlog_choices[choice][0]
            if backlog_path == "custom":
                backlog_path = console.input("[bold]Enter backlog path:[/] ").strip()
        else:
            backlog_path = ".spectrena/backlog.md"

        config.backlog.path = backlog_path

        # Create backlog from template if doesn't exist
        if project_dir:
            import shutil

            backlog_file = project_dir / backlog_path
            if not backlog_file.exists():
                # Look for template in templates directory
                template_path = project_dir / "templates" / "backlog-template.md"
                if not template_path.exists():
                    # Also check .spectrena/templates
                    template_path = project_dir / ".spectrena" / "templates" / "backlog-template.md"

                if template_path.exists():
                    backlog_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(template_path, backlog_file)
                    console.print(f"[green]✓ Created {backlog_path}[/green]")

        # Ask about reference docs
        console.print("\n[dim]Reference doc abbreviations (optional):[/dim]")
        console.print("[dim]Format: ABBREV=path (e.g., REQ=docs/requirements.md)[/dim]")
        console.print("[dim]Press Enter without typing to finish[/dim]\n")

        while True:
            ref = console.input("[bold]Add reference (or Enter to finish):[/] ").strip()
            if not ref:
                break
            if "=" in ref:
                abbrev, path = ref.split("=", 1)
                config.backlog.reference_docs[abbrev.strip().upper()] = path.strip()
                console.print(f"[green]✓ Added {abbrev.strip().upper()}[/green]")
            else:
                console.print("[yellow]Invalid format. Use: ABBREV=path[/yellow]")

        console.print("[green]✓ Backlog enabled[/green]")
    else:
        config.backlog.enabled = False
        console.print("[dim]Backlog disabled[/dim]")

    # === GIT PROVIDER CONFIGURATION ===
    console.clear()
    console.print(
        Panel(
            "[cyan]Git Provider Configuration[/cyan]\n\n"
            "[bold]What is this?[/]\n"
            "Configure how spec branches create pull/merge requests.\n"
            "This is used by the /spectrena.spec.finish command.\n\n"
            "[bold]Providers:[/]\n"
            "  • GitHub - uses gh CLI\n"
            "  • GitLab - uses glab CLI\n"
            "  • Other - manual PR/MR creation\n",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    import shutil

    provider_choices = {
        "github": "GitHub (uses gh CLI)",
        "gitlab": "GitLab (uses glab CLI)",
        "other": "Other / Manual",
    }

    # Simple selection without arrow keys - just use the existing menu infrastructure
    console.print("\n[bold]Git provider:[/bold]")
    console.print("  [cyan]1[/cyan] GitHub (uses gh CLI)")
    console.print("  [cyan]2[/cyan] GitLab (uses glab CLI)")
    console.print("  [cyan]3[/cyan] Other / Manual")

    choice = console.input("\n[bold]Choice (1-3):[/] ").strip() or "1"

    provider_map = {"1": "github", "2": "gitlab", "3": "other"}
    provider = provider_map.get(choice, "github")
    config.git.provider = provider

    # Check CLI availability
    if provider == "github":
        if not shutil.which("gh"):
            console.print(
                "[yellow]⚠ gh CLI not found. Install: https://cli.github.com/[/yellow]"
            )
            console.print(
                "[dim]You can still use spectrena, but PR creation will be manual.[/dim]"
            )
    elif provider == "gitlab":
        if not shutil.which("glab"):
            console.print(
                "[yellow]⚠ glab CLI not found. Install: https://gitlab.com/gitlab-org/cli[/yellow]"
            )
            console.print(
                "[dim]You can still use spectrena, but MR creation will be manual.[/dim]"
            )

    # Default branch
    default_branch = typer.prompt("Default branch name", default="main")
    config.git.default_branch = default_branch

    # Auto-delete branch (only for github/gitlab)
    if provider in ("github", "gitlab"):
        auto_delete = typer.confirm(
            "Auto-delete spec branch after merge?", default=True
        )
        config.git.auto_delete_branch = auto_delete

    # Custom PR template (optional)
    if typer.confirm("Use custom PR/MR template?", default=False):
        template_path = typer.prompt(
            "Template path", default=".github/PULL_REQUEST_TEMPLATE.md"
        )
        if project_dir and (project_dir / template_path).exists():
            config.git.pr_template = template_path
        else:
            console.print(
                f"[yellow]Template not found at {template_path}, skipping[/yellow]"
            )

    config.save(project_dir)
    console.print("\n[green]✓ Configuration saved[/]")

    # Create .spectrena/.gitignore if needed
    if project_dir and (config.lineage.enabled or config.backlog.enabled):
        gitignore_path = project_dir / ".spectrena" / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = "# Lineage database (generated)\nlineage/\n"
            gitignore_path.write_text(gitignore_content)
            console.print("[green]✓ Created .spectrena/.gitignore[/]")

    return config
