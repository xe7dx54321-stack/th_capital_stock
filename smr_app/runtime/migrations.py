from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
ADD_COLUMN_RE = re.compile(
    r"^\s*ALTER\s+TABLE\s+([A-Za-z_][A-Za-z0-9_]*)\s+ADD\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)\b",
    re.IGNORECASE | re.DOTALL,
)


class MigrationError(RuntimeError):
    pass


class MigrationChecksumError(MigrationError):
    pass


@dataclass(frozen=True)
class MigrationResult:
    applied_versions: list[str]
    skipped_versions: list[str]


def _bootstrap(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(schema_migrations)")}
    if "checksum" not in columns:
        conn.execute("ALTER TABLE schema_migrations ADD COLUMN checksum TEXT")
    conn.commit()


def _statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                statements.append(statement)
            buffer = ""
    if buffer.strip():
        statements.append(buffer.strip())
    return statements


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return column.lower() in {str(row[1]).lower() for row in conn.execute(f"PRAGMA table_info({table})")}


def _execute_migration(conn: sqlite3.Connection, sql: str) -> None:
    for statement in _statements(sql):
        match = ADD_COLUMN_RE.match(statement)
        if match and _column_exists(conn, match.group(1), match.group(2)):
            continue
        conn.execute(statement)


def apply_migrations(
    db_path: str | Path,
    migrations_dir: str | Path | None = None,
) -> MigrationResult:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    migration_root = Path(migrations_dir) if migrations_dir is not None else DEFAULT_MIGRATIONS_DIR
    files = sorted(migration_root.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    if not files:
        raise MigrationError(f"No migrations found in {migration_root}")

    conn = sqlite3.connect(db_path, timeout=15)
    conn.execute("PRAGMA busy_timeout=15000")
    conn.execute("PRAGMA foreign_keys=ON")
    applied: list[str] = []
    skipped: list[str] = []
    try:
        _bootstrap(conn)
        for path in files:
            version = path.name.split("_", 1)[0]
            sql_bytes = path.read_bytes()
            checksum = hashlib.sha256(sql_bytes).hexdigest()
            existing = conn.execute(
                "SELECT checksum FROM schema_migrations WHERE version=?",
                (version,),
            ).fetchone()
            if existing:
                if existing[0] != checksum:
                    raise MigrationChecksumError(
                        f"Migration {version} checksum changed: recorded={existing[0]!r}, current={checksum}"
                    )
                skipped.append(version)
                continue

            conn.execute("BEGIN IMMEDIATE")
            try:
                _execute_migration(conn, sql_bytes.decode("utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations(version, checksum) VALUES (?, ?)",
                    (version, checksum),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            applied.append(version)
    finally:
        conn.close()
    return MigrationResult(applied, skipped)
