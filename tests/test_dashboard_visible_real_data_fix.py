"""Tests for visible real data fix in the Dashboard.

Validates that 5 view models correctly read from real data sources
(events.recent_market_events and operations.registry_timeline) instead
of empty fallback fields. Also validates that fake/old health incidents
do not appear as real events, and that empty states render properly
when real data is missing.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "08_scripts" / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


FAKE_HEALTH_INCIDENTS = [
    "某海外数据源",
    "站点A",
    "PDF 抽取失败率升高",
    "失败率达 18%",
    "部分海外站点反爬加强",
    "行情更新延迟（港股）",
    "部分新闻源抓取速率受限",
]


def _build_real_state():
    return {
        "events": {
            "recent_market_events": [
                {
                    "entity_id": "000001.SZ",
                    "event_type": "业绩预告",
                    "title": "平安银行发布2026年中报业绩预告",
                    "description": "净利润同比增长15%，超出市场预期",
                    "source_url": "https://example.com/announcement/001",
                    "source_name": "深交所公告",
                    "source_type": "official_disclosure",
                    "truth_status": "source_backed",
                    "provenance_confidence": "high",
                    "observed_at": "2026-07-07 09:30:00",
                },
                {
                    "entity_id": "600519.SH",
                    "event_type": "股东增持",
                    "title": "贵州茅台控股股东增持",
                    "description": "控股股东增持100万股，彰显信心",
                    "source_url": "https://example.com/announcement/002",
                    "source_name": "上交所公告",
                    "source_type": "official_disclosure",
                    "truth_status": "evidence_backed",
                    "provenance_confidence": "high",
                    "observed_at": "2026-07-07 10:00:00",
                },
                {
                    "entity_id": "AAPL",
                    "event_type": "新品发布",
                    "title": "苹果发布新一代iPhone",
                    "description": "搭载AI芯片，性能提升30%",
                    "source_url": "https://example.com/news/003",
                    "source_name": "科技新闻",
                    "source_type": "news_article",
                    "truth_status": "source_backed",
                    "provenance_confidence": "medium",
                    "observed_at": "2026-07-07 11:00:00",
                },
            ]
        },
        "operations": {
            "registry_timeline": [
                {
                    "entity_id": "000002.SZ",
                    "status": "已加入覆盖池",
                    "action": "add",
                    "description": "新增万科A为覆盖标的",
                    "source_name": "registry_operation",
                    "source_type": "foundation",
                    "truth_status": "source_backed",
                    "provenance_confidence": "high",
                    "updated_at": "2026-07-07 08:00:00",
                },
                {
                    "entity_id": "601318.SH",
                    "status": "因子已更新",
                    "action": "update",
                    "description": "中国平安趋势因子刷新完成",
                    "source_name": "registry_operation",
                    "source_type": "foundation",
                    "truth_status": "source_backed",
                    "provenance_confidence": "high",
                    "updated_at": "2026-07-07 09:00:00",
                },
                {
                    "entity_id": "MSFT",
                    "status": "联动因子已同步",
                    "action": "sync",
                    "description": "微软联动因子数据同步完成",
                    "source_name": "registry_operation",
                    "source_type": "foundation",
                    "truth_status": "source_backed",
                    "provenance_confidence": "high",
                    "updated_at": "2026-07-07 10:30:00",
                },
            ]
        },
        "daily_report": {"highlights": []},
        "risk": {"monitor": {"alerts": []}, "decision": {"sell_candidates": []}},
        "strategy_watch": {"top_focus_items": []},
        "opportunity": {"watchlist_signals": [], "radar": {"markets": []}},
        "market_events": {"upcoming_events": []},
        "current_state": {"evidence_gaps": []},
    }


def _build_empty_state():
    return {
        "events": {"recent_market_events": []},
        "operations": {"registry_timeline": []},
        "daily_report": {"highlights": []},
        "risk": {"monitor": {"alerts": []}, "decision": {"sell_candidates": []}},
        "strategy_watch": {"top_focus_items": []},
        "opportunity": {"watchlist_signals": [], "radar": {"markets": []}},
        "market_events": {"upcoming_events": []},
        "current_state": {"evidence_gaps": []},
    }


def _has_real_item_fields(item: dict) -> bool:
    has_source = any(
        item.get(k) for k in ("source_type", "source_name", "source_label")
    )
    has_time = any(
        item.get(k)
        for k in (
            "observed_at",
            "updated_at",
            "generated_at",
            "latest_update",
            "timestamp",
            "time_label",
        )
    )
    has_truth = any(
        item.get(k) for k in ("truth_status", "data_status", "truth_level")
    )
    has_provenance = any(
        item.get(k)
        for k in (
            "provenance_confidence",
            "confidence",
            "evidence_strength",
            "timestamp_confidence",
            "evidence_completeness",
            "has_source",
            "has_evidence_packet",
            "truth_reason",
        )
    )
    return has_source and has_time and has_truth and has_provenance


class TestTodayOverviewVisibleRealData(unittest.TestCase):
    def test_today_overview_extracts_from_recent_market_events(self):
        from today_overview_view_model import build_today_overview_view_model

        state = _build_real_state()
        view = build_today_overview_view_model(state=state, backend_state={})
        changes = view.get("top_changes", [])
        market_event_titles = [c for c in changes if "业绩预告" in c.get("title", "") or "股东增持" in c.get("title", "")]
        self.assertGreater(len(market_event_titles), 0, "today_overview should extract top changes from recent_market_events")

    def test_today_overview_extracts_from_registry_timeline(self):
        from today_overview_view_model import build_today_overview_view_model

        state = _build_real_state()
        view = build_today_overview_view_model(state=state, backend_state={})
        changes = view.get("top_changes", [])
        registry_items = [
            c for c in changes
            if c.get("source_label") == "registry_operation" or "已加入覆盖池" in c.get("title", "")
        ]
        self.assertGreater(len(registry_items), 0, "today_overview should extract from registry_timeline")

    def test_today_overview_real_items_have_required_fields(self):
        from today_overview_view_model import build_today_overview_view_model

        state = _build_real_state()
        view = build_today_overview_view_model(state=state, backend_state={})
        changes = view.get("top_changes", [])
        real_items = [c for c in changes if c.get("data_status") == "real_snapshot"]
        self.assertGreater(len(real_items), 0)
        for item in real_items[:5]:
            self.assertTrue(
                _has_real_item_fields(item),
                f"real item missing required fields: {item}",
            )

    def test_today_overview_empty_state_no_fake_data(self):
        from today_overview_view_model import build_today_overview_view_model

        state = _build_empty_state()
        view = build_today_overview_view_model(state=state, backend_state={})
        changes = view.get("top_changes", [])
        fake_items = [
            c for c in changes
            if c.get("data_status") not in ("real_snapshot", "empty_state")
            and c.get("truth_status") in ("generated_summary", "default_fallback", "placeholder")
        ]
        self.assertEqual(len(fake_items), 0, "empty state should not show fake generated_summary data")


class TestSignalFlowVisibleRealData(unittest.TestCase):
    def test_signal_flow_extracts_from_recent_market_events(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state = _build_real_state()
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        signals = view.get("signals", [])
        market_event_signals = [s for s in signals if "业绩预告" in s.get("title", "") or "股东增持" in s.get("title", "")]
        self.assertGreater(len(market_event_signals), 0, "signal_flow should extract main signals from recent_market_events")

    def test_signal_flow_extracts_from_registry_timeline(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state = _build_real_state()
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        signals = view.get("signals", [])
        registry_signals = [
            s for s in signals
            if s.get("source_label") == "注册表操作" or "已加入覆盖池" in s.get("title", "")
        ]
        self.assertGreater(len(registry_signals), 0, "signal_flow should extract from registry_timeline")

    def test_signal_flow_real_items_have_required_fields(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state = _build_real_state()
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        signals = view.get("signals", [])
        real_signals = [s for s in signals if s.get("data_status") == "real_snapshot"]
        self.assertGreater(len(real_signals), 0)
        for sig in real_signals[:5]:
            self.assertTrue(
                _has_real_item_fields(sig),
                f"real signal missing required fields: {sig}",
            )

    def test_signal_flow_empty_state_no_fake_data(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state = _build_empty_state()
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        signals = view.get("signals", [])
        fake_signals = [
            s for s in signals
            if s.get("truth_status") in ("generated_summary", "default_fallback", "placeholder")
        ]
        self.assertEqual(len(fake_signals), 0, "empty state should not show fake signals")

    def test_signal_flow_no_generated_summary_in_main_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state = _build_real_state()
        view = build_signal_flow_view_model(state, enable_quality_gate=True)
        signals = view.get("signals", [])
        generated = [s for s in signals if s.get("truth_status") == "generated_summary"]
        self.assertEqual(len(generated), 0, "generated_summary must not enter main signal flow")


class TestResearchQueueVisibleRealData(unittest.TestCase):
    def test_research_queue_extracts_from_recent_market_events(self):
        from research_queue_view_model import build_research_queue_view_model

        state = _build_real_state()
        view = build_research_queue_view_model(state=state, backend_state={})
        queue = view.get("queue", []) + view.get("candidates", []) + view.get("items", [])
        if not queue:
            for key in view:
                if isinstance(view[key], list):
                    queue.extend(view[key])
        market_items = [q for q in queue if isinstance(q, dict) and ("业绩预告" in str(q.get("title", "")) or "新品发布" in str(q.get("title", "")))]
        self.assertGreater(len(market_items), 0, "research_queue should extract from recent_market_events")

    def test_research_queue_extracts_from_registry_timeline(self):
        from research_queue_view_model import build_research_queue_view_model

        state = _build_real_state()
        view = build_research_queue_view_model(state=state, backend_state={})
        all_items = []
        for key in view:
            val = view[key]
            if isinstance(val, list):
                all_items.extend(val)
        registry_items = [
            item for item in all_items
            if isinstance(item, dict) and (
                item.get("source_label") == "registry_operation"
                or "因子已更新" in str(item.get("title", ""))
                or "已加入覆盖池" in str(item.get("title", ""))
            )
        ]
        self.assertGreater(len(registry_items), 0, "research_queue should extract from registry_timeline")

    def test_research_queue_real_items_have_required_fields(self):
        from research_queue_view_model import build_research_queue_view_model

        state = _build_real_state()
        view = build_research_queue_view_model(state=state, backend_state={})
        all_items = []
        for key in view:
            val = view[key]
            if isinstance(val, list):
                all_items.extend(val)
        real_items = [i for i in all_items if isinstance(i, dict) and i.get("data_status") == "real_snapshot"]
        if real_items:
            for item in real_items[:3]:
                self.assertTrue(
                    _has_real_item_fields(item),
                    f"real item missing required fields: {item}",
                )

    def test_research_queue_empty_state_renders(self):
        from research_queue_view_model import build_research_queue_view_model

        state = _build_empty_state()
        view = build_research_queue_view_model(state=state, backend_state={})
        self.assertIsInstance(view, dict)


class TestCoveragePoolVisibleRealData(unittest.TestCase):
    def test_coverage_pool_extracts_from_real_data(self):
        from coverage_pool_view_model import build_coverage_pool_view_model

        state = _build_real_state()
        view = build_coverage_pool_view_model(state=state, backend_state={})
        coverage_items = view.get("coverage_items", [])
        real_items = [i for i in coverage_items if i.get("data_status") == "real_snapshot"]
        self.assertGreater(len(real_items), 0, "coverage_pool should extract coverage objects from real data sources")

    def test_coverage_pool_has_registry_timeline_in_activity(self):
        from coverage_pool_view_model import build_coverage_pool_view_model

        state = _build_real_state()
        view = build_coverage_pool_view_model(state=state, backend_state={})
        all_items = []
        for key in view:
            val = view[key]
            if isinstance(val, list):
                all_items.extend(val)
        registry_related = [
            item for item in all_items
            if isinstance(item, dict) and (
                item.get("source_label") == "registry_operation"
                or "注册表操作" in str(item.get("source_type", ""))
                or "已加入覆盖池" in str(item.get("title", ""))
                or "因子已更新" in str(item.get("title", ""))
            )
        ]
        self.assertGreater(len(registry_related), 0, "coverage_pool should include registry_timeline data")

    def test_coverage_pool_real_items_have_required_fields(self):
        from coverage_pool_view_model import build_coverage_pool_view_model

        state = _build_real_state()
        view = build_coverage_pool_view_model(state=state, backend_state={})
        all_items = []
        for key in view:
            val = view[key]
            if isinstance(val, list):
                all_items.extend(val)
        real_items = [i for i in all_items if isinstance(i, dict) and i.get("data_status") == "real_snapshot"]
        if real_items:
            for item in real_items[:3]:
                self.assertTrue(
                    _has_real_item_fields(item),
                    f"real item missing required fields: {item}",
                )

    def test_coverage_pool_empty_state_renders(self):
        from coverage_pool_view_model import build_coverage_pool_view_model

        state = _build_empty_state()
        view = build_coverage_pool_view_model(state=state, backend_state={})
        self.assertIsInstance(view, dict)


class TestDataHealthVisibleRealData(unittest.TestCase):
    def test_data_health_extracts_from_registry_timeline(self):
        from data_health_view_model import build_data_health_view_model

        state = _build_real_state()
        view = build_data_health_view_model(state=state, backend_state={})
        issues = view.get("health_issues", []) + view.get("issues", []) + view.get("incidents", [])
        if not issues:
            for key in view:
                val = view[key]
                if isinstance(val, list):
                    issues.extend(val)
        registry_issues = [
            issue for issue in issues
            if isinstance(issue, dict) and (
                issue.get("source_label") == "registry_operation"
                or "已加入覆盖池" in str(issue.get("title", ""))
                or "因子已更新" in str(issue.get("title", ""))
            )
        ]
        self.assertGreater(len(registry_issues), 0, "data_health should extract health events from registry_timeline")

    def test_data_health_real_items_have_required_fields(self):
        from data_health_view_model import build_data_health_view_model

        state = _build_real_state()
        view = build_data_health_view_model(state=state, backend_state={})
        all_items = []
        for key in view:
            val = view[key]
            if isinstance(val, list):
                all_items.extend(val)
        real_items = [i for i in all_items if isinstance(i, dict) and i.get("data_status") == "real_snapshot"]
        if real_items:
            for item in real_items[:3]:
                self.assertTrue(
                    _has_real_item_fields(item),
                    f"real item missing required fields: {item}",
                )

    def test_data_health_no_fake_health_incidents(self):
        from data_health_view_model import build_data_health_view_model

        state = _build_real_state()
        view = build_data_health_view_model(state=state, backend_state={})
        all_text = str(view)
        for fake in FAKE_HEALTH_INCIDENTS:
            self.assertNotIn(
                fake,
                all_text,
                f"Fake health incident '{fake}' must not appear in data_health page",
            )

    def test_data_health_empty_state_renders(self):
        from data_health_view_model import build_data_health_view_model

        state = _build_empty_state()
        view = build_data_health_view_model(state=state, backend_state={})
        self.assertIsInstance(view, dict)
        self.assertIn("page_data_status", view)


class TestFakeDataExclusion(unittest.TestCase):
    def test_old_fake_health_incidents_not_in_any_view(self):
        from today_overview_view_model import build_today_overview_view_model
        from signal_flow_view_model import build_signal_flow_view_model
        from research_queue_view_model import build_research_queue_view_model
        from coverage_pool_view_model import build_coverage_pool_view_model
        from data_health_view_model import build_data_health_view_model

        state = _build_real_state()
        views = [
            build_today_overview_view_model(state=state, backend_state={}),
            build_signal_flow_view_model(state, enable_quality_gate=True),
            build_research_queue_view_model(state=state, backend_state={}),
            build_coverage_pool_view_model(state=state, backend_state={}),
            build_data_health_view_model(state=state, backend_state={}),
        ]
        for view in views:
            all_text = str(view)
            for fake in FAKE_HEALTH_INCIDENTS:
                self.assertNotIn(
                    fake,
                    all_text,
                    f"Fake health incident '{fake}' found in view: {list(view.keys())[:5]}",
                )

    def test_generated_summary_not_in_main_signal_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state_with_generated = _build_real_state()
        state_with_generated["daily_report"] = {
            "highlights": [
                {
                    "title": "生成的摘要",
                    "content": "这是生成的摘要内容",
                    "truth_status": "generated_summary",
                    "source_name": "generated",
                }
            ]
        }
        view = build_signal_flow_view_model(state_with_generated, enable_quality_gate=True)
        signals = view.get("signals", [])
        generated = [s for s in signals if s.get("truth_status") == "generated_summary"]
        self.assertEqual(len(generated), 0, "generated_summary must be filtered from main signal flow")

    def test_default_fallback_not_in_main_signal_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state_with_fallback = _build_real_state()
        state_with_fallback["risk"] = {
            "monitor": {"alerts": []},
            "decision": {
                "sell_candidates": [
                    {
                        "title": "默认回退项",
                        "truth_status": "default_fallback",
                        "data_status": "placeholder",
                    }
                ]
            },
        }
        view = build_signal_flow_view_model(state_with_fallback, enable_quality_gate=True)
        signals = view.get("signals", [])
        fallback = [s for s in signals if s.get("truth_status") == "default_fallback"]
        self.assertEqual(len(fallback), 0, "default_fallback must be filtered from main signal flow")

    def test_placeholder_not_in_main_signal_flow(self):
        from signal_flow_view_model import build_signal_flow_view_model

        state_with_placeholder = _build_real_state()
        state_with_placeholder["opportunity"] = {
            "watchlist_signals": [
                {
                    "title": "占位符信号",
                    "truth_status": "placeholder",
                    "data_status": "placeholder",
                }
            ],
            "radar": {"markets": []},
        }
        view = build_signal_flow_view_model(state_with_placeholder, enable_quality_gate=True)
        signals = view.get("signals", [])
        placeholder = [s for s in signals if s.get("truth_status") == "placeholder"]
        self.assertEqual(len(placeholder), 0, "placeholder must be filtered from main signal flow")


if __name__ == "__main__":
    unittest.main()
