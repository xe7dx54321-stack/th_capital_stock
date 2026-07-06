"""Tests for the Research Queue dashboard page view model and rendering.

Covers:
- build_research_queue_view_model fail-soft with None / {}
- metrics 4 cards structure
- queue_items capped at 20
- selected_detail structure
- evidence_gaps structure
- filters support priority / status / sort / q
- bad filter values don't crash
- /research page HTML contains expected sections
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

from research_queue_view_model import build_research_queue_view_model


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


class TestResearchQueueViewModel(unittest.TestCase):
    def test_none_state_no_crash(self):
        view = build_research_queue_view_model(None)
        self.assertIsInstance(view, dict)
        self.assertIn("data_status", view)
        self.assertIn("metrics", view)
        self.assertIn("filters", view)
        self.assertIn("queue_items", view)
        self.assertIn("selected_detail", view)
        self.assertIn("evidence_gaps", view)
        self.assertIn("empty_state", view)
        self.assertIn("updated_at", view)

    def test_empty_dict_no_crash(self):
        view = build_research_queue_view_model({})
        self.assertTrue(view["empty_state"])
        self.assertEqual(view["metrics"]["research_topic_count"]["count"], 0)

    def test_data_status_present(self):
        view = build_research_queue_view_model({})
        self.assertEqual(view["data_status"], "lightweight_mapping")
        self.assertIn("data_status", view["selected_detail"])

    def test_metrics_four_cards(self):
        view = build_research_queue_view_model({})
        m = view["metrics"]
        for key in ["research_topic_count", "high_priority_count", "evidence_gap_count", "new_today_count"]:
            self.assertIn(key, m, f"missing metric: {key}")
            self.assertIn("count", m[key])
            self.assertIn("subtitle", m[key])
            self.assertIsInstance(m[key]["count"], int)

    def test_queue_items_default_max_20(self):
        fake_state = {
            "current_state": {
                "evidence_gaps": [{"entity": f"公司{i}", "gap_type": "测试"} for i in range(30)]
            }
        }
        view = build_research_queue_view_model(fake_state, limit=20)
        self.assertLessEqual(len(view["queue_items"]), 20)

    def test_selected_detail_structure(self):
        view = build_research_queue_view_model({})
        d = view["selected_detail"]
        for field in [
            "title", "related_entities", "related_topics", "priority",
            "research_hypothesis", "existing_evidence", "missing_evidence",
            "next_steps", "risk_flags", "data_status",
        ]:
            self.assertIn(field, d, f"missing field: {field}")

    def test_evidence_gaps_structure(self):
        view = build_research_queue_view_model({})
        gaps = view["evidence_gaps"]
        self.assertIsInstance(gaps, list)
        if gaps:
            for g in gaps:
                for field in ["gap_title", "importance", "target_source", "expected_time", "status"]:
                    self.assertIn(field, g, f"missing gap field: {field}")

    def test_filters_priority(self):
        view = build_research_queue_view_model({}, filters={"priority": "高"})
        self.assertEqual(view["filters"]["priority"], "高")

    def test_filters_status(self):
        view = build_research_queue_view_model({}, filters={"status": "待验证"})
        self.assertEqual(view["filters"]["status"], "待验证")

    def test_filters_sort(self):
        view = build_research_queue_view_model({}, filters={"sort": "priority"})
        self.assertEqual(view["filters"]["sort"], "priority")

    def test_filters_keyword(self):
        view = build_research_queue_view_model({}, filters={"q": "英伟达"})
        self.assertEqual(view["filters"]["q"], "英伟达")

    def test_bad_filter_values_no_crash(self):
        bad_filters = {
            "priority": "<script>",
            "status": None,
            "sort": 123,
            "q": "<b>xss</b>",
        }
        view = build_research_queue_view_model({}, filters=bad_filters)
        self.assertIsInstance(view, dict)

    def test_queue_item_structure(self):
        fake_state = {
            "current_state": {"evidence_gaps": [{"entity": "测试", "gap_type": "测试"}]},
            "strategy_watch": {"top_focus_items": [{"name": "测试公司", "reason": "测试"}]},
        }
        view = build_research_queue_view_model(fake_state)
        if view["queue_items"]:
            item = view["queue_items"][0]
            for field in [
                "item_id", "rank", "title", "related_entities", "related_topics",
                "priority", "status", "evidence_count", "gap_count",
                "updated_at", "short_reason", "data_status",
            ]:
                self.assertIn(field, item, f"missing item field: {field}")


class TestResearchQueueRendering(unittest.TestCase):
    def _render(self, state: dict | None = None, filters: dict | None = None) -> str:
        from run_control_tower import render_research_queue

        state = state or {}
        return render_research_queue(state, refresh_seconds=0, filters=filters)

    def test_render_no_crash_empty_state(self):
        html = self._render({})
        self.assertIn("研究队列", html)

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
        self.assertIn("待深挖研究主题", html)
        self.assertIn("高优先级事项", html)
        self.assertIn("待补证据事项", html)
        self.assertIn("今日新增", html)

    def test_render_research_list_present(self):
        html = self._render({})
        self.assertIn("研究队列", html)

    def test_render_research_detail_present(self):
        html = self._render({})
        self.assertIn("研究详情", html)

    def test_render_evidence_gaps_present(self):
        html = self._render({})
        self.assertIn("证据缺口", html)

    def test_render_disclaimer_present(self):
        html = self._render({})
        self.assertIn("系统仅组织研究证据与待办，不直接给出投资建议", html)

    def test_render_empty_state_text(self):
        html = self._render({})
        self.assertIn("暂无研究队列", html)

    def test_render_action_buttons_present(self):
        fake_state = {
            "current_state": {"evidence_gaps": [{"entity": "测试公司", "gap_type": "测试"}]},
            "strategy_watch": {"top_focus_items": [{"name": "测试公司", "reason": "测试"}]},
        }
        html = self._render(fake_state)
        self.assertIn("通过", html)
        self.assertIn("补证据", html)
        self.assertIn("暂缓", html)
        self.assertIn("驳回", html)

    def test_render_filters_present(self):
        html = self._render({})
        self.assertIn('name="priority"', html)
        self.assertIn('name="status"', html)
        self.assertIn('name="sort"', html)
        self.assertIn("全部", html)


class TestOtherPagesStillWork(unittest.TestCase):
    def test_today_overview_still_works(self):
        import run_control_tower as rt

        html = rt.render_today_overview({}, 0)
        self.assertIn("今日总览", html)

    def test_signals_still_works(self):
        import run_control_tower as rt

        html = rt.render_signal_flow({}, 0)
        self.assertIn("信号流", html)

    def test_coverage_placeholder(self):
        import run_control_tower as rt

        html = rt.render_placeholder_coverage({}, 0)
        self.assertIn("覆盖池", html)

    def test_health_placeholder(self):
        import run_control_tower as rt

        html = rt.render_placeholder_health({}, 0)
        self.assertIn("数据健康", html)


class TestPageRenderers(unittest.TestCase):
    def test_five_page_renderers(self):
        import run_control_tower as rt

        self.assertEqual(len(rt.PAGE_RENDERERS), 5)
        paths = set(rt.PAGE_RENDERERS.keys())
        self.assertEqual(paths, {"/", "/coverage", "/signals", "/research", "/health"})


if __name__ == "__main__":
    unittest.main()
