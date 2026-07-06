"""Tests for full real data integration in the Dashboard.

Validates that the backend provider and page view models correctly
integrate real data sources with provenance tracking, and that
D6.1 truth gate functionality is preserved.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "08_scripts" / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


class TestBackendProviderRealDataInventory(unittest.TestCase):
    def test_backend_state_has_real_data_inventory(self):
        from backend_data_provider import load_dashboard_backend_state
        state = load_dashboard_backend_state()
        self.assertIn("real_data_inventory", state)

    def test_real_data_inventory_has_available_sources(self):
        from backend_data_provider import load_dashboard_backend_state
        state = load_dashboard_backend_state()
        inventory = state["real_data_inventory"]
        self.assertIn("available_sources", inventory)
        self.assertIn("pending_integrations", inventory)
        self.assertIn("total_sources", inventory)
        self.assertGreater(inventory["total_sources"], 0)

    def test_real_data_inventory_foundation_pending(self):
        from backend_data_provider import load_dashboard_backend_state
        state = load_dashboard_backend_state()
        inventory = state["real_data_inventory"]
        self.assertIn("foundation_input_stream", inventory["pending_integrations"])

    def test_backend_state_has_evidence_provenance_summary(self):
        from backend_data_provider import load_dashboard_backend_state
        state = load_dashboard_backend_state()
        self.assertIn("evidence_provenance_summary", state)

    def test_evidence_provenance_summary_has_counts(self):
        from backend_data_provider import load_dashboard_backend_state
        state = load_dashboard_backend_state()
        summary = state["evidence_provenance_summary"]
        self.assertIn("total_count", summary)
        self.assertIn("evidence_backed_count", summary)
        self.assertIn("source_backed_count", summary)
        self.assertIn("generated_summary_count", summary)
        self.assertIn("main_flow_eligible_count", summary)
        self.assertIn("filtered_out_count", summary)

    def test_backend_connection_summary_still_works(self):
        from backend_data_provider import load_dashboard_backend_state
        state = load_dashboard_backend_state()
        self.assertIn("backend_connection_summary", state)
        self.assertIn("used_real_sources", state["backend_connection_summary"])
        self.assertIn("pending_integrations", state["backend_connection_summary"])


class TestSignalFlowWithProvenance(unittest.TestCase):
    def test_signal_flow_view_model_has_provenance_fields(self):
        from signal_flow_view_model import build_signal_flow_view_model
        from backend_data_provider import load_dashboard_backend_state
        backend_state = load_dashboard_backend_state()
        view = build_signal_flow_view_model(
            state=backend_state.get("dashboard_state"),
            backend_state=backend_state,
            enable_quality_gate=True,
        )
        self.assertIn("summary", view)
        self.assertIn("filtered_signal_count", view["summary"])
        self.assertIn("low_confidence_candidate_count", view["summary"])
        self.assertIsInstance(view["summary"]["filtered_signal_count"], int)
        self.assertIsInstance(view["summary"]["low_confidence_candidate_count"], int)

    def test_evidence_backed_signal_enters_main_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model
        state = {
            "daily_report": {
                "highlights": [
                    {
                        "title": "有证据的信号",
                        "content": "这是真实的日报内容",
                        "source_url": "https://example.com/report",
                        "published_at": "2026-07-06 10:00:00",
                        "source_name": "日报",
                        "source_type": "public_research",
                    }
                ]
            },
            "risk": {"monitor": {"alerts": []}, "decision": {"sell_candidates": []}},
            "strategy_watch": {"top_focus_items": []},
            "opportunity": {"watchlist_signals": []},
            "market_events": {"upcoming_events": []},
        }
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        self.assertGreater(len(view["signals"]), 0)

    def test_generated_summary_still_blocked(self):
        from signal_flow_view_model import build_signal_flow_view_model
        fake_state = {
            "risk": {
                "monitor": {"alerts": []},
                "decision": {
                    "sell_candidates": [
                        {
                            "name": "易点天下",
                            "summary": "卖出优先级已经足够高，建议减仓",
                            "verdict": "sell",
                        }
                    ]
                },
            },
            "daily_report": {"highlights": []},
            "strategy_watch": {"top_focus_items": []},
            "opportunity": {"watchlist_signals": []},
            "market_events": {"upcoming_events": []},
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertEqual(len(view["signals"]), 0)
        self.assertGreaterEqual(view["summary"]["filtered_signal_count"], 0)

    def test_default_fallback_still_blocked(self):
        from signal_flow_view_model import build_signal_flow_view_model
        state = {
            "risk": {
                "monitor": {
                    "alerts": [
                        {
                            "title": "暂无原文的风险提示",
                            "description": "系统检测到风险",
                        }
                    ]
                },
                "decision": {"sell_candidates": []},
            },
            "daily_report": {"highlights": []},
            "strategy_watch": {"top_focus_items": []},
            "opportunity": {"watchlist_signals": []},
            "market_events": {"upcoming_events": []},
        }
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        self.assertEqual(len(view["signals"]), 0)

    def test_placeholder_still_blocked(self):
        from signal_flow_view_model import build_signal_flow_view_model
        state = {
            "strategy_watch": {
                "top_focus_items": [
                    {
                        "name": "示例公司",
                        "reason": "待接入真实数据",
                    }
                ]
            },
            "risk": {"monitor": {"alerts": []}, "decision": {"sell_candidates": []}},
            "daily_report": {"highlights": []},
            "opportunity": {"watchlist_signals": []},
            "market_events": {"upcoming_events": []},
        }
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        self.assertEqual(len(view["signals"]), 0)


class TestDataHealthNoFakePercent(unittest.TestCase):
    def test_data_health_has_real_data_inventory(self):
        from data_health_view_model import build_data_health_view_model
        state = {"source_registry": {"sources": []}}
        view = build_data_health_view_model(state)
        self.assertIn("data_status", view)

    def test_data_health_no_default_84_percent(self):
        from data_health_view_model import build_data_health_view_model
        state = {}
        view = build_data_health_view_model(state)
        view_str = str(view).lower()
        self.assertNotIn("84%", view_str)
        self.assertNotIn("84 %", view_str)


class TestRealDataIntegrationSafety(unittest.TestCase):
    def test_new_modules_no_forbidden_investment_words(self):
        import inspect
        import real_data_registry
        import evidence_provenance_resolver
        modules = [real_data_registry, evidence_provenance_resolver]
        forbidden = [
            "target price",
            "目标价",
            "position_size",
            "trade_signal",
            "expected_return",
            "valuation_upside",
            "portfolio_action",
        ]
        for mod in modules:
            source = inspect.getsource(mod).lower()
            for word in forbidden:
                self.assertNotIn(
                    word.lower(), source,
                    f"Found forbidden word '{word}' in {mod.__name__}"
                )

    def test_new_modules_no_secrets_patterns(self):
        import inspect
        import real_data_registry
        import evidence_provenance_resolver
        modules = [real_data_registry, evidence_provenance_resolver]
        secret_patterns = [
            "AIza",
            "api_key",
            "private_key",
            "proxy_url",
        ]
        for mod in modules:
            source = inspect.getsource(mod)
            for pattern in secret_patterns:
                self.assertNotIn(
                    pattern, source,
                    f"Found secret pattern '{pattern}' in {mod.__name__}"
                )


if __name__ == "__main__":
    unittest.main()
