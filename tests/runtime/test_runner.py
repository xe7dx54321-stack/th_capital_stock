from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowDefinition
from smr_app.runtime.event_store import EventStore
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.registry import PRODUCTION_WORKFLOW_IDS, production_registry
from smr_app.runtime.runner import WorkflowBusyError, WorkflowRunner


def workflow(*stages: StageDefinition) -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="test_fixture",
        title="Test fixture",
        description="Deterministic test workflow",
        stages=stages,
    )


class WorkflowRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "runtime.db"
        apply_migrations(self.db_path)
        self.runner = WorkflowRunner(self.db_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def events(self, run_id: str) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        try:
            return EventStore(conn).list_events(run_id)
        finally:
            conn.close()

    def test_production_registry_contains_only_four_fixed_workflows(self) -> None:
        registry = production_registry()
        self.assertEqual(PRODUCTION_WORKFLOW_IDS, frozenset(registry.ids()))

    def test_success_records_complete_ordered_event_sequence(self) -> None:
        definition = workflow(
            StageDefinition("load", lambda _context: StageResult.completed("loaded", {"count": 2})),
            StageDefinition("summarize", lambda _context: StageResult.completed("summarized", {"ready": True})),
        )

        run = self.runner.run(definition, {"ticker": "300308.SZ"}, run_id="run_success")

        self.assertEqual("completed", run["status"])
        self.assertEqual({"ready": True}, run["summary"])
        events = self.events("run_success")
        self.assertEqual(list(range(1, 8)), [event["sequence"] for event in events])
        self.assertEqual(
            [
                "run.queued",
                "run.started",
                "stage.started",
                "stage.completed",
                "stage.started",
                "stage.completed",
                "run.completed",
            ],
            [event["event_type"] for event in events],
        )

    def test_stage_exception_is_persisted_as_failed_run(self) -> None:
        def fail(_context):
            raise RuntimeError("fixture exploded")

        run = self.runner.run(
            workflow(StageDefinition("explode", fail)),
            {},
            run_id="run_failure",
        )

        self.assertEqual("failed", run["status"])
        self.assertEqual("RuntimeError", run["error_code"])
        self.assertIn("fixture exploded", run["error_message"])
        self.assertEqual("run.failed", self.events("run_failure")[-1]["event_type"])

    def test_cancellation_is_observed_between_stages(self) -> None:
        touched: list[str] = []

        def request_cancel(context):
            touched.append("first")
            context.request_cancel()
            return StageResult.completed("cancel requested")

        def must_not_run(_context):
            touched.append("second")
            return StageResult.completed("unexpected")

        run = self.runner.run(
            workflow(
                StageDefinition("first", request_cancel),
                StageDefinition("second", must_not_run),
            ),
            {},
            run_id="run_cancel",
        )

        self.assertEqual(["first"], touched)
        self.assertEqual("cancelled", run["status"])
        self.assertEqual("run.cancelled", self.events("run_cancel")[-1]["event_type"])

    def test_waiting_review_stops_without_marking_run_completed(self) -> None:
        run = self.runner.run(
            workflow(
                StageDefinition(
                    "review",
                    lambda _context: StageResult.waiting_review("Approve the memory candidate", {"candidate_id": "m1"}),
                )
            ),
            {},
            run_id="run_review",
        )

        self.assertEqual("waiting_review", run["status"])
        self.assertEqual("review.requested", self.events("run_review")[-1]["event_type"])

    def test_second_writer_gets_explicit_busy_error(self) -> None:
        conn = sqlite3.connect(self.db_path)
        EventStore(conn).create_run("run_active", "daily_brief", {})
        EventStore(conn).update_run("run_active", status="running")
        conn.close()

        with self.assertRaisesRegex(WorkflowBusyError, "run_active"):
            self.runner.run(workflow(), {}, run_id="run_blocked")

        conn = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                0,
                conn.execute("SELECT COUNT(*) FROM workflow_runs WHERE run_id='run_blocked'").fetchone()[0],
            )
        finally:
            conn.close()

    def test_existing_queued_run_resumes_without_duplicate_queue_event(self) -> None:
        conn = sqlite3.connect(self.db_path)
        store = EventStore(conn)
        store.create_run("run_existing", "test_fixture", {"source": "api"})
        store.append_event("run_existing", "run.queued", "Queued by API")
        conn.close()

        run = self.runner.run_existing(
            workflow(StageDefinition("work", lambda _context: StageResult.completed("done", {"ok": True}))),
            "run_existing",
        )

        self.assertEqual("completed", run["status"])
        events = self.events("run_existing")
        self.assertEqual(1, sum(event["event_type"] == "run.queued" for event in events))
        self.assertEqual(list(range(1, len(events) + 1)), [event["sequence"] for event in events])


if __name__ == "__main__":
    unittest.main()
