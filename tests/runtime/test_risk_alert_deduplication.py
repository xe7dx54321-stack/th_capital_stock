from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RISK_DIR = ROOT / "08_scripts" / "risk_engine"
if str(RISK_DIR) not in sys.path:
    sys.path.insert(0, str(RISK_DIR))

from monitor import (  # noqa: E402
    build_alert,
    ensure_risk_alert_lifecycle_schema,
    escalate_existing_alerts,
    persist_alerts,
    resolve_inactive_alerts,
)


def make_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE risk_alert (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_time TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            ts_code TEXT,
            message TEXT,
            action TEXT,
            acknowledged INTEGER DEFAULT 0
        )
        """
    )
    ensure_risk_alert_lifecycle_schema(conn)
    return conn


class RiskAlertDeduplicationTests(unittest.TestCase):
    def test_same_alert_five_times_creates_one_row(self) -> None:
        conn = make_connection()
        alert = build_alert(
            "data_stale",
            "critical",
            "daily bar is three sessions behind",
            "refresh data",
            "300308.SZ",
            source_state="stale",
            reason_key="daily_bar_gap",
        )

        results = []
        for minute in range(5):
            results.extend(persist_alerts(conn, [alert], f"2026-07-13 10:0{minute}:00"))

        row = conn.execute(
            "SELECT lifecycle_status, occurrence_count, first_seen_at, last_seen_at FROM risk_alert"
        ).fetchone()
        self.assertEqual(1, conn.execute("SELECT COUNT(*) FROM risk_alert").fetchone()[0])
        self.assertEqual("updated", row[0])
        self.assertEqual(5, row[1])
        self.assertEqual("2026-07-13 10:00:00", row[2])
        self.assertEqual("2026-07-13 10:04:00", row[3])
        self.assertEqual(["opened", "updated", "updated", "updated", "updated"], [r["status"] for r in results])

    def test_critical_repeat_never_escalates_another_critical_repeat(self) -> None:
        conn = make_connection()
        persist_alerts(
            conn,
            [
                build_alert(
                    "critical_repeat",
                    "critical",
                    "base alert remains open",
                    "review",
                    "300308.SZ",
                    source_state="base:1",
                )
            ],
            "2026-07-13 01:00:00",
        )

        generated = escalate_existing_alerts(conn, "2026-07-13 12:00:00")

        self.assertEqual([], generated)

    def test_repeat_for_base_critical_alert_is_upserted_not_appended(self) -> None:
        conn = make_connection()
        persist_alerts(
            conn,
            [
                build_alert(
                    "drawdown",
                    "critical",
                    "300308.SZ drawdown exceeds 20%",
                    "review",
                    "300308.SZ",
                    source_state="critical",
                )
            ],
            "2026-07-13 01:00:00",
        )

        for now in ("2026-07-13 06:00:00", "2026-07-13 07:00:00"):
            generated = escalate_existing_alerts(conn, now)
            persist_alerts(conn, generated, now)

        repeat = conn.execute(
            "SELECT occurrence_count FROM risk_alert WHERE alert_type='critical_repeat'"
        ).fetchone()
        self.assertEqual(2, conn.execute("SELECT COUNT(*) FROM risk_alert").fetchone()[0])
        self.assertEqual(2, repeat[0])

    def test_unseen_managed_alert_is_resolved_without_deleting_history(self) -> None:
        conn = make_connection()
        result = persist_alerts(
            conn,
            [build_alert("drawdown", "warning", "drawdown", "watch", "A", source_state="warning")],
            "2026-07-13 01:00:00",
        )[0]

        resolved = resolve_inactive_alerts(conn, set(), "2026-07-13 02:00:00")

        row = conn.execute("SELECT lifecycle_status, resolved_at FROM risk_alert").fetchone()
        self.assertEqual(1, resolved)
        self.assertEqual("resolved", row[0])
        self.assertEqual("2026-07-13 02:00:00", row[1])
        self.assertTrue(result["fingerprint"])


if __name__ == "__main__":
    unittest.main()
