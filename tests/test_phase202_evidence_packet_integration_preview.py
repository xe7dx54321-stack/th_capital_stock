import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase202_evidence_packet_integration_preview import (
    build_phase202_config, build_phase201_loader, build_ticker_evidence_summaries,
    build_evidence_to_claim_map, build_direct_context_policy,
    build_packet_section_preview, build_evidence_packet_preview,
    build_ticker_summary_preview, build_packet_readiness_score,
    build_missing_evidence_report, build_conflict_manual_review_reminder,
    build_300394_packet_preview, build_packet_apply_readiness_gate,
    build_packet_integration_manifest, build_packet_integration_board,
    build_packet_integration_brief, build_backlog_update,
    build_cannot_conclude_guard, build_quality_gate, build_dashboard
)

class TestConfig(unittest.TestCase):
    def test_has_config(self):
        r = build_phase202_config()
        self.assertIn("phase202_config", r)
    def test_preview_only(self):
        r = build_phase202_config()
        self.assertTrue(r["phase202_config"]["preview_only"])
    def test_formal_packet_disabled(self):
        r = build_phase202_config()
        self.assertTrue(r["phase202_config"]["formal_packet_disabled"])
    def test_no_mock(self):
        r = build_phase202_config()
        self.assertFalse(r["phase202_config"]["mock_used"])

class TestLoader(unittest.TestCase):
    def test_loader_loaded(self):
        r = build_phase201_loader()
        self.assertTrue(r["phase202_phase201_loader"]["loaded"])
    def test_loader_count(self):
        r = build_phase201_loader()
        self.assertEqual(r["phase202_phase201_loader"]["clean_evidence_record_count"], 84)
    def test_loader_direct(self):
        r = build_phase201_loader()
        self.assertEqual(r["phase202_phase201_loader"]["direct_evidence_count"], 42)
    def test_loader_context(self):
        r = build_phase201_loader()
        self.assertEqual(r["phase202_phase201_loader"]["context_evidence_count"], 42)

class TestTickerSummaries(unittest.TestCase):
    def test_has_tickers(self):
        r = build_ticker_evidence_summaries()
        self.assertGreater(r["phase202_ticker_evidence_summaries"]["ticker_count"], 0)
    def test_total_mapped(self):
        r = build_ticker_evidence_summaries()
        self.assertEqual(r["phase202_ticker_evidence_summaries"]["total_evidence_mapped"], 84)

class TestClaimMap(unittest.TestCase):
    def test_has_claims(self):
        r = build_evidence_to_claim_map()
        self.assertGreater(r["phase202_evidence_to_claim_map"]["claim_types_count"], 0)
    def test_total_mapped(self):
        r = build_evidence_to_claim_map()
        self.assertEqual(r["phase202_evidence_to_claim_map"]["total_evidence_mapped"], 84)

class TestDirectContextPolicy(unittest.TestCase):
    def test_policy_active(self):
        r = build_direct_context_policy()
        self.assertTrue(r["phase202_direct_context_policy"]["policy_active"])
    def test_context_as_direct_zero(self):
        r = build_direct_context_policy()
        self.assertEqual(r["phase202_direct_context_policy"]["context_as_direct_count"], 0)
    def test_conflict_never_in_evidence(self):
        r = build_direct_context_policy()
        self.assertTrue(r["phase202_direct_context_policy"]["conflict_never_in_evidence_section"])

class TestPacketSectionPreview(unittest.TestCase):
    def test_three_sections(self):
        r = build_packet_section_preview()
        self.assertEqual(r["phase202_packet_section_preview"]["total_sections"], 3)
    def test_preview_only(self):
        r = build_packet_section_preview()
        self.assertTrue(r["phase202_packet_section_preview"]["preview_only"])

class TestEvidencePacketPreview(unittest.TestCase):
    def test_generated(self):
        r = build_evidence_packet_preview()
        self.assertTrue(r["phase202_evidence_packet_preview"]["packet_preview_generated"])
    def test_total(self):
        r = build_evidence_packet_preview()
        self.assertEqual(r["phase202_evidence_packet_preview"]["total_evidence"], 84)
    def test_formal_not_updated(self):
        r = build_evidence_packet_preview()
        self.assertTrue(r["phase202_evidence_packet_preview"]["formal_packet_not_updated"])

class TestReadinessScore(unittest.TestCase):
    def test_has_score(self):
        r = build_packet_readiness_score()
        self.assertIn("score", r["phase202_packet_readiness_score"])
    def test_score_positive(self):
        r = build_packet_readiness_score()
        self.assertGreater(r["phase202_packet_readiness_score"]["score"], 0)
    def test_has_label(self):
        r = build_packet_readiness_score()
        self.assertIn("readiness_label", r["phase202_packet_readiness_score"])

class TestMissingEvidence(unittest.TestCase):
    def test_report_generated(self):
        r = build_missing_evidence_report()
        self.assertTrue(r["phase202_missing_evidence_report"]["report_generated"])

class TestConflictReminder(unittest.TestCase):
    def test_reminder_generated(self):
        r = build_conflict_manual_review_reminder()
        self.assertTrue(r["phase202_conflict_manual_review_reminder"]["reminder_generated"])
    def test_conflict_as_evidence_zero(self):
        r = build_conflict_manual_review_reminder()
        self.assertEqual(r["phase202_conflict_manual_review_reminder"]["conflict_as_evidence_count"], 0)
    def test_needs_review_as_evidence_zero(self):
        r = build_conflict_manual_review_reminder()
        self.assertEqual(r["phase202_conflict_manual_review_reminder"]["needs_review_as_evidence_count"], 0)

class Test300394(unittest.TestCase):
    def test_preview_generated(self):
        r = build_300394_packet_preview()
        self.assertTrue(r["phase202_300394_packet_preview"]["300394_packet_preview_generated"])
    def test_cninfo_retained(self):
        r = build_300394_packet_preview()
        self.assertTrue(r["phase202_300394_packet_preview"]["300394_cninfo_limitation_retained"])

class TestApplyGate(unittest.TestCase):
    def test_gate_generated(self):
        r = build_packet_apply_readiness_gate()
        self.assertTrue(r["phase202_packet_apply_readiness_gate"]["gate_generated"])
    def test_formal_not_updated(self):
        r = build_packet_apply_readiness_gate()
        self.assertTrue(r["phase202_packet_apply_readiness_gate"]["formal_packet_not_updated"])

class TestManifest(unittest.TestCase):
    def test_generated(self):
        r = build_packet_integration_manifest()
        self.assertTrue(r["phase202_packet_integration_manifest"]["manifest_generated"])
    def test_total(self):
        r = build_packet_integration_manifest()
        self.assertEqual(r["phase202_packet_integration_manifest"]["total_evidence_records"], 84)
    def test_preview_only(self):
        r = build_packet_integration_manifest()
        self.assertTrue(r["phase202_packet_integration_manifest"]["preview_only"])

class TestBoard(unittest.TestCase):
    def test_generated(self):
        r = build_packet_integration_board()
        self.assertTrue(r["phase202_packet_integration_board"]["board_generated"])
    def test_not_trade_signal(self):
        r = build_packet_integration_board()
        self.assertTrue(r["phase202_packet_integration_board"]["board_not_trade_signal"])

class TestBrief(unittest.TestCase):
    def test_generated(self):
        r = build_packet_integration_brief()
        self.assertTrue(r["phase202_packet_integration_brief"]["brief_generated"])
    def test_preview_only(self):
        r = build_packet_integration_brief()
        self.assertTrue(r["phase202_packet_integration_brief"]["brief_preview_only"])
    def test_not_trade_advice(self):
        r = build_packet_integration_brief()
        self.assertTrue(r["phase202_packet_integration_brief"]["brief_not_trade_advice"])

class TestBacklog(unittest.TestCase):
    def test_generated(self):
        r = build_backlog_update()
        self.assertTrue(r["phase202_backlog_update"]["backlog_generated"])

class TestGuard(unittest.TestCase):
    def test_pass(self):
        r = build_cannot_conclude_guard()
        self.assertTrue(r["phase202_cannot_conclude_guard"]["guard_pass"])
    def test_violations_zero(self):
        r = build_cannot_conclude_guard()
        self.assertEqual(r["phase202_cannot_conclude_guard"]["violations_count"], 0)

class TestQualityGate(unittest.TestCase):
    def test_pass(self):
        r = build_quality_gate()
        self.assertTrue(r["phase202_quality_gate"]["gate_pass"])
    def test_no_failed_checks(self):
        r = build_quality_gate()
        self.assertEqual(len(r["phase202_quality_gate"]["failed_checks"]), 0)
    def test_formal_not_updated(self):
        r = build_quality_gate()
        self.assertTrue(r["phase202_quality_gate"]["checks"]["formal_packet_not_updated"])

class TestDashboard(unittest.TestCase):
    def test_generated(self):
        r = build_dashboard()
        self.assertTrue(r["phase202_dashboard"]["dashboard_generated"])
    def test_safety_formal_not_updated(self):
        r = build_dashboard()
        self.assertFalse(r["phase202_dashboard"]["safety"]["formal_packet_updated"])
    def test_safety_no_trade(self):
        r = build_dashboard()
        self.assertFalse(r["phase202_dashboard"]["safety"]["trade_recommendation_created"])

if __name__ == '__main__':
    unittest.main()
