# Changelog

All notable changes to Spectrena will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Lineage DB Check in `spectrena check`** - Now verifies lineage database schema version when present, showing migration status
- **Automatic Migration in `spectrena update`** - Database migrations now run automatically after file updates if lineage DB exists

## [1.3.2] - 2025-12-06

### Fixed

- Template download URLs now include version suffix in filenames (e.g., `spectrena-template-claude-sh-v1.3.2.zip`) to match actual GitHub release asset names

## [1.3.1] - 2025-12-06

### Added

- **Complete Update Command Implementation** - Full implementation of `spectrena update` command with GitHub API integration, automatic version detection, template downloading, and file categorization logic

### Changed

- Enhanced update command now supports `--version`, `--dry-run`, and `--force` flags for flexible update workflows
- Update command now auto-detects project agent and script type from `.spectrena/config.yml`

## [1.3.0] - 2025-12-06

### Added

- **Project Update System** - New `spectrena update` command for updating projects with smart file categorization (PRESERVE, UPDATE, MERGE, ADD)
- **Database Migration System** - Versioned schema migrations with automatic application on database connection
- **Database Management** - New `spectrena db` command with `status`, `migrate`, and `reset` subcommands for manual database control
- **Spec Completion Workflow** - New `/spectrena.spec.finish` slash command for verifying spec completion and creating pull/merge requests
- **Git Provider Configuration** - Support for GitHub and GitLab with configurable default branches, auto-delete options, and PR templates
- **Update Review Workflow** - New `/spectrena.review-updates` slash command for reviewing and merging pending project updates
- **Hash Tracking** - File hash tracking system (`.template-hashes.json`) to detect user modifications during updates

### Changed

- LineageDB now automatically applies pending migrations on connection
- Updated initialization wizard to include git provider configuration
- Enhanced `spectrena check` command to verify git CLI availability

## [1.0.1] - 2025-12-06

### Fixed

- SurrealDB RELATE statement record ID escaping using `_record_literal()` helper

## [1.0.0] - 2025-06-12

### Added

- **Spec Backlog Support** - New backlog workflow for managing spec ideas before formal specification
- **Constitution File Management** - Project constitution now lives at `.spectrena/memory/constitution.md`
- **Enhanced Implementation Templates** - Explicit task commit requirements in implement.md

### Fixed

- SurrealDB record ID escaping for special characters (SPECTRENA-PATCH-007)
- Constitution file path corrected to `.spectrena/memory/constitution.md`

### Changed

- Improved documentation for implementation workflow with explicit commit guidance

---

## [0.3.3] - 2025-06-XX

### Added

- MCP server entry point (`spectrena-mcp`)
- Enhanced lineage tracking

---

## [0.1.0] - 2024-XX-XX

### Added

- **Core CLI Commands**
  - `spectrena init` - Project initialization with wizard
  - `spectrena discover` - Discovery phase document generation
  - `spectrena new` - Create new specs with configurable IDs
  - `spectrena plan-init` - Initialize implementation plans
  - `spectrena doctor` - Check dependencies
  - `spectrena update-context` - Sync CLAUDE.md with plans
  - `spectrena config` - View and migrate configuration

- **Worktree Management (`sw`)**
  - `sw list` - List spec branches
  - `sw ready` - Show unblocked specs
  - `sw create` - Create worktree
  - `sw open` - Open in terminal
  - `sw merge` - Merge and cleanup
  - `sw status` - Show active worktrees

- **Dependency Management (`sw dep`)**
  - `sw dep add` - Add dependency
  - `sw dep rm` - Remove dependency
  - `sw dep check` - Validate graph
  - `sw dep show` - Visualize (ASCII/Mermaid)
  - `sw dep sync` - Sync file ↔ database
  - Mermaid format for deps.mermaid

- **Lineage Tracking**
  - SurrealDB embedded backend (SurrealKV)
  - SQLite fallback option
  - Spec → Plan → Task → Code tracking
  - MCP server for Claude integration

- **MCP Integration**
  - `spectrena-mcp` server
  - Phase/task management tools
  - Dependency analysis tools
  - Serena integration for code change tracking

- **Slash Commands**
  - `/spectrena.specify` - Create specs
  - `/spectrena.clarify` - Refine specs
  - `/spectrena.plan` - Generate plans
  - `/spectrena.tasks` - Break into tasks
  - `/spectrena.deps` - Analyze dependencies

- **Configuration**
  - Configurable spec ID patterns
  - Per-component numbering
  - Late-binding format changes
  - Migration support

### Changed

- Forked from spec-kit
- Replaced bash/PowerShell scripts with pure Python
- Changed from `dependencies.txt` to `deps.mermaid`

### Technical

- Python 3.11+ required
- Built with Typer, Rich, GitPython
- SurrealDB for lineage (optional)
- 100% cross-platform (no shell scripts)

---

## Comparison with spec-kit

| Feature | spec-kit | Spectrena |
|---------|----------|-----------|
| Spec IDs | Fixed `NNN-slug` | Configurable patterns |
| Components | Not supported | Built-in |
| Discovery | Not supported | Phase -2 |
| Dependencies | Not tracked | Mermaid + DB |
| Lineage | Not tracked | Full traceability |
| Scripts | Bash + PowerShell | Pure Python |
| Windows | Via PowerShell | Native |

[Unreleased]: https://github.com/rghsoftware/spectrena/compare/v1.3.2...HEAD
[1.3.2]: https://github.com/rghsoftware/spectrena/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/rghsoftware/spectrena/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/rghsoftware/spectrena/compare/v1.0.1...v1.3.0
[1.0.1]: https://github.com/rghsoftware/spectrena/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/rghsoftware/spectrena/releases/tag/v1.0.0
[0.3.3]: https://github.com/rghsoftware/spectrena/releases/tag/v0.3.3
[0.1.0]: https://github.com/rghsoftware/spectrena/releases/tag/v0.1.0
