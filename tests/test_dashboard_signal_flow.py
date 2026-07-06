"""Tests for the Signal Flow dashboard page view model and rendering.

Covers:
- build_signal_flow_view_model fail-soft with None / {}
- summary 4 cards structure
- signals capped at 20
- hot_entities aggregation
- source_distribution aggregation
- filters support all 5 dimensions
- bad filter values don't crash
- /signals page HTML contains expected sections
- 5 nav items still present
- placeholder pages still work
- forbidden words absent
- empty state present when no data
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta

DASHBOARD_DIR = os.path.join(
    os.path.dirname(__file__), "..", "08_scripts", "dashboard"
)
LIB_DIR = os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib")
for _p in (DASHBOARD_DIR, LIB_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from signal_flow_view_model import build_signal_flow_view_model


FORBIDDEN_WORDS = [
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

NAV_LABELS = ["今日总览", "覆盖池", "信号流", "研究队列", "数据健康"]


class TestSignalFlowViewModel(unittest.TestCase):
    def test_none_state_no_crash(self):
        view = build_signal_flow_view_model(None)
        self.assertIsInstance(view, dict)
        self.assertIn("filters", view)
        self.assertIn("summary", view)
        self.assertIn("signals", view)
        self.assertIn("hot_entities", view)
        self.assertIn("source_distribution", view)
        self.assertIn("empty_state", view)
        self.assertIn("updated_at", view)

    def test_empty_dict_no_crash(self):
        view = build_signal_flow_view_model({})
        self.assertTrue(view["empty_state"])
        self.assertEqual(view["summary"]["total_signals"], 0)

    def test_summary_four_cards(self):
        view = build_signal_flow_view_model({})
        s = view["summary"]
        self.assertIn("total_signals", s)
        self.assertIn("focus_company_count", s)
        self.assertIn("high_strength_count", s)
        self.assertIn("needs_review_count", s)
        self.assertIsInstance(s["total_signals"], int)
        self.assertIsInstance(s["focus_company_count"], int)
        self.assertIsInstance(s["high_strength_count"], int)
        self.assertIsInstance(s["needs_review_count"], int)

    def test_signals_default_max_20(self):
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": f"公司{i}", "reason": "测试风险"}
                        for i in range(30)
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, limit=20)
        self.assertLessEqual(len(view["signals"]), 20)

    def test_hot_entities_aggregation(self):
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "英伟达", "reason": "测试"},
                        {"name": "英伟达", "reason": "测试2"},
                        {"name": "博通", "reason": "测试"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state)
        entities = {e["name"]: e["count"] for e in view["hot_entities"]}
        self.assertIn("英伟达", entities)
        self.assertGreaterEqual(entities["英伟达"], 2)

    def test_source_distribution_aggregation(self):
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "公司A", "reason": "测试风险"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state)
        dist = {d["source_type"]: d["count"] for d in view["source_distribution"]}
        self.assertIn("risk_monitor", dist)
        self.assertGreaterEqual(dist["risk_monitor"], 1)
        self.assertIn("official_disclosure", dist)

    def test_filters_time_range_24h(self):
        now = datetime.now()
        old_signal_time = now - timedelta(days=2)
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "新公司", "reason": "新信号"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(
            fake_state, filters={"time_range": "24h"}, now=now
        )
        self.assertIsInstance(view["filters"]["time_range"], str)
        self.assertEqual(view["filters"]["time_range"], "24h")

    def test_filters_source_type(self):
        view = build_signal_flow_view_model(
            {}, filters={"source_type": "risk_monitor"}
        )
        self.assertEqual(view["filters"]["source_type"], "risk_monitor")

    def test_filters_entity(self):
        view = build_signal_flow_view_model({}, filters={"entity": "company"})
        self.assertEqual(view["filters"]["entity"], "company")

    def test_filters_strength(self):
        view = build_signal_flow_view_model({}, filters={"strength": "高"})
        self.assertEqual(view["filters"]["strength"], "高")

    def test_filters_keyword(self):
        view = build_signal_flow_view_model({}, filters={"q": "英伟达"})
        self.assertEqual(view["filters"]["q"], "英伟达")

    def test_bad_filter_values_no_crash(self):
        bad_filters = {
            "time_range": "non_existent_value",
            "source_type": "<script>",
            "entity": None,
            "strength": 123,
            "q": "<b>xss</b>",
        }
        view = build_signal_flow_view_model({}, filters=bad_filters)
        self.assertIsInstance(view, dict)
        self.assertIn("filters", view)

    def test_updated_at_present(self):
        view = build_signal_flow_view_model({})
        self.assertTrue(isinstance(view["updated_at"], str))
        self.assertTrue(len(view["updated_at"]) > 0)

    def test_empty_state_flag(self):
        view = build_signal_flow_view_model({})
        self.assertTrue(view["empty_state"])

    def test_signal_signal_structure(self):
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [{"name": "测试公司", "reason": "风险原因"}]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state)
        self.assertGreater(len(view["signals"]), 0)
        s = view["signals"][0]
        for field in [
            "time_label", "title", "summary", "source_type", "source_label",
            "related_entities", "related_topics", "evidence_strength",
            "timestamp_confidence", "review_status",
        ]:
            self.assertIn(field, s, f"missing field: {field}")


class TestSignalFlowRendering(unittest.TestCase):
    def _render(self, state: dict | None = None, filters: dict | None = None) -> str:
        from run_control_tower import render_signal_flow

        state = state or {}
        return render_signal_flow(state, refresh_seconds=0, filters=filters)

    def test_render_no_crash_empty_state(self):
        html = self._render({})
        self.assertIn("信号流", html)

    def test_render_has_five_nav_items(self):
        html = self._render({})
        for label in NAV_LABELS:
            self.assertIn(label, html, f"nav missing: {label}")

    def test_render_no_forbidden_words(self):
        html = self._render({}).lower()
        for word in FORBIDDEN_WORDS:
            self.assertNotIn(word.lower(), html, f"forbidden word found: {word}")

    def test_render_filter_bar_present(self):
        html = self._render({})
        self.assertIn("时间范围", html)
        self.assertIn("来源类型", html)
        self.assertIn("关联对象", html)
        self.assertIn("证据强度", html)
        self.assertIn("关键词搜索", html)
        self.assertIn("重置筛选", html)

    def test_render_timeline_present(self):
        html = self._render({})
        self.assertIn("信号时间线", html)

    def test_render_summary_present(self):
        html = self._render({})
        self.assertIn("今日信号摘要", html)

    def test_render_hot_entities_present(self):
        html = self._render({})
        self.assertIn("热门关联对象", html)

    def test_render_source_distribution_present(self):
        html = self._render({})
        self.assertIn("信号来源分布", html)

    def test_render_disclaimer_present(self):
        html = self._render({})
        self.assertIn("系统仅展示证据与信号，不直接给出投资建议", html)

    def test_render_empty_state_text(self):
        html = self._render({})
        self.assertIn("暂无信号", html)

    def test_render_with_filters(self):
        html = self._render({}, filters={"time_range": "7d", "q": "测试"})
        self.assertIn("信号流", html)


class TestPlaceholderPagesStillWork(unittest.TestCase):
    def test_coverage_placeholder(self):
        import run_control_tower as rt

        html = rt.render_coverage_pool({}, 0)
        self.assertIn("覆盖池", html)
        self.assertIn("覆盖对象列表", html)

    def test_research_placeholder(self):
        import run_control_tower as rt

        html = rt.render_research_queue({}, 0)
        self.assertIn("研究队列", html)

    def test_health_placeholder(self):
        import run_control_tower as rt

        html = rt.render_placeholder_health({}, 0)
        self.assertIn("数据健康", html)

    def test_today_overview_still_works(self):
        import run_control_tower as rt

        html = rt.render_today_overview({}, 0)
        self.assertIn("今日总览", html)


class TestPageRenderers(unittest.TestCase):
    def test_five_page_renderers(self):
        import run_control_tower as rt

        self.assertEqual(len(rt.PAGE_RENDERERS), 5)
        paths = set(rt.PAGE_RENDERERS.keys())
        self.assertEqual(paths, {"/", "/coverage", "/signals", "/research", "/health"})


if __name__ == "__main__":
    unittest.main()
