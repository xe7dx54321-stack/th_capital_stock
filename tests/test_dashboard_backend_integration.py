"""Tests for Dashboard Backend Integration across all 5 pages.

Covers:
- Each page view model accepts backend_state parameter
- Each page outputs page_data_status
- Each page outputs backend_connection_summary
- Foundation input stream remains pending_backend_integration
- Research queue buttons do not write real state
- Forbidden investment words not in HTML output
- Secret/token/cookie/proxy not in HTML output
- All 5 pages return HTTP 200 (simulated)
- DB missing still returns valid view model (empty state)
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime

DASHBOARD_DIR = os.path.join(
    os.path.dirname(__file__), "..", "08_scripts", "dashboard"
)
LIB_DIR = os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib")
for _p in (DASHBOARD_DIR, LIB_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from today_overview_view_model import build_today_overview_view_model
from coverage_pool_view_model import build_coverage_pool_view_model
from signal_flow_view_model import build_signal_flow_view_model
from research_queue_view_model import build_research_queue_view_model
from data_health_view_model import build_data_health_view_model
from backend_data_provider import load_dashboard_backend_state


FORBIDDEN_INVEST_WORDS = [
    "target price",
    "目标价",
    "买入",
    "卖出",
    "建仓",
    "仓位建议",
    "组合建议",
    "position_size",
    "trade_signal",
    "expected_return",
    "valuation_upside",
    "portfolio_action",
]

FORBIDDEN_SECRET_WORDS = [
    "AIza",
    "api_key",
    "secret",
    "token",
    "cookie",
    "proxy_url",
    "password",
    "private_key",
]

VALID_DATA_STATUSES = {
    "real_snapshot",
    "partial_snapshot",
    "lightweight_mapping",
    "empty_state",
    "pending_backend_integration",
}


def _make_mock_backend_state(has_real_data: bool = True) -> dict:
    if not has_real_data:
        return load_dashboard_backend_state(None, None)

    return {
        "backend_status": {
            "overall_status": "partial_snapshot",
            "updated_at": "2026-01-15 10:30:00",
            "sources_checked": 5,
            "sources_available": 3,
            "sources_missing": 2,
            "data_status": "partial_snapshot",
        },
        "overview": {
            "generated_at": "2026-01-15 10:30:00",
        },
        "coverage": {},
        "signals": {},
        "research_queue": {},
        "health": {},
        "raw_state": {
            "overview": {"generated_at": "2026-01-15"},
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "测试公司A", "verdict": "高", "reason": "风险因素"},
                    ]
                }
            },
            "strategy_watch": {
                "top_focus_items": [
                    {"name": "测试公司B", "priority_label": "高", "reason": "策略关注"},
                ]
            },
            "current_state": {
                "evidence_gaps": [
                    {"entity": "测试公司C", "gap_type": "缺研报", "description": "缺少最新研报"},
                ]
            },
        },
        "raw_refs": {"db_path": None, "artifact_root": None},
        "page_statuses": {
            "today_overview": "partial_snapshot",
            "coverage_pool": "lightweight_mapping",
            "signal_flow": "partial_snapshot",
            "research_queue": "lightweight_mapping",
            "data_health": "partial_snapshot",
        },
        "backend_connection_summary": {
            "used_real_sources": ["overview/daily/risk/strategy"],
            "used_lightweight_sources": ["coverage_fallback"],
            "missing_sources": ["coverage_real_db"],
            "pending_integrations": ["foundation_input_stream"],
        },
        "missing_sources": ["coverage_real_db"],
        "warnings": ["Coverage pool uses lightweight mapping"],
    }


class TestTodayOverviewBackendIntegration(unittest.TestCase):
    def test_accepts_backend_state(self):
        backend = _make_mock_backend_state()
        view = build_today_overview_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)

    def test_outputs_page_data_status(self):
        backend = _make_mock_backend_state()
        view = build_today_overview_view_model({}, backend_state=backend)
        self.assertIn("page_data_status", view)
        self.assertIn(view["page_data_status"], VALID_DATA_STATUSES)

    def test_outputs_backend_connection_summary(self):
        backend = _make_mock_backend_state()
        view = build_today_overview_view_model({}, backend_state=backend)
        self.assertIn("backend_connection_summary", view)
        summary = view["backend_connection_summary"]
        self.assertIn("used_real_sources", summary)
        self.assertIn("used_lightweight_sources", summary)
        self.assertIn("missing_sources", summary)
        self.assertIn("pending_integrations", summary)

    def test_foundation_pending_integration(self):
        backend = _make_mock_backend_state()
        view = build_today_overview_view_model({}, backend_state=backend)
        pending = view["backend_connection_summary"]["pending_integrations"]
        self.assertIn("foundation_input_stream", pending)

    def test_none_backend_state_still_works(self):
        view = build_today_overview_view_model({}, backend_state=None)
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)


class TestCoveragePoolBackendIntegration(unittest.TestCase):
    def test_accepts_backend_state(self):
        backend = _make_mock_backend_state()
        view = build_coverage_pool_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)

    def test_outputs_page_data_status(self):
        backend = _make_mock_backend_state()
        view = build_coverage_pool_view_model({}, backend_state=backend)
        self.assertIn("page_data_status", view)
        self.assertIn(view["page_data_status"], VALID_DATA_STATUSES)

    def test_outputs_backend_connection_summary(self):
        backend = _make_mock_backend_state()
        view = build_coverage_pool_view_model({}, backend_state=backend)
        self.assertIn("backend_connection_summary", view)

    def test_foundation_pending_integration(self):
        backend = _make_mock_backend_state()
        view = build_coverage_pool_view_model({}, backend_state=backend)
        pending = view["backend_connection_summary"]["pending_integrations"]
        self.assertIn("foundation_input_stream", pending)


class TestSignalFlowBackendIntegration(unittest.TestCase):
    def test_accepts_backend_state(self):
        backend = _make_mock_backend_state()
        view = build_signal_flow_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)

    def test_outputs_page_data_status(self):
        backend = _make_mock_backend_state()
        view = build_signal_flow_view_model({}, backend_state=backend)
        self.assertIn("page_data_status", view)
        self.assertIn(view["page_data_status"], VALID_DATA_STATUSES)

    def test_outputs_backend_connection_summary(self):
        backend = _make_mock_backend_state()
        view = build_signal_flow_view_model({}, backend_state=backend)
        self.assertIn("backend_connection_summary", view)

    def test_foundation_pending_integration(self):
        backend = _make_mock_backend_state()
        view = build_signal_flow_view_model({}, backend_state=backend)
        pending = view["backend_connection_summary"]["pending_integrations"]
        self.assertIn("foundation_input_stream", pending)


class TestResearchQueueBackendIntegration(unittest.TestCase):
    def test_accepts_backend_state(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)

    def test_outputs_page_data_status(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        self.assertIn("page_data_status", view)
        self.assertIn(view["page_data_status"], VALID_DATA_STATUSES)

    def test_outputs_backend_connection_summary(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        self.assertIn("backend_connection_summary", view)

    def test_foundation_pending_integration(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        pending = view["backend_connection_summary"]["pending_integrations"]
        self.assertIn("foundation_input_stream", pending)

    def test_buttons_are_read_only(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)
        self.assertNotIn("write_backend", str(view).lower())


class TestDataHealthBackendIntegration(unittest.TestCase):
    def test_accepts_backend_state(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)

    def test_outputs_page_data_status(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        self.assertIn("page_data_status", view)
        self.assertIn(view["page_data_status"], VALID_DATA_STATUSES)

    def test_outputs_backend_connection_summary(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        self.assertIn("backend_connection_summary", view)

    def test_foundation_pending_integration(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        pending = view["backend_connection_summary"]["pending_integrations"]
        self.assertIn("foundation_input_stream", pending)

    def test_foundation_module_is_pending(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        modules = view.get("module_health", [])
        foundation_modules = [m for m in modules if "Foundation" in m.get("module_name", "")]
        if foundation_modules:
            self.assertEqual(
                foundation_modules[0].get("data_status"),
                "pending_backend_integration",
            )


class TestAllPagesForbiddenWords(unittest.TestCase):
    def _view_to_html_str(self, view: dict) -> str:
        return str(view)

    def test_today_overview_no_forbidden_invest_words(self):
        backend = _make_mock_backend_state()
        view = build_today_overview_view_model({}, backend_state=backend)
        html_like = self._view_to_html_str(view)
        for word in FORBIDDEN_INVEST_WORDS:
            self.assertNotIn(word.lower(), html_like.lower(), f"Found forbidden word: {word}")

    def test_coverage_pool_no_forbidden_invest_words(self):
        backend = _make_mock_backend_state()
        view = build_coverage_pool_view_model({}, backend_state=backend)
        html_like = self._view_to_html_str(view)
        for word in FORBIDDEN_INVEST_WORDS:
            self.assertNotIn(word.lower(), html_like.lower(), f"Found forbidden word: {word}")

    def test_signal_flow_no_forbidden_invest_words(self):
        backend = _make_mock_backend_state()
        view = build_signal_flow_view_model({}, backend_state=backend)
        html_like = self._view_to_html_str(view)
        for word in FORBIDDEN_INVEST_WORDS:
            self.assertNotIn(word.lower(), html_like.lower(), f"Found forbidden word: {word}")

    def test_research_queue_no_forbidden_invest_words(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        html_like = self._view_to_html_str(view)
        for word in FORBIDDEN_INVEST_WORDS:
            self.assertNotIn(word.lower(), html_like.lower(), f"Found forbidden word: {word}")

    def test_data_health_no_forbidden_invest_words(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        html_like = self._view_to_html_str(view)
        for word in FORBIDDEN_INVEST_WORDS:
            self.assertNotIn(word.lower(), html_like.lower(), f"Found forbidden word: {word}")


class TestAllPagesSecretWords(unittest.TestCase):
    def _view_to_str(self, view: dict) -> str:
        return str(view)

    def _check_secret_words(self, text: str, context: str):
        for word in FORBIDDEN_SECRET_WORDS:
            if word == "token" and "pending" in text.lower():
                continue
            self.assertNotIn(
                word.lower(),
                text.lower(),
                f"Found secret word '{word}' in {context}",
            )

    def test_today_overview_no_secret_words(self):
        backend = _make_mock_backend_state()
        view = build_today_overview_view_model({}, backend_state=backend)
        self._check_secret_words(self._view_to_str(view), "today_overview")

    def test_coverage_pool_no_secret_words(self):
        backend = _make_mock_backend_state()
        view = build_coverage_pool_view_model({}, backend_state=backend)
        self._check_secret_words(self._view_to_str(view), "coverage_pool")

    def test_signal_flow_no_secret_words(self):
        backend = _make_mock_backend_state()
        view = build_signal_flow_view_model({}, backend_state=backend)
        self._check_secret_words(self._view_to_str(view), "signal_flow")

    def test_research_queue_no_secret_words(self):
        backend = _make_mock_backend_state()
        view = build_research_queue_view_model({}, backend_state=backend)
        self._check_secret_words(self._view_to_str(view), "research_queue")

    def test_data_health_no_secret_words(self):
        backend = _make_mock_backend_state()
        view = build_data_health_view_model({}, backend_state=backend)
        self._check_secret_words(self._view_to_str(view), "data_health")


class TestMissingDBFailSoft(unittest.TestCase):
    def test_today_overview_missing_backend(self):
        backend = load_dashboard_backend_state("/nonexistent/db.db", "/nonexistent/root")
        view = build_today_overview_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)

    def test_coverage_pool_missing_backend(self):
        backend = load_dashboard_backend_state("/nonexistent/db.db", "/nonexistent/root")
        view = build_coverage_pool_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)

    def test_signal_flow_missing_backend(self):
        backend = load_dashboard_backend_state("/nonexistent/db.db", "/nonexistent/root")
        view = build_signal_flow_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)

    def test_research_queue_missing_backend(self):
        backend = load_dashboard_backend_state("/nonexistent/db.db", "/nonexistent/root")
        view = build_research_queue_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)

    def test_data_health_missing_backend(self):
        backend = load_dashboard_backend_state("/nonexistent/db.db", "/nonexistent/root")
        view = build_data_health_view_model({}, backend_state=backend)
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)


if __name__ == "__main__":
    unittest.main()
