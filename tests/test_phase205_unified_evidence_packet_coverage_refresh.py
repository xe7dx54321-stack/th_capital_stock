import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase205_unified_evidence_packet_coverage_refresh import *

class TestConfig(unittest.TestCase):
    def test_has(self): r = build_phase205_config(); self.assertIn("phase205_config", r)
    def test_universe(self): r = build_phase205_config(); self.assertEqual(r["phase205_config"]["universe_ticker_count"], 8)
    def test_preview(self): r = build_phase205_config(); self.assertTrue(r["phase205_config"]["preview_only"])
    def test_no_mock(self): r = build_phase205_config(); self.assertFalse(r["phase205_config"]["mock_used"])

class TestPhase201Loader(unittest.TestCase):
    def test_loaded(self): r = build_phase201_loader(); self.assertTrue(r["phase205_phase201_loader"]["loaded"])
    def test_total(self): r = build_phase201_loader(); self.assertEqual(r["phase205_phase201_loader"]["cn_a_total"], 84)

class TestPhase204Loader(unittest.TestCase):
    def test_loaded(self): r = build_phase204_loader(); self.assertTrue(r["phase205_phase204_loader"]["loaded"])
    def test_total(self): r = build_phase204_loader(); self.assertEqual(r["phase205_phase204_loader"]["hk_us_total"], 20)

class TestUnifiedLoader(unittest.TestCase):
    def test_loaded(self): r = build_unified_evidence_loader(); self.assertTrue(r["phase205_unified_evidence_loader"]["unified_loaded"])
    def test_total(self): r = build_unified_evidence_loader(); self.assertEqual(r["phase205_unified_evidence_loader"]["total_evidence_records"], 104)
    def test_direct(self): r = build_unified_evidence_loader(); self.assertEqual(r["phase205_unified_evidence_loader"]["direct_evidence_count"], 54)
    def test_context(self): r = build_unified_evidence_loader(); self.assertEqual(r["phase205_unified_evidence_loader"]["context_evidence_count"], 50)
    def test_no_dupes(self): r = build_unified_evidence_loader(); self.assertEqual(r["phase205_unified_evidence_loader"]["duplicate_evidence_count"], 0)

class TestTickerCoverage(unittest.TestCase):
    def test_count(self): r = build_ticker_coverage_board(); self.assertEqual(r["phase205_ticker_coverage_board"]["ticker_count"], 8)
    def test_covered(self): r = build_ticker_coverage_board(); self.assertEqual(r["phase205_ticker_coverage_board"]["covered_count"], 7)
    def test_blocked(self): r = build_ticker_coverage_board(); self.assertEqual(r["phase205_ticker_coverage_board"]["blocked_count"], 1)

class TestMarketMatrix(unittest.TestCase):
    def test_count(self): r = build_market_matrix(); self.assertEqual(r["phase205_market_matrix"]["market_count"], 3)
    def test_all_markets(self):
        r = build_market_matrix()
        for m in ["CN_A","HK","US"]:
            self.assertIn(m, r["phase205_market_matrix"]["markets"])

class TestClaimMapRefresh(unittest.TestCase):
    def test_generated(self): r = build_evidence_to_claim_map_refresh(); self.assertGreater(r["phase205_evidence_to_claim_map_refresh"]["claim_type_count"], 0)

class TestSectionPreview(unittest.TestCase):
    def test_sections(self): r = build_packet_section_preview_refresh(); self.assertEqual(r["phase205_packet_section_preview_refresh"]["total_sections"], 3)

class TestEvidencePacketPreview(unittest.TestCase):
    def test_generated(self): r = build_evidence_packet_preview_refresh(); self.assertTrue(r["phase205_evidence_packet_preview_refresh"]["packet_preview_generated"])
    def test_total(self): r = build_evidence_packet_preview_refresh(); self.assertEqual(r["phase205_evidence_packet_preview_refresh"]["total_evidence"], 104)

class TestReadiness(unittest.TestCase):
    def test_generated(self): r = build_packet_readiness_recalculation(); self.assertTrue(r["phase205_packet_readiness_recalculation"]["readiness_recalculated"])
    def test_score(self): r = build_packet_readiness_recalculation(); self.assertGreaterEqual(r["phase205_packet_readiness_recalculation"]["score"], 80)
    def test_ready(self): r = build_packet_readiness_recalculation(); self.assertTrue(r["phase205_packet_readiness_recalculation"]["ready_for_formal_packet"])

class TestGapCloseout(unittest.TestCase):
    def test_generated(self): r = build_remaining_gap_closeout(); self.assertTrue(r["phase205_remaining_gap_closeout"]["gap_closeout_generated"])
    def test_300394_gap(self): r = build_remaining_gap_closeout(); self.assertEqual(r["phase205_remaining_gap_closeout"]["remaining_gap"], "300394.SZ")
    def test_cninfo_retained(self): r = build_remaining_gap_closeout(); self.assertTrue(r["phase205_remaining_gap_closeout"]["300394_cninfo_limitation_retained"])
    def test_not_resolved(self): r = build_remaining_gap_closeout(); self.assertTrue(r["phase205_remaining_gap_closeout"]["300394_not_cninfo_resolved"])

class TestManualReview(unittest.TestCase):
    def test_generated(self): r = build_manual_review_reminder(); self.assertTrue(r["phase205_manual_review_reminder"]["reminder_generated"])
    def test_queue(self): r = build_manual_review_reminder(); self.assertEqual(r["phase205_manual_review_reminder"]["manual_review_queue_retained"], 63)

class Test300394sReport(unittest.TestCase):
    def test_generated(self): r = build_300394_source_limitation_report(); self.assertTrue(r["phase205_300394_source_limitation_report"]["report_generated"])
    def test_cninfo(self): r = build_300394_source_limitation_report(); self.assertTrue(r["phase205_300394_source_limitation_report"]["300394_cninfo_limitation_retained"])

class TestAdditiveAudit(unittest.TestCase):
    def test_not_replacement(self): r = build_additive_source_audit_v3(); self.assertFalse(r["phase205_additive_source_audit_v3"]["ifind_replacement_detected"])
    def test_sources_ok(self): r = build_additive_source_audit_v3(); self.assertTrue(r["phase205_additive_source_audit_v3"]["existing_sources_preserved"])

class TestApplyGate(unittest.TestCase):
    def test_generated(self): r = build_formal_apply_gate_preview(); self.assertTrue(r["phase205_formal_apply_gate_preview"]["gate_preview_generated"])
    def test_not_allowed(self): r = build_formal_apply_gate_preview(); self.assertFalse(r["phase205_formal_apply_gate_preview"]["formal_apply_allowed"])
    def test_not_executed(self): r = build_formal_apply_gate_preview(); self.assertFalse(r["phase205_formal_apply_gate_preview"]["formal_apply_executed"])

class TestApplyPackage(unittest.TestCase):
    def test_generated(self): r = build_apply_package_preview(); self.assertTrue(r["phase205_apply_package_preview"]["apply_package_generated"])

class TestRollback(unittest.TestCase):
    def test_generated(self): r = build_rollback_requirement_preview(); self.assertTrue(r["phase205_rollback_requirement_preview"]["rollback_preview_generated"])

class TestChecklist(unittest.TestCase):
    def test_generated(self): r = build_post_apply_checklist_preview(); self.assertTrue(r["phase205_post_apply_checklist_preview"]["checklist_generated"])

class TestBoard(unittest.TestCase):
    def test_generated(self): r = build_unified_board(); self.assertTrue(r["phase205_unified_board"]["board_generated"])

class TestBrief(unittest.TestCase):
    def test_generated(self): r = build_unified_brief(); self.assertTrue(r["phase205_unified_brief"]["brief_generated"])

class TestBacklog(unittest.TestCase):
    def test_generated(self): r = build_backlog_update(); self.assertTrue(r["phase205_backlog_update"]["backlog_generated"])

class TestGuard(unittest.TestCase):
    def test_pass(self): r = build_cannot_conclude_guard(); self.assertTrue(r["phase205_cannot_conclude_guard"]["guard_pass"])
    def test_zero(self): r = build_cannot_conclude_guard(); self.assertEqual(r["phase205_cannot_conclude_guard"]["violations_count"], 0)

class TestQualityGate(unittest.TestCase):
    def test_pass(self): r = build_quality_gate(); self.assertTrue(r["phase205_quality_gate"]["gate_pass"])
    def test_no_failed(self): r = build_quality_gate(); self.assertEqual(len(r["phase205_quality_gate"]["failed_checks"]), 0)

class TestDashboard(unittest.TestCase):
    def test_generated(self): r = build_dashboard(); self.assertTrue(r["phase205_dashboard"]["dashboard_generated"])
    def test_no_trade(self): r = build_dashboard(); self.assertFalse(r["phase205_dashboard"]["safety"]["trade_recommendation_created"])

if __name__ == '__main__':
    unittest.main()
