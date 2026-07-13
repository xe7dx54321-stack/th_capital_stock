from __future__ import annotations

import sqlite3

from .event_store import immediate_transaction, utc_now


class CancellationController:
    def __init__(self, conn: sqlite3.Connection, run_id: str):
        self.conn = conn
        self.run_id = run_id

    def request(self, requested_at: str | None = None) -> bool:
        requested_at = requested_at or utc_now()
        with immediate_transaction(self.conn):
            cursor = self.conn.execute(
                """
                UPDATE workflow_runs
                SET cancel_requested_at=COALESCE(cancel_requested_at, ?)
                WHERE run_id=? AND status IN ('queued', 'running', 'waiting_review')
                """,
                (requested_at, self.run_id),
            )
        return bool(cursor.rowcount)

    def is_requested(self) -> bool:
        row = self.conn.execute(
            "SELECT cancel_requested_at FROM workflow_runs WHERE run_id=?",
            (self.run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown workflow run: {self.run_id}")
        return row[0] is not None
