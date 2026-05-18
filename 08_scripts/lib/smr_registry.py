#!/usr/bin/env python3
"""Append-only task registry helpers for SMR script and workflow snapshots."""

import sqlite3

from smr_wiki import dumps_json, generate_execution_id, loads_json, now_ts


def ensure_task_registry_tables(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS task_registry_entry (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            relationships_json TEXT NOT NULL DEFAULT '{}',
            payload_json TEXT NOT NULL DEFAULT '{}',
            snapshot_index INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_task_registry_entity
        ON task_registry_entry(entity_type, entity_id, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_task_registry_source_status
        ON task_registry_entry(source, status, created_at DESC);
        """
    )
    try:
        conn.execute(
            """
            CREATE VIEW task_registry_entity_latest AS
            WITH ranked AS (
                SELECT
                    id,
                    entity_type,
                    entity_id,
                    status,
                    source,
                    relationships_json,
                    payload_json,
                    snapshot_index,
                    created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY entity_type, entity_id
                        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
                    ) AS rn
                FROM task_registry_entry
            )
            SELECT
                id,
                entity_type,
                entity_id,
                status,
                source,
                relationships_json,
                payload_json,
                snapshot_index,
                created_at
            FROM ranked
            WHERE rn = 1
            """
        )
    except sqlite3.OperationalError as exc:
        if "already exists" not in str(exc):
            raise


def register_snapshot(conn, entity_type, entity_id, status, source, relationships=None, payload=None, created_at=None):
    ensure_task_registry_tables(conn)
    created_at = created_at or now_ts()
    relationships = relationships or {}
    payload = payload or {}
    row = conn.execute(
        """
        SELECT COALESCE(MAX(snapshot_index), 0)
        FROM task_registry_entry
        WHERE entity_type=? AND entity_id=?
        """,
        (entity_type, entity_id),
    ).fetchone()
    snapshot_index = (row[0] or 0) + 1
    entry_id = generate_execution_id("registry")
    conn.execute(
        """
        INSERT INTO task_registry_entry (
            id,
            entity_type,
            entity_id,
            status,
            source,
            relationships_json,
            payload_json,
            snapshot_index,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            entity_type,
            entity_id,
            status,
            source,
            dumps_json(relationships),
            dumps_json(payload),
            snapshot_index,
            created_at,
        ),
    )
    return {
        "id": entry_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": status,
        "source": source,
        "snapshot_index": snapshot_index,
        "created_at": created_at,
        "relationships": relationships,
        "payload": payload,
    }


def list_entries(conn, entity_type=None, entity_id=None, source=None, status=None, limit=20):
    ensure_task_registry_tables(conn)
    filters = []
    params = []
    if entity_type:
        filters.append("entity_type=?")
        params.append(entity_type)
    if entity_id:
        filters.append("entity_id=?")
        params.append(entity_id)
    if source:
        filters.append("source=?")
        params.append(source)
    if status:
        filters.append("status=?")
        params.append(status)

    query = """
        SELECT
            id,
            entity_type,
            entity_id,
            status,
            source,
            relationships_json,
            payload_json,
            snapshot_index,
            created_at
        FROM task_registry_entry
    """
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": row[0],
            "entity_type": row[1],
            "entity_id": row[2],
            "status": row[3],
            "source": row[4],
            "relationships": loads_json(row[5], {}),
            "payload": loads_json(row[6], {}),
            "snapshot_index": row[7],
            "created_at": row[8],
        }
        for row in rows
    ]


def get_entity_snapshot(conn, entity_type, entity_id, limit=10):
    ensure_task_registry_tables(conn)
    rows = list_entries(conn, entity_type=entity_type, entity_id=entity_id, limit=limit)
    if not rows:
        return None
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "snapshot_count": conn.execute(
            """
            SELECT COUNT(*)
            FROM task_registry_entry
            WHERE entity_type=? AND entity_id=?
            """,
            (entity_type, entity_id),
        ).fetchone()[0],
        "latest_entry": rows[0],
        "entries": rows,
    }
