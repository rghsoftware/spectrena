"""Database schema migrations for spectrena lineage tracking."""

from typing import Callable
from rich.console import Console

console = Console()


class SchemaVersionError(Exception):
    """Database schema version mismatch."""
    pass


# Migration functions: version -> SQL or async function
MIGRATIONS: dict[int, str | Callable] = {
    1: """
        -- Initial schema
        DEFINE TABLE schema_meta SCHEMAFULL;
        DEFINE FIELD version ON schema_meta TYPE int;
        CREATE schema_meta:current SET version = 1;

        DEFINE TABLE spec SCHEMAFULL;
        DEFINE FIELD status ON spec TYPE string DEFAULT 'draft';
        DEFINE FIELD created_at ON spec TYPE datetime DEFAULT time::now();
        DEFINE FIELD metadata ON spec TYPE object DEFAULT {};

        DEFINE TABLE phase SCHEMAFULL;
        DEFINE FIELD spec ON phase TYPE record<spec>;
        DEFINE FIELD number ON phase TYPE int;
        DEFINE FIELD title ON phase TYPE string;
        DEFINE FIELD status ON phase TYPE string DEFAULT 'pending';
        DEFINE FIELD created_at ON phase TYPE datetime DEFAULT time::now();

        DEFINE TABLE task SCHEMAFULL;
        DEFINE FIELD spec ON task TYPE record<spec>;
        DEFINE FIELD phase ON task TYPE record<phase>;
        DEFINE FIELD status ON task TYPE string DEFAULT 'pending';
        DEFINE FIELD title ON task TYPE string;
        DEFINE FIELD created_at ON task TYPE datetime DEFAULT time::now();
        DEFINE FIELD completed_at ON task TYPE datetime;

        DEFINE TABLE commit SCHEMAFULL;
        DEFINE FIELD task ON commit TYPE record<task>;
        DEFINE FIELD sha ON commit TYPE string;
        DEFINE FIELD message ON commit TYPE string;
        DEFINE FIELD created_at ON commit TYPE datetime DEFAULT time::now();

        -- Relationships
        DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION FROM task TO spec;
        DEFINE TABLE committed_for SCHEMAFULL TYPE RELATION FROM commit TO task;

        -- Current task tracking
        DEFINE TABLE phase_state SCHEMAFULL;
        DEFINE TABLE current_task SCHEMAFULL TYPE RELATION FROM phase_state TO task;
    """,

    2: """
        -- Add notes/context fields
        DEFINE FIELD notes ON task TYPE string;
        DEFINE FIELD context ON task TYPE object DEFAULT {};

        -- Add spec weight
        DEFINE FIELD weight ON spec TYPE string DEFAULT 'STANDARD';

        UPDATE schema_meta:current SET version = 2;
    """,

    3: """
        -- Add backlog tracking
        DEFINE FIELD backlog_id ON spec TYPE string;
        DEFINE FIELD depends_on ON spec TYPE array DEFAULT [];

        -- Add phase ordering
        DEFINE INDEX phase_order ON phase FIELDS spec, number UNIQUE;

        UPDATE schema_meta:current SET version = 3;
    """,

    # Future migrations follow same pattern
}

CURRENT_SCHEMA_VERSION = max(MIGRATIONS.keys()) if MIGRATIONS else 0


async def get_schema_version(db) -> int:
    """Get current schema version from database."""
    try:
        result = await db.query("SELECT version FROM schema_meta:current")
        if result and len(result) > 0:
            # Handle different response formats
            if isinstance(result[0], dict):
                return result[0].get('version', 0)
            elif hasattr(result[0], 'version'):
                return result[0].version
    except Exception:
        pass
    return 0  # No schema = version 0


async def set_schema_version(db, version: int) -> None:
    """Update schema version in database."""
    await db.query(f"UPDATE schema_meta:current SET version = {version}")


async def ensure_schema(db, backup: bool = True) -> None:
    """
    Check and apply any pending migrations.

    Called on database connection. Raises SchemaVersionError if
    database is newer than this spectrena version supports.

    Args:
        db: Database connection
        backup: Whether to create a backup before migrating
    """
    current = await get_schema_version(db)
    target = CURRENT_SCHEMA_VERSION

    if current == target:
        return  # Already up to date

    if current > target:
        raise SchemaVersionError(
            f"Database schema v{current} is newer than spectrena supports (v{target}). "
            f"Please update spectrena: pip install --upgrade spectrena"
        )

    console.print(f"[cyan]Migrating database schema v{current} → v{target}[/cyan]")

    # TODO: Implement backup before migration if backup=True
    # if backup and current > 0:
    #     backup_path = create_backup(db.path)
    #     console.print(f"[dim]Backup created: {backup_path}[/dim]")

    # Apply migrations in order
    for version in range(current + 1, target + 1):
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise SchemaVersionError(f"Missing migration for version {version}")

        console.print(f"  Applying migration {version}...")

        if callable(migration):
            await migration(db)
        else:
            # Split into statements and execute
            statements = migration.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    try:
                        await db.query(statement)
                    except Exception as e:
                        console.print(f"  [red]Error in migration {version}:[/red] {e}")
                        console.print(f"  [dim]Statement: {statement[:100]}...[/dim]")
                        raise

        console.print(f"  [green]✓[/green] Migration {version} complete")

    console.print(f"[green]Schema updated to v{target}[/green]")
