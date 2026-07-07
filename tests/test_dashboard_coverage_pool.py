"""Tests for the Coverage Pool dashboard page view model and rendering.

Covers:
- build_coverage_pool_view_model fail-soft with None / {}
- metrics 4 cards structure
- coverage_items capped at 12
- selected_detail structure
- coverage_distribution structure
- priority_hotzone structure
- filters support type / priority / status / q / page
- bad filter values don't crash
- /coverage page HTML contains expected sections
- 5 nav items still present
- other completed pages still work
- forbidden words absent
- empty state present when no data
- data_status field present
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

from coverage_pool_view_model import build_coverage_pool_view_model


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


class TestCoveragePoolViewModel(unittest.TestCase):
    def test_none_state_no_crash(self):
        view = build_coverage_pool_view_model(None)
        self.assertIsInstance(view, dict)
        self.assertIn("data_status", view)
        self.assertIn("metrics", view)
        self.assertIn("filters", view)
        self.assertIn("coverage_items", view)
        self.assertIn("selected_detail", view)
        self.assertIn("coverage_distribution", view)
        self.assertIn("priority_hotzone", view)
        self.assertIn("empty_state", view)
        self.assertIn("updated_at", view)

    def test_empty_dict_no_crash(self):
        view = build_coverage_pool_view_model({})
        self.assertTrue(view["empty_state"])
        self.assertEqual(view["metrics"]["company_count"]["count"], 0)

    def test_data_status_present(self):
        view = build_coverage_pool_view_model({})
        self.assertEqual(view["data_status"], "lightweight_mapping")
        self.assertIn("data_status", view["selected_detail"])

    def test_metrics_four_cards(self):
        view = build_coverage_pool_view_model({})
        m = view["metrics"]
        for key in ["company_count", "industry_count", "high_priority_count", "evidence_completeness"]:
            self.assertIn(key, m, f"missing metric: {key}")
            if key == "evidence_completeness":
                self.assertIn("value", m[key])
            else:
                self.assertIn("count", m[key])
            self.assertIn("subtitle", m[key])

    def test_coverage_items_default_max_12(self):
        fake_state = {
            "current_state": {
                "evidence_gaps": [{"entity": f"公司{i}", "gap_type": "测试"} for i in range(30)]
            }
        }
        view = build_coverage_pool_view_model(fake_state, limit=12)
        self.assertLessEqual(len(view["coverage_items"]), 12)

    def test_selected_detail_structure(self):
        view = build_coverage_pool_view_model({})
        d = view["selected_detail"]
        for field in [
            "name", "type", "badges", "priority", "focus_points",
            "latest_signals", "evidence_overview", "missing_evidence",
            "related_topics", "related_companies", "data_status",
        ]:
            self.assertIn(field, d, f"missing field: {field}")

    def test_evidence_overview_structure(self):
        view = build_coverage_pool_view_model({})
        ev = view["selected_detail"]["evidence_overview"]
        for field in ["completeness", "covered_count", "partial_count", "missing_count"]:
            self.assertIn(field, ev, f"missing evidence field: {field}")

    def test_coverage_distribution_structure(self):
        view = build_coverage_pool_view_model({})
        dist = view["coverage_distribution"]
        self.assertIsInstance(dist, list)
        if dist:
            for d in dist:
                for field in ["type", "count", "percentage"]:
                    self.assertIn(field, d, f"missing dist field: {field}")

    def test_priority_hotzone_structure(self):
        view = build_coverage_pool_view_model({})
        hotzone = view["priority_hotzone"]
        self.assertIsInstance(hotzone, list)

    def test_filters_type(self):
        view = build_coverage_pool_view_model({}, filters={"type": "company"})
        self.assertEqual(view["filters"]["type"], "company")

    def test_filters_priority(self):
        view = build_coverage_pool_view_model({}, filters={"priority": "高"})
        self.assertEqual(view["filters"]["priority"], "高")

    def test_filters_status(self):
        view = build_coverage_pool_view_model({}, filters={"status": "跟踪中"})
        self.assertEqual(view["filters"]["status"], "跟踪中")

    def test_filters_keyword(self):
        view = build_coverage_pool_view_model({}, filters={"q": "英伟达"})
        self.assertEqual(view["filters"]["q"], "英伟达")

    def test_filters_page(self):
        view = build_coverage_pool_view_model({}, filters={"page": 2})
        self.assertEqual(view["filters"]["page"], 2)

    def test_bad_filter_values_no_crash(self):
        bad_filters = {
            "type": "<script>",
            "priority": None,
            "status": 123,
            "q": "<b>xss</b>",
            "page": "abc",
        }
        view = build_coverage_pool_view_model({}, filters=bad_filters)
        self.assertIsInstance(view, dict)

    def test_coverage_item_structure(self):
        fake_state = {
            "current_state": {"evidence_gaps": [{"entity": "测试", "gap_type": "测试"}]},
            "strategy_watch": {"top_focus_items": [{"name": "测试公司", "reason": "测试"}]},
        }
        view = build_coverage_pool_view_model(fake_state)
        if view["coverage_items"]:
            item = view["coverage_items"][0]
            for field in [
                "item_id", "name", "type", "status", "evidence_completeness",
                "priority", "updated_at", "related_entities", "related_topics",
                "focus_points", "data_status",
            ]:
                self.assertIn(field, item, f"missing item field: {field}")


class TestCoveragePoolRendering(unittest.TestCase):
    def _render(self, state: dict | None = None, filters: dict | None = None) -> str:
        from run_control_tower import render_coverage_pool

        state = state or {}
        return render_coverage_pool(state, refresh_seconds=0, filters=filters)

    def test_render_no_crash_empty_state(self):
        html = self._render({})
        self.assertIn("覆盖池", html)

    def test_render_has_five_nav_items(self):
        html = self._render({})
        for label in NAV_LABELS:
            self.assertIn(label, html, f"nav missing: {label}")

    def test_render_no_forbidden_words(self):
        html = self._render({}).lower()
        for word in FORBIDDEN_WORDS:
            self.assertNotIn(word.lower(), html, f"forbidden word found: {word}")

    def test_render_has_kpi_cards(self):
        html = self._render({})
        self.assertIn("覆盖公司数", html)
        self.assertIn("覆盖行业/主题数", html)
        self.assertIn("高优先级对象", html)
        self.assertIn("证据完整度", html)

    def test_render_coverage_list_present(self):
        html = self._render({})
        self.assertIn("覆盖对象列表", html)

    def test_render_coverage_detail_present(self):
        html = self._render({})
        self.assertIn("投资关注点", html)

    def test_render_evidence_overview_present(self):
        fake_state = {
            "strategy_watch": {"top_focus_items": [{"name": "测试公司", "reason": "测试"}]},
        }
        html = self._render(fake_state)
        self.assertIn("证据概览", html)

    def test_render_missing_evidence_present(self):
        fake_state = {
            "strategy_watch": {"top_focus_items": [{"name": "测试公司", "reason": "测试"}]},
        }
        html = self._render(fake_state)
        self.assertIn("缺失证据", html)

    def test_render_distribution_present(self):
        html = self._render({})
        self.assertIn("覆盖分布", html)

    def test_render_hotzone_present(self):
        fake_state = {
            "strategy_watch": {"top_focus_items": [{"name": "测试公司", "reason": "测试", "priority_label": "高"}]},
        }
        html = self._render(fake_state)
        self.assertIn("优先级热区", html)

    def test_render_disclaimer_present(self):
        html = self._render({})
        self.assertIn("系统展示覆盖状态与证据完整度，不直接给出投资建议", html)

    def test_render_empty_state_text(self):
        html = self._render({})
        self.assertIn("覆盖对象列表", html)

    def test_render_filters_present(self):
        html = self._render({})
        self.assertIn('name="type"', html)
        self.assertIn('name="priority"', html)
        self.assertIn('name="status"', html)
        self.assertIn('name="q"', html)

    def test_render_with_filters(self):
        html = self._render({}, filters={"type": "company", "q": "测试"})
        self.assertIn("覆盖池", html)


class TestOtherPagesStillWork(unittest.TestCase):
    def test_today_overview_still_works(self):
        import run_control_tower as rt

        html = rt.render_today_overview({}, 0)
        self.assertIn("今日总览", html)

    def test_signals_still_works(self):
        import run_control_tower as rt

        html = rt.render_signal_flow({}, 0)
        self.assertIn("信号流", html)

    def test_research_still_works(self):
        import run_control_tower as rt

        html = rt.render_research_queue({}, 0)
        self.assertIn("研究队列", html)

    def test_health_page_placeholder(self):
        import run_control_tower as rt

        html = rt.render_data_health({}, 0)
        self.assertIn("数据健康", html)
        self.assertIn("关键健康问题", html)


class TestPageRenderers(unittest.TestCase):
    def test_five_page_renderers(self):
        import run_control_tower as rt

        self.assertEqual(len(rt.PAGE_RENDERERS), 5)
        paths = set(rt.PAGE_RENDERERS.keys())
        self.assertEqual(paths, {"/", "/coverage", "/signals", "/research", "/health"})


if __name__ == "__main__":
    unittest.main()
