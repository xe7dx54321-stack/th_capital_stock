"""Tests for the Data Health dashboard page view model and rendering.

Covers:
- build_data_health_view_model fail-soft with None / {}
- metrics 4 cards structure
- health_issues structure
- module_health structure
- source_status_distribution structure
- run_summary structure
- filters support status / severity / q
- bad filter values don't crash
- /health page HTML contains expected sections
- 5 nav items still present
- other completed pages still work
- forbidden investment words absent
- secret words absent
- data_status field present
- Foundation input flow marked as pending
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

from data_health_view_model import build_data_health_view_model


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

NAV_LABELS = ["今日总览", "覆盖池", "信号流", "研究队列", "数据健康"]


class TestDataHealthViewModel(unittest.TestCase):
    def test_none_state_no_crash(self):
        view = build_data_health_view_model(None)
        self.assertIsInstance(view, dict)
        self.assertIn("data_status", view)
        self.assertIn("metrics", view)
        self.assertIn("health_issues", view)
        self.assertIn("module_health", view)
        self.assertIn("source_status_distribution", view)
        self.assertIn("run_summary", view)
        self.assertIn("empty_state", view)
        self.assertIn("updated_at", view)

    def test_empty_dict_no_crash(self):
        view = build_data_health_view_model({})
        self.assertFalse(view["empty_state"])

    def test_data_status_present(self):
        view = build_data_health_view_model({})
        self.assertEqual(view["data_status"], "lightweight_mapping")

    def test_metrics_four_cards(self):
        view = build_data_health_view_model({})
        m = view["metrics"]
        for key in ["market_freshness", "source_availability", "blocking_issues", "evidence_pipeline"]:
            self.assertIn(key, m, f"missing metric: {key}")

    def test_market_freshness_structure(self):
        view = build_data_health_view_model({})
        m = view["metrics"]["market_freshness"]
        self.assertIn("status", m)
        self.assertIn("subtitle", m)

    def test_source_availability_structure(self):
        view = build_data_health_view_model({})
        m = view["metrics"]["source_availability"]
        self.assertIn("value", m)
        self.assertIn("subtitle", m)

    def test_blocking_issues_structure(self):
        view = build_data_health_view_model({})
        m = view["metrics"]["blocking_issues"]
        self.assertIn("count", m)
        self.assertIn("subtitle", m)

    def test_evidence_pipeline_structure(self):
        view = build_data_health_view_model({})
        m = view["metrics"]["evidence_pipeline"]
        self.assertIn("status", m)
        self.assertIn("subtitle", m)

    def test_health_issues_structure(self):
        view = build_data_health_view_model({})
        issues = view["health_issues"]
        self.assertIsInstance(issues, list)
        if issues:
            issue = issues[0]
            for field in ["severity", "title", "impact_scope", "status", "description", "latest_update", "action_hint", "data_status"]:
                self.assertIn(field, issue, f"missing issue field: {field}")

    def test_module_health_structure(self):
        view = build_data_health_view_model({})
        modules = view["module_health"]
        self.assertIsInstance(modules, list)
        self.assertGreater(len(modules), 0)
        for m in modules:
            for field in ["module_name", "status", "summary", "data_status"]:
                self.assertIn(field, m, f"missing module field: {field}")

    def test_foundation_module_pending(self):
        view = build_data_health_view_model({})
        found = None
        for m in view["module_health"]:
            if "Foundation" in m.get("module_name", ""):
                found = m
                break
        self.assertIsNotNone(found, "Foundation 输入流模块应存在")
        self.assertIn(
            found["status"], ["待接入", "未接入"],
            f"Foundation 输入流应标记为待接入，实际为: {found['status']}"
        )
        self.assertEqual(found["data_status"], "pending_backend_integration")

    def test_source_status_distribution_structure(self):
        view = build_data_health_view_model({})
        dist = view["source_status_distribution"]
        self.assertIsInstance(dist, list)
        for d in dist:
            for field in ["status", "count", "percentage"]:
                self.assertIn(field, d, f"missing dist field: {field}")

    def test_run_summary_structure(self):
        view = build_data_health_view_model({})
        s = view["run_summary"]
        for field in ["successful_batches", "failed_batches", "pending_queue", "last_check"]:
            self.assertIn(field, s, f"missing summary field: {field}")

    def test_filters_status(self):
        view = build_data_health_view_model({}, filters={"status": "降级"})
        self.assertEqual(view["filters"]["status"], "降级")

    def test_filters_severity(self):
        view = build_data_health_view_model({}, filters={"severity": "P1"})
        self.assertEqual(view["filters"]["severity"], "P1")

    def test_filters_keyword(self):
        view = build_data_health_view_model({}, filters={"q": "PDF"})
        self.assertEqual(view["filters"]["q"], "PDF")

    def test_bad_filter_values_no_crash(self):
        bad_filters = {
            "status": "<script>",
            "severity": None,
            "q": 123,
        }
        view = build_data_health_view_model({}, filters=bad_filters)
        self.assertIsInstance(view, dict)


class TestDataHealthRendering(unittest.TestCase):
    def _render(self, state: dict | None = None, filters: dict | None = None) -> str:
        from run_control_tower import render_data_health

        state = state or {}
        return render_data_health(state, refresh_seconds=0, filters=filters)

    def test_render_no_crash(self):
        html = self._render({})
        self.assertIn("数据健康", html)

    def test_render_has_five_nav_items(self):
        html = self._render({})
        for label in NAV_LABELS:
            self.assertIn(label, html, f"nav missing: {label}")

    def test_render_no_forbidden_invest_words(self):
        html = self._render({}).lower()
        for word in FORBIDDEN_INVEST_WORDS:
            self.assertNotIn(word.lower(), html, f"forbidden invest word found: {word}")

    def test_render_no_secret_words(self):
        html = self._render({}).lower()
        for word in FORBIDDEN_SECRET_WORDS:
            self.assertNotIn(word.lower(), html, f"forbidden secret word found: {word}")

    def test_render_has_kpi_cards(self):
        html = self._render({})
        self.assertIn("行情新鲜度", html)
        self.assertIn("信息源可用率", html)
        self.assertIn("关键阻塞问题", html)
        self.assertIn("证据流水线", html)

    def test_render_health_issues_present(self):
        html = self._render({})
        self.assertIn("关键健康问题", html)

    def test_render_module_health_present(self):
        html = self._render({})
        self.assertIn("系统模块健康度", html)

    def test_render_source_distribution_present(self):
        html = self._render({})
        self.assertIn("数据源状态分布", html)

    def test_render_run_summary_present(self):
        html = self._render({})
        self.assertIn("今日运行摘要", html)

    def test_render_disclaimer_present(self):
        html = self._render({})
        self.assertIn(
            "数据健康页面用于观察投研系统的运行状态与数据质量",
            html,
        )
        self.assertIn("不提供任何投资建议", html)

    def test_render_foundation_pending(self):
        html = self._render({})
        self.assertIn("Foundation", html)
        self.assertIn("待接入", html)

    def test_render_with_filters(self):
        html = self._render({}, filters={"status": "降级", "q": "test"})
        self.assertIn("数据健康", html)


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

    def test_coverage_still_works(self):
        import run_control_tower as rt

        html = rt.render_coverage_pool({}, 0)
        self.assertIn("覆盖池", html)


class TestPageRenderers(unittest.TestCase):
    def test_five_page_renderers(self):
        import run_control_tower as rt

        self.assertEqual(len(rt.PAGE_RENDERERS), 5)
        paths = set(rt.PAGE_RENDERERS.keys())
        self.assertEqual(paths, {"/", "/coverage", "/signals", "/research", "/health"})


if __name__ == "__main__":
    unittest.main()
