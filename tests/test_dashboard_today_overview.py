"""Tests for the Today Overview dashboard page view model and rendering.

Covers:
- build_today_overview_view_model fail-soft with missing data
- metrics 4 cards structure
- top_changes capped at 3
- pending_decisions capped at 3
- no forbidden investment words in rendered HTML
- navigation has exactly 5 business pages
- HTML contains all 5 nav labels
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

from today_overview_view_model import build_today_overview_view_model


FORBIDDEN_WORDS = [
    "target price",
    "目标价",
    "买入",
    "卖出",
    "建仓",
    "仓位建议",
    "position_size",
    "trade_signal",
]

NAV_LABELS = ["今日总览", "覆盖池", "信号流", "研究队列", "数据健康"]


class TestTodayOverviewViewModel(unittest.TestCase):
    def test_empty_state_no_crash(self):
        view = build_today_overview_view_model({})
        self.assertIn("metrics", view)
        self.assertIn("top_changes", view)
        self.assertIn("pending_decisions", view)
        self.assertIn("coverage_moves", view)
        self.assertIn("health_summary", view)
        self.assertIn("updated_at", view)
        self.assertIn("empty_state", view)

    def test_none_state_no_crash(self):
        view = build_today_overview_view_model(None)
        self.assertIsInstance(view, dict)
        self.assertIn("metrics", view)

    def test_metrics_four_cards(self):
        view = build_today_overview_view_model({})
        metrics = view["metrics"]
        self.assertEqual(
            set(metrics.keys()),
            {"important_changes", "pending_decisions", "high_priority_companies", "risk_alerts"},
        )
        for key, card in metrics.items():
            self.assertIn("count", card, f"{key} missing count")
            self.assertIn("subtitle", card, f"{key} missing subtitle")

    def test_top_changes_max_3(self):
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": f"公司{i}", "verdict": "sell", "reason": "测试风险"}
                        for i in range(5)
                    ]
                }
            }
        }
        view = build_today_overview_view_model(fake_state)
        self.assertLessEqual(len(view["top_changes"]), 3)
        for idx, item in enumerate(view["top_changes"]):
            self.assertEqual(item["rank"], idx + 1)

    def test_pending_decisions_max_3(self):
        fake_state = {
            "current_state": {
                "evidence_gaps": [
                    {"entity": f"对象{i}", "gap_type": "缺研报", "description": "测试缺口"}
                    for i in range(5)
                ]
            }
        }
        view = build_today_overview_view_model(fake_state)
        self.assertLessEqual(len(view["pending_decisions"]), 3)

    def test_coverage_moves_has_expected_fields(self):
        view = build_today_overview_view_model({})
        for item in view["coverage_moves"]:
            self.assertIn("company", item)
            self.assertIn("status_label", item)
            self.assertIn("status_tone", item)
            self.assertIn("evidence_pct", item)
            self.assertIn("priority", item)

    def test_health_summary_three_items(self):
        view = build_today_overview_view_model({})
        self.assertEqual(len(view["health_summary"]), 3)
        labels = [h["label"] for h in view["health_summary"]]
        self.assertEqual(labels, ["行情新鲜度", "信息源状态", "Pipeline 状态"])

    def test_updated_at_present(self):
        view = build_today_overview_view_model({})
        self.assertTrue(isinstance(view["updated_at"], str))
        self.assertTrue(len(view["updated_at"]) > 0)


class TestTodayOverviewRendering(unittest.TestCase):
    def _render(self, state: dict | None = None) -> str:
        from run_control_tower import render_today_overview

        state = state or {}
        return render_today_overview(state, refresh_seconds=0)

    def test_render_no_crash_empty_state(self):
        html = self._render({})
        self.assertIn("今日总览", html)
        self.assertIn("今天最值得关注的变化与待判断事项", html)

    def test_render_has_five_nav_items(self):
        html = self._render({})
        for label in NAV_LABELS:
            self.assertIn(label, html, f"nav missing: {label}")

    def test_render_no_forbidden_words(self):
        html = self._render({}).lower()
        for word in FORBIDDEN_WORDS:
            self.assertNotIn(word.lower(), html, f"forbidden word found: {word}")

    def test_render_metric_cards_present(self):
        html = self._render({})
        self.assertIn("今日重点变化", html)
        self.assertIn("待判断事项", html)
        self.assertIn("高优先级公司", html)
        self.assertIn("风险提示", html)

    def test_render_sections_present(self):
        html = self._render({})
        self.assertIn("今日最重要的 3 件事", html)
        self.assertIn("今日待判断", html)
        self.assertIn("覆盖池异动", html)
        self.assertIn("数据健康提醒", html)

    def test_render_empty_state_text(self):
        html = self._render({})
        self.assertIn("暂无今日重点变化", html)


class TestPlaceholderPages(unittest.TestCase):
    def _render_page(self, renderer_name: str, path: str) -> str:
        import run_control_tower as rt

        renderer = getattr(rt, renderer_name)
        return renderer({}, 0)

    def test_coverage_page_placeholder(self):
        html = self._render_page("render_placeholder_coverage", "/coverage")
        self.assertIn("覆盖池", html)
        self.assertIn("页面设计已完成", html)

    def test_signals_page_placeholder(self):
        html = self._render_page("render_placeholder_signals", "/signals")
        self.assertIn("信号流", html)

    def test_research_page_placeholder(self):
        html = self._render_page("render_placeholder_research", "/research")
        self.assertIn("研究队列", html)

    def test_health_page_placeholder(self):
        html = self._render_page("render_placeholder_health", "/health")
        self.assertIn("数据健康", html)

    def test_nav_active_on_each_page(self):
        import run_control_tower as rt

        pairs = [
            ("/coverage", "覆盖池"),
            ("/signals", "信号流"),
            ("/research", "研究队列"),
            ("/health", "数据健康"),
        ]
        for path, label in pairs:
            renderer = rt.PAGE_RENDERERS.get(path)
            self.assertIsNotNone(renderer, f"no renderer for {path}")
            html = renderer({}, 0)
            self.assertIn(label, html)


if __name__ == "__main__":
    unittest.main()
