"""Database access and repository layer."""

from findrr.db.connection import DEFAULT_DB_PATH, get_connection, init_db
from findrr.db.repository import ProfileRepository, SearchConfigRepository, TitleRepository
from findrr.db.schema import SCHEMA_SQL

__all__ = [
    "DEFAULT_DB_PATH",
    "get_connection",
    "init_db",
    "SCHEMA_SQL",
    "ProfileRepository",
    "TitleRepository",
    "SearchConfigRepository",
]
