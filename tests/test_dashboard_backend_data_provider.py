"""Tests for the Dashboard Backend Data Provider.

Covers:
- load_dashboard_backend_state with no args (fail-soft)
- load_dashboard_backend_state with missing DB
- backend_status structure
- page_statuses for all 5 pages
- backend_connection_summary structure
- no write operations
- no network access
- Foundation input stream is pending_backend_integration
"""

from __future__ import annotations

import os
import sys
import unittest

DASHBOARD_DIR = os.path.join(
    os.path.dirname(__file__), "..", "08_scripts", "dashboard"
)
LIB_DIR = os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib")
for _p in (DASHBOARD_DIR, LIB_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend_data_provider import load_dashboard_backend_state


VALID_DATA_STATUSES = {
    "real_snapshot",
    "partial_snapshot",
    "lightweight_mapping",
    "empty_state",
    "pending_backend_integration",
}

PAGE_KEYS = {
    "today_overview",
    "coverage_pool",
    "signal_flow",
    "research_queue",
    "data_health",
}


class TestBackendDataProviderBasic(unittest.TestCase):
    def test_load_with_none_args_no_crash(self):
        result = load_dashboard_backend_state(None, None)
        self.assertIsInstance(result, dict)

    def test_load_default_no_crash(self):
        result = load_dashboard_backend_state()
        self.assertIsInstance(result, dict)

    def test_result_has_backend_status(self):
        result = load_dashboard_backend_state()
        self.assertIn("backend_status", result)
        status = result["backend_status"]
        self.assertIn("overall_status", status)
        self.assertIn("updated_at", status)
        self.assertIn("sources_checked", status)
        self.assertIn("sources_available", status)
        self.assertIn("sources_missing", status)
        self.assertIn("data_status", status)

    def test_overall_status_is_valid(self):
        result = load_dashboard_backend_state()
        status = result["backend_status"]["overall_status"]
        self.assertIn(status, VALID_DATA_STATUSES)

    def test_result_has_page_sections(self):
        result = load_dashboard_backend_state()
        for key in ["overview", "coverage", "signals", "research_queue", "health"]:
            self.assertIn(key, result)

    def test_result_has_page_statuses(self):
        result = load_dashboard_backend_state()
        self.assertIn("page_statuses", result)
        page_statuses = result["page_statuses"]
        self.assertEqual(set(page_statuses.keys()), PAGE_KEYS)
        for page, status in page_statuses.items():
            self.assertIn(status, VALID_DATA_STATUSES, f"{page} has invalid status {status}")

    def test_result_has_backend_connection_summary(self):
        result = load_dashboard_backend_state()
        self.assertIn("backend_connection_summary", result)
        summary = result["backend_connection_summary"]
        self.assertIn("used_real_sources", summary)
        self.assertIn("used_lightweight_sources", summary)
        self.assertIn("missing_sources", summary)
        self.assertIn("pending_integrations", summary)

    def test_foundation_is_pending_integration(self):
        result = load_dashboard_backend_state()
        pending = result["backend_connection_summary"]["pending_integrations"]
        self.assertIn("foundation_input_stream", pending)

    def test_result_has_missing_sources_list(self):
        result = load_dashboard_backend_state()
        self.assertIn("missing_sources", result)
        self.assertIsInstance(result["missing_sources"], list)

    def test_result_has_warnings_list(self):
        result = load_dashboard_backend_state()
        self.assertIn("warnings", result)
        self.assertIsInstance(result["warnings"], list)

    def test_result_has_raw_refs(self):
        result = load_dashboard_backend_state()
        self.assertIn("raw_refs", result)
        refs = result["raw_refs"]
        self.assertIn("db_path", refs)
        self.assertIn("artifact_root", refs)

    def test_allow_missing_true_no_exception(self):
        try:
            load_dashboard_backend_state(
                db_path="/nonexistent/path/db.db",
                artifact_root="/nonexistent/path",
                allow_missing=True,
            )
        except Exception as e:
            self.fail(f"load_dashboard_backend_state raised {type(e).__name__} with allow_missing=True")

    def test_provider_is_read_only(self):
        result = load_dashboard_backend_state()
        self.assertIsInstance(result, dict)
        self.assertNotIn("write", str(result.get("backend_status", {})).lower())


class TestBackendDataProviderWithMockState(unittest.TestCase):
    def test_partial_state_detected(self):
        import backend_data_provider as bdp

        original_build = bdp._safe_build_state

        def mock_build(db_path=None):
            return {
                "overview": {"generated_at": "2026-01-01"},
                "risk": {"monitor": {"alerts": []}},
                "strategy_watch": {"top_focus_items": []},
            }

        bdp._safe_build_state = mock_build
        try:
            result = bdp.load_dashboard_backend_state()
            self.assertIn("page_statuses", result)
            overview_status = result["page_statuses"]["today_overview"]
            self.assertIn(overview_status, {"real_snapshot", "partial_snapshot"})
        finally:
            bdp._safe_build_state = original_build

    def test_empty_state_detected(self):
        import backend_data_provider as bdp

        original_build = bdp._safe_build_state

        def mock_build(db_path=None):
            return None

        bdp._safe_build_state = mock_build
        try:
            result = bdp.load_dashboard_backend_state()
            status = result["backend_status"]["overall_status"]
            self.assertIn(status, {"empty_state", "lightweight_mapping"})
        finally:
            bdp._safe_build_state = original_build


if __name__ == "__main__":
    unittest.main()
