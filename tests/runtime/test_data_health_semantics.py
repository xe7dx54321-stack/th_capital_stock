from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_data_health import classify_health_semantics  # noqa: E402


class DataHealthSemanticsTests(unittest.TestCase):
    def classify(self, collection_state: str | None = None, timestamp: str | None = "2026-07-13 09:30:00"):
        return classify_health_semantics(
            data_type="daily_bar",
            source_key="daily_bar",
            last_data_timestamp=timestamp,
            stale_after_minutes=60,
            rule={
                "blocking_level_when_stale": "block",
                "blocking_level_when_missing": "block",
                "blocking_level_when_fetch_failed": "degrade",
            },
            now=datetime(2026, 7, 13, 12, 0, 0),
            collection_state=collection_state,
        )

    def test_market_closed_is_healthy_not_failed(self) -> None:
        result = self.classify("market_closed", timestamp="2026-07-10 18:00:00")
        self.assertEqual("market_closed", result.condition)
        self.assertEqual("fresh", result.freshness_status)
        self.assertEqual("none", result.blocking_level)

    def test_source_not_due_is_healthy_not_stale(self) -> None:
        result = self.classify("source_not_due", timestamp=None)
        self.assertEqual("source_not_due", result.condition)
        self.assertEqual("fresh", result.freshness_status)
        self.assertEqual("none", result.blocking_level)

    def test_fetch_failed_is_distinct_from_data_stale(self) -> None:
        result = self.classify("fetch_failed")
        self.assertEqual("fetch_failed", result.condition)
        self.assertEqual("degraded", result.freshness_status)
        self.assertEqual("degrade", result.blocking_level)

    def test_old_data_is_data_stale(self) -> None:
        result = self.classify(timestamp="2026-07-13 09:00:00")
        self.assertEqual("data_stale", result.condition)
        self.assertEqual("stale", result.freshness_status)
        self.assertEqual("block", result.blocking_level)

    def test_not_configured_is_distinct_from_missing_data(self) -> None:
        result = self.classify("not_configured", timestamp=None)
        self.assertEqual("not_configured", result.condition)
        self.assertEqual("missing", result.freshness_status)
        self.assertEqual("block", result.blocking_level)


if __name__ == "__main__":
    unittest.main()
