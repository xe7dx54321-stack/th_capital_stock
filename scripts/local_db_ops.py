#!/usr/bin/env python3
"""Read-only diagnostics and online SQLite backups for the local workbench."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def expected_migration_versions(migrations_dir: str | Path | None = None) -> list[str]:
    root = Path(migrations_dir) if migrations_dir is not None else DEFAULT_MIGRATIONS_DIR
    return [path.name.split("_", 1)[0] for path in sorted(root.glob("[0-9][0-9][0-9][0-9]_*.sql"))]


def inspect_database(
    db_path: str | Path,
    migrations_dir: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"database not found: {path}")

    with closing(sqlite3.connect(_readonly_uri(path), uri=True, timeout=15)) as conn:
        conn.execute("PRAGMA query_only=ON")
        quick_check = str(conn.execute("PRAGMA quick_check").fetchone()[0])
        tables = {
            str(row[0])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        applied: list[str] = []
        if "schema_migrations" in tables:
            applied = [
                str(row[0])
                for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
            ]
        query_only = int(conn.execute("PRAGMA query_only").fetchone()[0])

    expected = expected_migration_versions(migrations_dir)
    missing = [version for version in expected if version not in set(applied)]
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "quick_check": quick_check,
        "query_only": query_only,
        "table_count": len(tables),
        "applied_migrations": applied,
        "expected_migrations": expected,
        "missing_migrations": missing,
    }


def verify_database(db_path: str | Path) -> dict[str, Any]:
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"database not found: {path}")
    with closing(sqlite3.connect(_readonly_uri(path), uri=True, timeout=30)) as conn:
        conn.execute("PRAGMA query_only=ON")
        integrity_check = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        query_only = int(conn.execute("PRAGMA query_only").fetchone()[0])
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "integrity_check": integrity_check,
        "query_only": query_only,
    }


def backup_database(source_path: str | Path, destination_path: str | Path) -> dict[str, Any]:
    source = Path(source_path).resolve()
    destination = Path(destination_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"database not found: {source}")
    if destination.exists():
        raise FileExistsError(f"backup destination already exists: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.partial")
    if partial.exists():
        partial.unlink()

    try:
        with closing(sqlite3.connect(_readonly_uri(source), uri=True, timeout=30)) as source_conn:
            source_conn.execute("PRAGMA query_only=ON")
            with closing(sqlite3.connect(partial, timeout=30)) as destination_conn:
                source_conn.backup(destination_conn, pages=2048, sleep=0.01)
        verification = verify_database(partial)
        if verification["integrity_check"] != "ok":
            raise sqlite3.DatabaseError(
                f"backup integrity check failed: {verification['integrity_check']}"
            )
        os.replace(partial, destination)
    except Exception:
        if partial.exists():
            partial.unlink()
        raise

    return {
        "source": str(source),
        "destination": str(destination),
        "size_bytes": destination.stat().st_size,
        "integrity_check": "ok",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a database without writing")
    inspect_parser.add_argument("--db", required=True, type=Path)
    inspect_parser.add_argument("--migrations-dir", type=Path, default=DEFAULT_MIGRATIONS_DIR)

    verify_parser = subparsers.add_parser("verify", help="Run a full integrity check read-only")
    verify_parser.add_argument("--db", required=True, type=Path)

    backup_parser = subparsers.add_parser("backup", help="Create and verify an online backup")
    backup_parser.add_argument("--db", required=True, type=Path)
    backup_parser.add_argument("--destination", required=True, type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "inspect":
        result = inspect_database(args.db, args.migrations_dir)
    elif args.command == "verify":
        result = verify_database(args.db)
    else:
        result = backup_database(args.db, args.destination)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
