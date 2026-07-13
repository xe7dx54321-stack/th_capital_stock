from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def immediate_transaction(conn: sqlite3.Connection) -> Iterator[None]:
    if conn.in_transaction:
        savepoint = f"smr_{uuid.uuid4().hex}"
        conn.execute(f"SAVEPOINT {savepoint}")
        try:
            yield
            conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        except Exception:
            conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            conn.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise
        return

    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise


class EventStore:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.execute("PRAGMA busy_timeout=15000")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def create_run(
        self,
        run_id: str,
        workflow_id: str,
        input_data: dict[str, Any],
        *,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        created_at = created_at or utc_now()
        with immediate_transaction(self.conn):
            self.conn.execute(
                """
                INSERT INTO workflow_runs(run_id, workflow_id, status, input_json, created_at)
                VALUES (?, ?, 'queued', ?, ?)
                """,
                (run_id, workflow_id, json.dumps(input_data, ensure_ascii=False, sort_keys=True), created_at),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT run_id, workflow_id, status, input_json, summary_json,
                   error_code, error_message, created_at, started_at, completed_at,
                   cancel_requested_at
            FROM workflow_runs WHERE run_id=?
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown workflow run: {run_id}")
        return {
            "run_id": row[0],
            "workflow_id": row[1],
            "status": row[2],
            "input": json.loads(row[3] or "{}"),
            "summary": json.loads(row[4] or "{}"),
            "error_code": row[5],
            "error_message": row[6],
            "created_at": row[7],
            "started_at": row[8],
            "completed_at": row[9],
            "cancel_requested_at": row[10],
        }

    def update_run(self, run_id: str, **fields: Any) -> dict[str, Any]:
        allowed = {
            "status",
            "summary_json",
            "error_code",
            "error_message",
            "started_at",
            "completed_at",
            "cancel_requested_at",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Unsupported workflow run fields: {sorted(unknown)}")
        if "summary_json" in fields and not isinstance(fields["summary_json"], str):
            fields["summary_json"] = json.dumps(fields["summary_json"], ensure_ascii=False, sort_keys=True)
        if fields:
            assignments = ", ".join(f"{name}=?" for name in fields)
            with immediate_transaction(self.conn):
                self.conn.execute(
                    f"UPDATE workflow_runs SET {assignments} WHERE run_id=?",
                    (*fields.values(), run_id),
                )
        return self.get_run(run_id)

    def append_event(
        self,
        run_id: str,
        event_type: str,
        message: str,
        *,
        stage_id: str | None = None,
        level: str = "info",
        payload: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        created_at = created_at or utc_now()
        with immediate_transaction(self.conn):
            sequence = self.conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM workflow_events WHERE run_id=?",
                (run_id,),
            ).fetchone()[0]
            self.conn.execute(
                """
                INSERT INTO workflow_events(
                    run_id, sequence, event_type, stage_id, level, message, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    sequence,
                    event_type,
                    stage_id,
                    level,
                    message,
                    json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
                    created_at,
                ),
            )
        return {
            "run_id": run_id,
            "sequence": sequence,
            "event_type": event_type,
            "stage_id": stage_id,
            "level": level,
            "message": message,
            "payload": payload or {},
            "created_at": created_at,
        }

    def list_events(self, run_id: str, after_sequence: int = 0) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT run_id, sequence, event_type, stage_id, level, message, payload_json, created_at
            FROM workflow_events
            WHERE run_id=? AND sequence>?
            ORDER BY sequence
            """,
            (run_id, after_sequence),
        ).fetchall()
        return [
            {
                "run_id": row[0],
                "sequence": row[1],
                "event_type": row[2],
                "stage_id": row[3],
                "level": row[4],
                "message": row[5],
                "payload": json.loads(row[6] or "{}"),
                "created_at": row[7],
            }
            for row in rows
        ]
