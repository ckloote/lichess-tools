from __future__ import annotations

import sqlite3

from lichess_tools.db.schema import MIGRATIONS, SCHEMA_VERSION


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Run any pending migrations to bring the schema up to date."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);"
    )
    conn.commit()

    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current_version = row[0] if row[0] is not None else 0

    for version in sorted(MIGRATIONS.keys()):
        if version <= current_version:
            continue
        for statement in MIGRATIONS[version]:
            conn.executescript(statement)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()
