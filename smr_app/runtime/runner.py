from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .cancellation import CancellationController
from .contracts import StageResult, WorkflowContext, WorkflowDefinition
from .event_store import EventStore, immediate_transaction, utc_now
from .migrations import apply_migrations


class WorkflowBusyError(RuntimeError):
    pass


class WorkflowDisabledError(RuntimeError):
    pass


class WorkflowRunner:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        apply_migrations(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.execute("PRAGMA busy_timeout=15000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _claim_run(
        self,
        conn: sqlite3.Connection,
        definition: WorkflowDefinition,
        input_data: dict[str, Any],
        run_id: str,
    ) -> None:
        created_at = utc_now()
        with immediate_transaction(conn):
            active = conn.execute(
                """
                SELECT run_id FROM workflow_runs
                WHERE status IN ('queued', 'running')
                ORDER BY created_at LIMIT 1
                """
            ).fetchone()
            if active:
                raise WorkflowBusyError(f"Write workflow already active: {active[0]}")
            conn.execute(
                """
                INSERT INTO workflow_runs(run_id, workflow_id, status, input_json, created_at)
                VALUES (?, ?, 'queued', ?, ?)
                """,
                (
                    run_id,
                    definition.workflow_id,
                    json.dumps(input_data, ensure_ascii=False, sort_keys=True),
                    created_at,
                ),
            )

    def run(
        self,
        definition: WorkflowDefinition,
        input_data: dict[str, Any],
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        if not definition.enabled:
            raise WorkflowDisabledError(f"Workflow is not implemented yet: {definition.workflow_id}")
        run_id = run_id or f"run_{uuid.uuid4().hex}"
        conn = self._connect()
        store = EventStore(conn)
        try:
            self._claim_run(conn, definition, input_data, run_id)
            return self._execute_claimed(conn, store, definition, input_data, run_id, emit_queued=True)
        finally:
            conn.close()

    def run_existing(self, definition: WorkflowDefinition, run_id: str) -> dict[str, Any]:
        if not definition.enabled:
            raise WorkflowDisabledError(f"Workflow is not implemented yet: {definition.workflow_id}")
        conn = self._connect()
        store = EventStore(conn)
        try:
            with immediate_transaction(conn):
                row = conn.execute(
                    "SELECT workflow_id, status, input_json FROM workflow_runs WHERE run_id=?",
                    (run_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(f"Unknown workflow run: {run_id}")
                if row[0] != definition.workflow_id:
                    raise ValueError("workflow definition does not match queued run")
                if row[1] != "queued":
                    return store.get_run(run_id)
                active = conn.execute(
                    """
                    SELECT run_id FROM workflow_runs
                    WHERE run_id<>? AND status IN ('queued', 'running')
                    ORDER BY created_at LIMIT 1
                    """,
                    (run_id,),
                ).fetchone()
                if active:
                    raise WorkflowBusyError(f"Write workflow already active: {active[0]}")
                input_data = json.loads(row[2] or "{}")
            return self._execute_claimed(conn, store, definition, input_data, run_id, emit_queued=False)
        finally:
            conn.close()

    def _execute_claimed(
        self,
        conn: sqlite3.Connection,
        store: EventStore,
        definition: WorkflowDefinition,
        input_data: dict[str, Any],
        run_id: str,
        *,
        emit_queued: bool,
    ) -> dict[str, Any]:
        try:
            if emit_queued:
                store.append_event(run_id, "run.queued", f"Queued {definition.workflow_id}")
            cancellation = CancellationController(conn, run_id)
            if cancellation.is_requested():
                return self._mark_cancelled(store, run_id)
            store.update_run(run_id, status="running", started_at=utc_now())
            store.append_event(run_id, "run.started", f"Started {definition.workflow_id}")

            context = WorkflowContext(
                run_id=run_id,
                workflow_id=definition.workflow_id,
                input_data=dict(input_data),
                db_path=self.db_path,
                _request_cancel=cancellation.request,
            )
            final_summary: dict[str, Any] = {}
            for stage in definition.stages:
                if cancellation.is_requested():
                    return self._mark_cancelled(store, run_id)
                store.append_event(
                    run_id,
                    "stage.started",
                    f"Started stage {stage.stage_id}",
                    stage_id=stage.stage_id,
                )
                result = stage.handler(context)
                if not isinstance(result, StageResult):
                    raise TypeError(f"Stage {stage.stage_id} must return StageResult")
                if result.summary:
                    final_summary = result.summary
                if result.status == "waiting_review":
                    store.update_run(run_id, status="waiting_review", summary_json=final_summary)
                    store.append_event(
                        run_id,
                        "review.requested",
                        result.message,
                        stage_id=stage.stage_id,
                        payload={**result.payload, "summary": result.summary},
                    )
                    return store.get_run(run_id)
                if result.status != "completed":
                    raise ValueError(f"Unsupported stage status: {result.status}")
                store.append_event(
                    run_id,
                    "stage.completed",
                    result.message,
                    stage_id=stage.stage_id,
                    payload={**result.payload, "summary": result.summary},
                )
                for artifact in result.artifacts:
                    store.append_event(
                        run_id,
                        "artifact.created",
                        artifact.get("title") or "Artifact created",
                        stage_id=stage.stage_id,
                        payload=artifact,
                    )

            if cancellation.is_requested():
                return self._mark_cancelled(store, run_id)
            store.update_run(
                run_id,
                status="completed",
                summary_json=final_summary,
                completed_at=utc_now(),
            )
            store.append_event(
                run_id,
                "run.completed",
                f"Completed {definition.workflow_id}",
                payload={"summary": final_summary},
            )
            return store.get_run(run_id)
        except WorkflowBusyError:
            raise
        except Exception as exc:
            error_message = str(exc)[:2000]
            store.update_run(
                run_id,
                status="failed",
                error_code=type(exc).__name__,
                error_message=error_message,
                completed_at=utc_now(),
            )
            store.append_event(
                run_id,
                "run.failed",
                error_message or type(exc).__name__,
                level="error",
                payload={"error_code": type(exc).__name__},
            )
            return store.get_run(run_id)

    @staticmethod
    def _mark_cancelled(store: EventStore, run_id: str) -> dict[str, Any]:
        store.update_run(run_id, status="cancelled", completed_at=utc_now())
        store.append_event(run_id, "run.cancelled", "Run cancelled")
        return store.get_run(run_id)
