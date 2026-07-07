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


class TestVisibleRealDataFlow(unittest.TestCase):
    """Verify real backend_state data reaches each dashboard page."""

    def _load_backend(self):
        from backend_data_provider import load_dashboard_backend_state
        return load_dashboard_backend_state()

    def _is_real(self, item: dict) -> bool:
        return item.get("data_status") in {
            "real_snapshot",
            "evidence_backed_real",
            "real_snapshot_with_source",
            "real_snapshot_no_evidence",
        } or item.get("truth_status") in {
            "evidence_backed_real",
            "real_snapshot_with_source",
            "real_snapshot_no_evidence",
        }

    def test_recent_market_events_reach_today_overview(self):
        from today_overview_view_model import build_today_overview_view_model
        backend = self._load_backend()
        view = build_today_overview_view_model(backend_state=backend)
        real_changes = [c for c in view.get("top_changes", []) if self._is_real(c)]
        self.assertGreater(len(real_changes), 0)

    def test_recent_market_events_reach_signal_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model
        backend = self._load_backend()
        view = build_signal_flow_view_model(backend_state=backend)
        real_signals = [s for s in view.get("signals", []) if self._is_real(s)]
        self.assertGreater(len(real_signals), 0)

    def test_recent_market_events_reach_research_queue(self):
        from research_queue_view_model import build_research_queue_view_model
        backend = self._load_backend()
        view = build_research_queue_view_model(backend_state=backend)
        real_items = [i for i in view.get("queue_items", []) if self._is_real(i)]
        self.assertGreater(len(real_items), 0)

    def test_recent_market_events_reach_coverage_pool(self):
        from coverage_pool_view_model import build_coverage_pool_view_model
        backend = self._load_backend()
        view = build_coverage_pool_view_model(backend_state=backend)
        real_items = [i for i in view.get("coverage_items", []) if self._is_real(i)]
        self.assertGreater(len(real_items), 0)

    def test_registry_timeline_reaches_data_health(self):
        from data_health_view_model import build_data_health_view_model
        backend = self._load_backend()
        view = build_data_health_view_model(backend_state=backend)
        real_issues = [i for i in view.get("health_issues", []) if self._is_real(i)]
        self.assertGreater(len(real_issues), 0)

    def test_registry_timeline_reaches_coverage_pool(self):
        from coverage_pool_view_model import build_coverage_pool_view_model
        backend = self._load_backend()
        view = build_coverage_pool_view_model(backend_state=backend)
        real_items = [i for i in view.get("coverage_items", []) if self._is_real(i)]
        self.assertGreater(len(real_items), 0)

    def test_registry_timeline_reaches_signal_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model
        backend = self._load_backend()
        view = build_signal_flow_view_model(backend_state=backend)
        real_signals = [s for s in view.get("signals", []) if self._is_real(s)]
        self.assertGreater(len(real_signals), 0)

    def test_fake_health_events_not_present_in_rendered_health(self):
        from data_health_view_model import build_data_health_view_model
        backend = self._load_backend()
        view = build_data_health_view_model(backend_state=backend)
        titles = " ".join(i.get("title", "") for i in view.get("health_issues", []))
        fake_markers = [
            "某海外数据源",
            "站点A",
            "PDF 抽取失败率升高",
            "失败率达 18%",
            "部分海外站点反爬加强",
            "行情更新延迟（港股）",
            "部分新闻源抓取速率受限",
        ]
        for marker in fake_markers:
            self.assertNotIn(marker, titles)

    def test_empty_state_has_no_simulated_events(self):
        from today_overview_view_model import build_today_overview_view_model
        from signal_flow_view_model import build_signal_flow_view_model
        from research_queue_view_model import build_research_queue_view_model
        from coverage_pool_view_model import build_coverage_pool_view_model
        from data_health_view_model import build_data_health_view_model

        for name, builder in [
            ("today", lambda: build_today_overview_view_model({})),
            ("signals", lambda: build_signal_flow_view_model({})),
            ("research", lambda: build_research_queue_view_model({})),
            ("coverage", lambda: build_coverage_pool_view_model({})),
            ("health", lambda: build_data_health_view_model({})),
        ]:
            view = builder()
            self.assertTrue(view.get("empty_state"), f"{name} should be empty state")

    def test_real_items_carry_source_provenance_truth_data_status(self):
        from today_overview_view_model import build_today_overview_view_model
        from signal_flow_view_model import build_signal_flow_view_model
        from research_queue_view_model import build_research_queue_view_model
        from coverage_pool_view_model import build_coverage_pool_view_model
        from data_health_view_model import build_data_health_view_model
        from backend_data_provider import load_dashboard_backend_state

        backend = load_dashboard_backend_state()
        views = {
            "today": build_today_overview_view_model(backend_state=backend),
            "signals": build_signal_flow_view_model(backend_state=backend),
            "research": build_research_queue_view_model(backend_state=backend),
            "coverage": build_coverage_pool_view_model(backend_state=backend),
            "health": build_data_health_view_model(backend_state=backend),
        }

        for page_name, view in views.items():
            item_lists = {
                "today": view.get("top_changes", []) + view.get("pending_decisions", []) + view.get("coverage_moves", []),
                "signals": view.get("signals", []),
                "research": view.get("queue_items", []),
                "coverage": view.get("coverage_items", []),
                "health": view.get("health_issues", []),
            }.get(page_name, [])
            real_items = [i for i in item_lists if self._is_real(i)]
            for item in real_items:
                has_source = bool(
                    item.get("source")
                    or item.get("source_type")
                    or item.get("source_label")
                    or item.get("provenance")
                )
                has_time = bool(
                    item.get("updated_at")
                    or item.get("timestamp")
                    or item.get("latest_update")
                )
                self.assertIn("data_status", item, f"{page_name} item missing data_status")
                self.assertIn("truth_status", item, f"{page_name} item missing truth_status")
                self.assertTrue(has_source, f"{page_name} real item missing source info")
                self.assertTrue(has_time, f"{page_name} real item missing time info")


if __name__ == "__main__":
    unittest.main()
