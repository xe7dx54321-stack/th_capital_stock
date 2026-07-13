from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from smr_app.adapters.contracts import AdapterResult
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.daily_brief import daily_brief_definition


class DailyBriefWorkflowTests(unittest.TestCase):
    def test_fixture_is_change_only_deduplicated_and_category_capped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "runtime.db"
            apply_migrations(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                for index in range(8):
                    conn.execute(
                        """INSERT INTO risk_alert(
                            alert_time, alert_type, severity, ts_code, message, action, acknowledged,
                            lifecycle_status, occurrence_count, fingerprint
                        ) VALUES ('2026-07-13T01:00:00Z', 'stale_data', 'warning', ?, ?, 'refresh', 0, 'opened', 1, ?)""",
                        (f"00000{index}.SZ", f"stale fixture {index}", f"risk-{index}"),
                    )
                conn.execute(
                    """INSERT INTO risk_alert(
                        alert_time, alert_type, severity, ts_code, message, action, acknowledged,
                        lifecycle_status, occurrence_count, fingerprint
                    ) VALUES ('2026-07-13T01:00:00Z', 'stale_data', 'warning', '000000.SZ', 'stale fixture 0', 'refresh', 0, 'opened', 1, NULL)"""
                )
                conn.commit()

            scheduler_calls = []

            def scheduler(request):
                scheduler_calls.append(request)
                return AdapterResult("ok", {"job_id": request.job_id, "dry_run": request.dry_run})

            definition = daily_brief_definition(
                artifact_root=root / "artifacts",
                scheduler=scheduler,
                max_items_per_category=3,
            )
            runner = WorkflowRunner(db_path)
            results = [runner.run(definition, {"allow_network": False}) for _ in range(5)]

            self.assertEqual(results[0]["summary"]["change_count"], 3)
            self.assertEqual(len(results[0]["summary"]["categories"]["risk"]), 3)
            self.assertEqual(results[1]["summary"]["change_count"], 0)
            self.assertTrue(all(result["summary"]["change_count"] == 0 for result in results[1:]))
            self.assertEqual(len({item["identity"] for item in results[0]["summary"]["categories"]["risk"]}), 3)
            self.assertEqual(len(scheduler_calls), 5)
            self.assertTrue(all(call.dry_run for call in scheduler_calls))


if __name__ == "__main__":
    unittest.main()
