"""SQLite database connection and lifecycle management."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from findrr.db.schema import COLUMN_MIGRATIONS, SCHEMA_SQL

DEFAULT_DB_DIR = Path("data")
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "findrr.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and configure an SQLite database connection.

    Enforces foreign keys, WAL journaling (for disk DBs), and dictionary row factory.
    """
    if db_path is None:
        db_path = os.getenv("FINDRR_DB_PATH", str(DEFAULT_DB_PATH))

    if db_path != ":memory:":
        target_dir = Path(db_path).parent
        target_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    if db_path != ":memory:":
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.close()

    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database tables, constraints, and indexes."""
    with conn:
        conn.executescript(SCHEMA_SQL)
        _apply_column_migrations(conn)


def _apply_column_migrations(conn: sqlite3.Connection) -> None:
    """Add nullable columns introduced after a database was first created (idempotent)."""
    for table, column, col_type in COLUMN_MIGRATIONS:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
