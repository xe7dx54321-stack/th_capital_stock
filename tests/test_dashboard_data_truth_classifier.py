"""Tests for data truth classifier."""

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

from data_truth_classifier import (
    DataTruthStatus,
    classify_data_truth,
    should_enter_main_signal_flow,
)


class TestDataTruthClassifier(unittest.TestCase):
    def test_evidence_backed_real(self):
        item = {
            "source_url": "https://example.com/report.pdf",
            "published_at": "2026-07-01 10:00:00",
            "title": "Company X earnings report",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.EVIDENCE_BACKED_REAL.value)
        self.assertTrue(result["has_source"])
        self.assertTrue(result["has_evidence_packet"])
        self.assertFalse(result["is_generated_summary"])
        self.assertFalse(result["is_default_fallback"])

    def test_real_snapshot_with_source(self):
        item = {
            "source_name": "eastmoney",
            "source_type": "public_research",
            "published_at": "2026-07-01 10:00:00",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.REAL_SNAPSHOT_WITH_SOURCE.value)
        self.assertTrue(result["has_source"])
        self.assertFalse(result["has_evidence_packet"])

    def test_real_snapshot_no_evidence(self):
        item = {
            "created_at": "2026-07-01 10:00:00",
            "title": "Market update",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.REAL_SNAPSHOT_NO_EVIDENCE.value)

    def test_generated_summary(self):
        item = {
            "summary": "卖出优先级已经足够高，应该先处理风险，再谈进攻。",
            "verdict": "sell",
            "reason": "估值压力偏高",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.GENERATED_SUMMARY.value)
        self.assertTrue(result["is_generated_summary"])

    def test_default_fallback(self):
        item = {
            "title": "风险提示",
            "summary": "暂无原文 / 暂无证据包",
            "review_status": "待复核",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.DEFAULT_FALLBACK.value)
        self.assertTrue(result["is_default_fallback"])

    def test_placeholder(self):
        item = {
            "title": "示例信号",
            "summary": "待接入 Foundation 证据流",
            "data_status": "placeholder",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.PLACEHOLDER.value)

    def test_historical_residual(self):
        item = {
            "source": "build_historical_dump.py",
            "entity_id": "historical_2025Q1_backup",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.HISTORICAL_RESIDUAL.value)

    def test_unknown(self):
        item = {
            "name": "Unknown item",
        }
        result = classify_data_truth(item)
        self.assertEqual(result["truth_status"], DataTruthStatus.UNKNOWN.value)


class TestSignalQualityGate(unittest.TestCase):
    def test_evidence_backed_real_allowed(self):
        item = {
            "source_url": "https://example.com/report.pdf",
            "published_at": "2026-07-01 10:00:00",
        }
        self.assertTrue(should_enter_main_signal_flow(item))

    def test_real_snapshot_with_source_allowed(self):
        item = {
            "source_name": "eastmoney",
            "source_type": "public_research",
        }
        self.assertTrue(should_enter_main_signal_flow(item))

    def test_generated_summary_not_allowed(self):
        item = {
            "summary": "还没到必须清仓，但更适合先做减仓或降权。",
            "verdict": "trim",
        }
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_default_fallback_not_allowed(self):
        item = {
            "summary": "暂无原文 / 暂无证据包",
        }
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_placeholder_not_allowed(self):
        item = {
            "title": "示例信号",
            "data_status": "placeholder",
        }
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_historical_residual_not_allowed(self):
        item = {
            "source": "build_legacy_dump.py",
        }
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_real_snapshot_no_evidence_not_allowed_by_default(self):
        item = {
            "created_at": "2026-07-01 10:00:00",
        }
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_real_snapshot_no_evidence_allowed_with_flag(self):
        item = {
            "created_at": "2026-07-01 10:00:00",
        }
        self.assertTrue(should_enter_main_signal_flow(item, include_low_confidence=True))


if __name__ == "__main__":
    unittest.main()
