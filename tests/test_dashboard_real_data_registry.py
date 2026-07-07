"""Tests for the Dashboard real data registry.

Validates that the real_data_registry correctly lists, classifies,
and summarizes real data sources available to the Dashboard.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "08_scripts" / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


class TestRealDataRegistry(unittest.TestCase):
    def test_list_available_real_sources(self):
        from real_data_registry import list_available_real_sources
        sources = list_available_real_sources()
        self.assertIsInstance(sources, list)
        self.assertGreater(len(sources), 0)
        self.assertIn("source_registry", sources)
        self.assertIn("daily_report", sources)
        self.assertIn("evidence_gaps", sources)
        self.assertIn("strategy_watch", sources)
        self.assertNotIn("foundation_input_stream", sources)

    def test_classify_source_priority_p0(self):
        from real_data_registry import classify_source_priority
        self.assertEqual(classify_source_priority("source_registry"), "P0")
        self.assertEqual(classify_source_priority("daily_report"), "P0")
        self.assertEqual(classify_source_priority("evidence_gaps"), "P0")
        self.assertEqual(classify_source_priority("strategy_watch"), "P0")
        self.assertEqual(classify_source_priority("overview"), "P0")

    def test_classify_source_priority_p1(self):
        from real_data_registry import classify_source_priority
        self.assertEqual(classify_source_priority("run_log"), "P1")
        self.assertEqual(classify_source_priority("opportunity_engine"), "P1")
        self.assertEqual(classify_source_priority("market_events"), "P1")

    def test_classify_source_priority_p2(self):
        from real_data_registry import classify_source_priority
        self.assertEqual(classify_source_priority("risk_monitor"), "P2")
        self.assertEqual(classify_source_priority("risk_decision"), "P2")

    def test_classify_source_priority_unknown(self):
        from real_data_registry import classify_source_priority
        self.assertEqual(classify_source_priority("nonexistent"), "unknown")

    def test_get_page_source_plan_today(self):
        from real_data_registry import get_page_source_plan
        plan = get_page_source_plan("today")
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        priorities = [s["priority"] for s in plan]
        self.assertEqual(priorities, sorted(priorities, key=lambda p: {"P0": 0, "P1": 1, "P2": 2}[p]))

    def test_get_page_source_plan_signals(self):
        from real_data_registry import get_page_source_plan
        plan = get_page_source_plan("signals")
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        source_names = [s["source_name"] for s in plan]
        self.assertIn("source_registry", source_names)
        self.assertIn("daily_report", source_names)
        self.assertIn("evidence_gaps", source_names)

    def test_get_page_source_plan_health(self):
        from real_data_registry import get_page_source_plan
        plan = get_page_source_plan("health")
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        source_names = [s["source_name"] for s in plan]
        self.assertIn("source_registry", source_names)
        self.assertIn("run_log", source_names)
        self.assertIn("overview", source_names)

    def test_validate_source_has_provenance_high(self):
        from real_data_registry import validate_source_has_provenance
        item = {
            "source_name": "测试来源",
            "source_type": "public_research",
            "source_url": "https://example.com/report",
            "published_at": "2026-07-06 10:00:00",
            "evidence_packet_id": "ep_12345",
        }
        result = validate_source_has_provenance(item)
        self.assertEqual(result["provenance_confidence"], "high")
        self.assertTrue(result["has_source"])
        self.assertTrue(result["has_evidence_packet"])
        self.assertTrue(result["has_timestamp"])

    def test_validate_source_has_provenance_medium(self):
        from real_data_registry import validate_source_has_provenance
        item = {
            "source_name": "测试来源",
            "source_type": "public_research",
            "source_url": "https://example.com/report",
        }
        result = validate_source_has_provenance(item)
        self.assertEqual(result["provenance_confidence"], "medium")
        self.assertTrue(result["has_source"])
        self.assertTrue(result["has_evidence_packet"])
        self.assertFalse(result["has_timestamp"])

    def test_validate_source_has_provenance_low(self):
        from real_data_registry import validate_source_has_provenance
        item = {
            "source_name": "测试来源",
        }
        result = validate_source_has_provenance(item)
        self.assertEqual(result["provenance_confidence"], "low")
        self.assertTrue(result["has_source"])
        self.assertFalse(result["has_evidence_packet"])
        self.assertFalse(result["has_timestamp"])

    def test_validate_source_has_provenance_none(self):
        from real_data_registry import validate_source_has_provenance
        item = {
            "title": "测试信号",
            "summary": "没有来源信息",
        }
        result = validate_source_has_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertFalse(result["has_source"])
        self.assertFalse(result["has_evidence_packet"])
        self.assertFalse(result["has_timestamp"])

    def test_summarize_real_data_coverage(self):
        from real_data_registry import summarize_real_data_coverage
        summary = summarize_real_data_coverage()
        self.assertIsInstance(summary, dict)
        self.assertIn("total_sources", summary)
        self.assertIn("available_sources", summary)
        self.assertIn("partial_sources", summary)
        self.assertIn("missing_sources", summary)
        self.assertIn("pending_integrations", summary)
        self.assertGreater(summary["total_sources"], 0)
        self.assertIn("foundation_input_stream", summary["pending_integrations"])
        self.assertGreater(summary["p0_available"], 0)


class TestRealDataRegistrySafety(unittest.TestCase):
    def test_no_network_access(self):
        from real_data_registry import REAL_DATA_SOURCES
        self.assertNotIn("network", str(REAL_DATA_SOURCES).lower())
        self.assertNotIn("http_request", str(REAL_DATA_SOURCES).lower())

    def test_no_secrets_in_registry(self):
        from real_data_registry import REAL_DATA_SOURCES
        content = str(REAL_DATA_SOURCES).lower()
        self.assertNotIn("api_key", content)
        self.assertNotIn("secret", content)
        self.assertNotIn("token", content)
        self.assertNotIn("password", content)
        self.assertNotIn("private_key", content)

    def test_no_write_functions(self):
        import inspect
        import real_data_registry
        source = inspect.getsource(real_data_registry)
        self.assertNotIn("open(", source)
        self.assertNotIn("write(", source)
        self.assertNotIn("save(", source)


if __name__ == "__main__":
    unittest.main()
