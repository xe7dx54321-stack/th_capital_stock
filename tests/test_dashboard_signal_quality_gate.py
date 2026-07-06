"""Tests for signal quality gate in signal flow view model."""

import os
import sys
import unittest
from datetime import datetime

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
from signal_flow_view_model import build_signal_flow_view_model


class TestSignalQualityGate(unittest.TestCase):
    def test_generated_summary_blocked(self):
        """Generated summary without evidence should NOT enter main signal flow."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {
                            "name": "易点天下",
                            "summary": "卖出优先级已经足够高，应该先处理风险，再谈进攻。",
                            "verdict": "sell",
                        }
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        # Main signal flow should be empty or contain only filtered signals
        self.assertEqual(len(view["signals"]), 0)
        self.assertGreater(view["summary"]["filtered_signal_count"], 0)

    def test_mechanical_timestamp_blocked(self):
        """Signals with mechanical timestamps should NOT enter main signal flow."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {
                            "name": "新雷能",
                            "summary": "还没到必须清仓，但更适合先做减仓或降权。",
                            "verdict": "trim",
                        }
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertEqual(len(view["signals"]), 0)
        self.assertGreater(view["summary"]["filtered_signal_count"], 0)

    def test_default_fallback_blocked(self):
        """Default fallback signals should NOT enter main signal flow."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {
                            "name": "阿里巴巴-W",
                            "summary": "暂无原文 / 暂无证据包",
                        }
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertEqual(len(view["signals"]), 0)
        self.assertGreater(view["summary"]["filtered_signal_count"], 0)

    def test_placeholder_blocked(self):
        """Placeholder signals should NOT enter main signal flow."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {
                            "name": "示例标的",
                            "data_status": "placeholder",
                            "summary": "待接入 Foundation 证据流",
                        }
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertEqual(len(view["signals"]), 0)
        self.assertGreater(view["summary"]["filtered_signal_count"], 0)

    def test_evidence_backed_real_allowed(self):
        """Evidence-backed real signals should enter main signal flow."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {
                            "name": "真实风险标的",
                            "source_url": "https://example.com/report.pdf",
                            "published_at": "2026-07-06 10:00:00",
                            "evidence_packet_id": "ev_001",
                        }
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertGreater(len(view["signals"]), 0)
        self.assertEqual(view["summary"]["filtered_signal_count"], 0)

    def test_real_snapshot_with_source_allowed(self):
        """Real snapshot with source should enter main signal flow."""
        fake_state = {
            "strategy_watch": {
                "top_focus_items": [
                    {
                        "name": "关注标的A",
                        "source_name": "eastmoney",
                        "source_type": "public_research",
                    }
                ]
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertGreater(len(view["signals"]), 0)

    def test_real_snapshot_no_evidence_blocked_by_default(self):
        """Real snapshot without evidence should NOT enter main signal flow by default."""
        fake_state = {
            "opportunity": {
                "markets": {
                    "A股": [
                        {
                            "name": "机会标的",
                            "summary": "估值修复机会",
                        }
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        # Should be filtered
        self.assertEqual(len(view["signals"]), 0)

    def test_real_snapshot_no_evidence_allowed_with_flag(self):
        """Real snapshot without evidence can be allowed with include_low_confidence flag."""
        fake_item = {
            "name": "机会标的",
            "created_at": "2026-07-06 10:00:00",
        }
        result = classify_data_truth(fake_item)
        self.assertTrue(should_enter_main_signal_flow(fake_item, include_low_confidence=True))

    def test_filtered_signal_count_increases(self):
        """filtered_signal_count should correctly increase."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "标的A", "summary": "风险提示"},
                        {"name": "标的B", "summary": "风险提示"},
                        {"name": "标的C", "summary": "风险提示"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertEqual(view["summary"]["filtered_signal_count"], 3)

    def test_low_confidence_candidate_count_increases(self):
        """low_confidence_candidate_count should correctly increase."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "标的A", "summary": "风险提示"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        self.assertGreater(view["summary"]["low_confidence_candidate_count"], 0)

    def test_signals_contain_truth_status(self):
        """All signals should contain truth_status field."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "标的A", "source_url": "https://example.com"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        for signal in view["signals"]:
            self.assertIn("truth_status", signal)

    def test_signals_contain_truth_reason(self):
        """All signals should contain truth_reason field."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "标的A", "source_url": "https://example.com"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        for signal in view["signals"]:
            self.assertIn("truth_reason", signal)

    def test_signals_contain_has_source(self):
        """All signals should contain has_source field."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "标的A", "source_url": "https://example.com"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        for signal in view["signals"]:
            self.assertIn("has_source", signal)

    def test_signals_contain_has_evidence_packet(self):
        """All signals should contain has_evidence_packet field."""
        fake_state = {
            "risk": {
                "decision": {
                    "sell_candidates": [
                        {"name": "标的A", "source_url": "https://example.com"},
                    ]
                }
            }
        }
        view = build_signal_flow_view_model(fake_state, enable_quality_gate=True)
        for signal in view["signals"]:
            self.assertIn("has_evidence_packet", signal)


class TestForbiddenTemplatesBlocked(unittest.TestCase):
    def test_sell_template_blocked(self):
        """'卖出优先级已经足够高...' template should be blocked."""
        item = {
            "summary": "卖出优先级已经足够高，应该先处理风险，再谈进攻。",
            "verdict": "sell",
        }
        classification = classify_data_truth(item)
        self.assertEqual(classification["truth_status"], DataTruthStatus.GENERATED_SUMMARY.value)
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_trim_template_blocked(self):
        """'还没到必须清仓...' template should be blocked."""
        item = {
            "summary": "还没到必须清仓，但更适合先做减仓或降权。",
            "verdict": "trim",
        }
        classification = classify_data_truth(item)
        self.assertEqual(classification["truth_status"], DataTruthStatus.GENERATED_SUMMARY.value)
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_watch_template_blocked(self):
        """'先盯紧，不急着做大动作...' template should be blocked."""
        item = {
            "summary": "先盯紧，不急着做大动作。",
            "verdict": "watch",
        }
        classification = classify_data_truth(item)
        self.assertEqual(classification["truth_status"], DataTruthStatus.GENERATED_SUMMARY.value)
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_hold_template_blocked(self):
        """'当前没有足够强的卖出信号...' template should be blocked."""
        item = {
            "summary": "当前没有足够强的卖出信号。",
            "verdict": "hold",
        }
        classification = classify_data_truth(item)
        self.assertEqual(classification["truth_status"], DataTruthStatus.GENERATED_SUMMARY.value)
        self.assertFalse(should_enter_main_signal_flow(item))


class TestNoEvidenceNoSourceBlocked(unittest.TestCase):
    def test_no_evidence_no_source_blocked(self):
        """Signals without evidence and source should be blocked."""
        item = {
            "name": "Unknown signal",
        }
        classification = classify_data_truth(item)
        self.assertEqual(classification["truth_status"], DataTruthStatus.UNKNOWN.value)
        self.assertFalse(should_enter_main_signal_flow(item))

    def test_evidence_gap_blocked(self):
        """Evidence gap signals should be blocked."""
        item = {
            "name": "Evidence gap item",
            "gap_type": "证据缺口",
            "description": "存在证据缺口，需要补充",
        }
        classification = classify_data_truth(item)
        # Evidence gaps should not enter main signal flow
        self.assertFalse(should_enter_main_signal_flow(item))


if __name__ == "__main__":
    unittest.main()