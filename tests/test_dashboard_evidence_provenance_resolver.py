"""Tests for the Dashboard evidence provenance resolver.

Validates that the evidence_provenance_resolver correctly enriches
data items with provenance fields and assesses confidence levels.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "08_scripts" / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


class TestEvidenceProvenanceResolver(unittest.TestCase):
    def test_resolve_provenance_high_confidence(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试信号",
            "source_name": "官方披露",
            "source_type": "official_disclosure",
            "source_url": "https://example.com/report",
            "evidence_packet_id": "ep_12345",
            "published_at": "2026-07-06 10:00:00",
            "entity": "测试公司",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "high")
        self.assertTrue(result["has_source"])
        self.assertTrue(result["has_evidence_packet"])
        self.assertTrue(result["has_timestamp"])
        self.assertTrue(result["can_enter_main_flow"])

    def test_resolve_provenance_medium_confidence(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试信号",
            "source_name": "策略研究",
            "source_type": "public_research",
            "source_url": "https://example.com/report",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "medium")
        self.assertTrue(result["has_source"])
        self.assertTrue(result["has_evidence_packet"])
        self.assertFalse(result["has_timestamp"])
        self.assertTrue(result["can_enter_main_flow"])

    def test_resolve_provenance_low_confidence(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试信号",
            "source_name": "风险监控",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "low")
        self.assertTrue(result["has_source"])
        self.assertFalse(result["has_evidence_packet"])
        self.assertFalse(result["has_timestamp"])
        self.assertFalse(result["can_enter_main_flow"])

    def test_resolve_provenance_none_confidence(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试信号",
            "summary": "没有任何来源信息",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertFalse(result["has_source"])
        self.assertFalse(result["has_evidence_packet"])
        self.assertFalse(result["has_timestamp"])
        self.assertFalse(result["can_enter_main_flow"])

    def test_generated_summary_no_evidence_gets_none(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "生成式摘要",
            "summary": "这是一个生成的摘要",
            "is_generated_summary": True,
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertTrue(result["is_generated_summary"])
        self.assertFalse(result["can_enter_main_flow"])

    def test_default_fallback_gets_none(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "默认兜底",
            "is_default_fallback": True,
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertTrue(result["is_default_fallback"])
        self.assertFalse(result["can_enter_main_flow"])

    def test_placeholder_gets_none(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "占位数据",
            "is_placeholder": True,
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertTrue(result["is_placeholder"])
        self.assertFalse(result["can_enter_main_flow"])

    def test_data_status_default_fallback(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试",
            "data_status": "default_fallback",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertTrue(result["is_default_fallback"])

    def test_data_status_placeholder(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试",
            "data_status": "placeholder",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertTrue(result["is_placeholder"])

    def test_truth_status_generated_summary(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "测试",
            "truth_status": "generated_summary",
            "source_name": "有来源但是生成的",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "none")
        self.assertTrue(result["is_generated_summary"])

    def test_report_path_counts_as_evidence(self):
        from evidence_provenance_resolver import resolve_provenance
        item = {
            "title": "有报告路径",
            "source_name": "研究部",
            "report_path": "/data/reports/2026/q2/report.pdf",
            "published_at": "2026-06-30",
        }
        result = resolve_provenance(item)
        self.assertEqual(result["provenance_confidence"], "high")
        self.assertTrue(result["has_evidence_packet"])
        self.assertTrue(result["can_enter_main_flow"])

    def test_enrich_with_provenance(self):
        from evidence_provenance_resolver import enrich_with_provenance
        items = [
            {
                "title": "有来源的信号",
                "source_name": "官方披露",
                "source_url": "https://example.com",
                "published_at": "2026-07-06",
            },
            {
                "title": "没有来源的信号",
                "summary": "假数据",
            },
        ]
        enriched = enrich_with_provenance(items)
        self.assertEqual(len(enriched), 2)
        self.assertIn("provenance_confidence", enriched[0])
        self.assertIn("can_enter_main_flow", enriched[0])
        self.assertTrue(enriched[0]["can_enter_main_flow"])
        self.assertFalse(enriched[1]["can_enter_main_flow"])

    def test_filter_main_flow_items(self):
        from evidence_provenance_resolver import filter_main_flow_items
        items = [
            {
                "title": "高可信信号",
                "source_name": "官方披露",
                "source_url": "https://example.com",
                "published_at": "2026-07-06",
            },
            {
                "title": "中可信信号",
                "source_name": "研究部",
                "source_url": "https://example.com/report",
            },
            {
                "title": "低可信信号",
                "source_name": "风险监控",
            },
            {
                "title": "无来源信号",
                "summary": "假的",
            },
        ]
        main_flow = filter_main_flow_items(items)
        self.assertEqual(len(main_flow), 2)
        titles = [item["title"] for item in main_flow]
        self.assertIn("高可信信号", titles)
        self.assertIn("中可信信号", titles)

    def test_summarize_provenance(self):
        from evidence_provenance_resolver import summarize_provenance
        items = [
            {
                "title": "高可信",
                "source_name": "官方披露",
                "source_url": "https://example.com",
                "published_at": "2026-07-06",
            },
            {
                "title": "中可信",
                "source_name": "研究部",
                "source_url": "https://example.com/report",
            },
            {
                "title": "生成式",
                "summary": "生成的摘要",
                "is_generated_summary": True,
            },
            {
                "title": "默认兜底",
                "is_default_fallback": True,
            },
        ]
        summary = summarize_provenance(items)
        self.assertEqual(summary["total_count"], 4)
        self.assertEqual(summary["high_confidence_count"], 1)
        self.assertEqual(summary["medium_confidence_count"], 1)
        self.assertEqual(summary["generated_summary_count"], 1)
        self.assertEqual(summary["default_fallback_count"], 1)
        self.assertEqual(summary["main_flow_eligible_count"], 2)
        self.assertGreater(summary["filtered_out_count"], 0)


class TestProvenanceResolverSafety(unittest.TestCase):
    def test_no_network_access(self):
        import inspect
        import evidence_provenance_resolver
        source = inspect.getsource(evidence_provenance_resolver)
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("http.client", source)

    def test_no_secrets_exposure(self):
        from evidence_provenance_resolver import EVIDENCE_KEYS, SOURCE_KEYS
        all_keys = EVIDENCE_KEYS + SOURCE_KEYS
        self.assertNotIn("api_key", all_keys)
        self.assertNotIn("secret", all_keys)
        self.assertNotIn("password", all_keys)
        self.assertNotIn("token", all_keys)

    def test_no_file_writes(self):
        import inspect
        import evidence_provenance_resolver
        source = inspect.getsource(evidence_provenance_resolver)
        self.assertNotIn("open(", source)
        self.assertNotIn("write(", source)


if __name__ == "__main__":
    unittest.main()
