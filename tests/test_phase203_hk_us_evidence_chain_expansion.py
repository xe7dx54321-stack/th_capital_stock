import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase203_hk_us_evidence_chain_expansion import *

class TestConfig(unittest.TestCase):
    def test_has_config(self):
        r = build_phase203_config()
        self.assertIn("phase203_config", r)
    def test_ticker_count(self):
        r = build_phase203_config()
        self.assertEqual(r["phase203_config"]["target_ticker_count"], 4)
    def test_preview_only(self):
        r = build_phase203_config()
        self.assertTrue(r["phase203_config"]["preview_only"])
    def test_no_mock(self):
        r = build_phase203_config()
        self.assertFalse(r["phase203_config"]["mock_used"])

class TestCoverageGap(unittest.TestCase):
    def test_gap_loaded(self):
        r = build_phase202_coverage_gap()
        self.assertTrue(r["phase203_phase202_coverage_gap"]["gap_loaded"])
    def test_missing_count(self):
        r = build_phase202_coverage_gap()
        self.assertEqual(r["phase203_phase202_coverage_gap"]["missing_ticker_count"], 4)
    def test_hk_count(self):
        r = build_phase202_coverage_gap()
        self.assertEqual(r["phase203_phase202_coverage_gap"]["hk_missing"], 2)
    def test_us_count(self):
        r = build_phase202_coverage_gap()
        self.assertEqual(r["phase203_phase202_coverage_gap"]["us_missing"], 2)

class TestAdditiveAudit(unittest.TestCase):
    def test_audit_generated(self):
        r = build_additive_source_audit()
        self.assertTrue(r["phase203_additive_source_audit"]["audit_generated"])
    def test_ifind_not_replacement(self):
        r = build_additive_source_audit()
        self.assertFalse(r["phase203_additive_source_audit"]["ifind_replacement_detected"])
    def test_sources_preserved(self):
        r = build_additive_source_audit()
        self.assertTrue(r["phase203_additive_source_audit"]["existing_sources_preserved"])
    def test_adapters_preserved(self):
        r = build_additive_source_audit()
        self.assertTrue(r["phase203_additive_source_audit"]["existing_adapters_preserved"])
    def test_no_source_deleted(self):
        r = build_additive_source_audit()
        self.assertTrue(r["phase203_additive_source_audit"]["no_source_deleted"])
    def test_no_adapter_disabled(self):
        r = build_additive_source_audit()
        self.assertTrue(r["phase203_additive_source_audit"]["no_adapter_disabled"])

class TestSourceRegistry(unittest.TestCase):
    def test_registry_count(self):
        r = build_hk_us_source_registry()
        self.assertEqual(r["phase203_hk_us_source_registry"]["ticker_count"], 4)
    def test_hk_us_count(self):
        r = build_hk_us_source_registry()
        self.assertEqual(r["phase203_hk_us_source_registry"]["hk_count"], 2)
        self.assertEqual(r["phase203_hk_us_source_registry"]["us_count"], 2)
    def test_ifind_additive(self):
        r = build_hk_us_source_registry()
        self.assertEqual(r["phase203_hk_us_source_registry"]["ifind_role"], "additive_never_sole_source")

class TestRoutePlan(unittest.TestCase):
    def test_route_count(self):
        r = build_hk_us_route_plan()
        self.assertEqual(r["phase203_hk_us_route_plan"]["route_count"], 4)
    def test_hk_routes(self):
        r = build_hk_us_route_plan()
        self.assertEqual(r["phase203_hk_us_route_plan"]["hk_routes"], 2)

class TestSourceLeads(unittest.TestCase):
    def test_lead_count(self):
        r = build_hk_us_source_leads()
        self.assertEqual(r["phase203_hk_us_source_leads"]["source_lead_count"], 4)
    def test_all_deferred(self):
        r = build_hk_us_source_leads()
        self.assertTrue(r["phase203_hk_us_source_leads"]["all_deferred_to_phase204"])
    def test_no_fetch(self):
        r = build_hk_us_source_leads()
        self.assertEqual(r["phase203_hk_us_source_leads"]["fetch_attempt_count"], 0)

class TestDirtyItems(unittest.TestCase):
    def test_count(self):
        r = build_hk_us_dirty_items()
        self.assertEqual(r["phase203_hk_us_dirty_items"]["dirty_item_count"], 4)
    def test_metadata_only(self):
        r = build_hk_us_dirty_items()
        self.assertTrue(r["phase203_hk_us_dirty_items"]["all_metadata_only"])

class TestSourcePairs(unittest.TestCase):
    def test_pair_count(self):
        r = build_hk_us_source_pair_candidates()
        self.assertEqual(r["phase203_hk_us_source_pair_candidates"]["source_pair_candidate_count"], 4)
    def test_ready_for_phase204(self):
        r = build_hk_us_source_pair_candidates()
        self.assertTrue(r["phase203_hk_us_source_pair_candidates"]["ready_for_phase204"])

class TestVerification(unittest.TestCase):
    def test_count(self):
        r = build_hk_us_verification_preview()
        self.assertEqual(r["phase203_hk_us_verification_preview"]["verification_preview_count"], 4)
    def test_ready_count(self):
        r = build_hk_us_verification_preview()
        self.assertEqual(r["phase203_hk_us_verification_preview"]["ready_for_phase204_real_verification_count"], 4)

class TestCandidates(unittest.TestCase):
    def test_count(self):
        r = build_hk_us_dirty_to_clean_candidate_preview()
        self.assertEqual(r["phase203_hk_us_dirty_to_clean_candidate_preview"]["dirty_to_clean_candidate_preview_count"], 20)
    def test_direct_count(self):
        r = build_hk_us_dirty_to_clean_candidate_preview()
        self.assertEqual(r["phase203_hk_us_dirty_to_clean_candidate_preview"]["direct_candidate_count"], 12)

class TestBackfill(unittest.TestCase):
    def test_count(self):
        r = build_hk_us_store_backfill_preview()
        self.assertEqual(r["phase203_hk_us_store_backfill_preview"]["store_backfill_preview_count"], 4)
    def test_estimated_total(self):
        r = build_hk_us_store_backfill_preview()
        self.assertEqual(r["phase203_hk_us_store_backfill_preview"]["estimated_total_evidence"], 20)
    def test_deferred(self):
        r = build_hk_us_store_backfill_preview()
        self.assertTrue(r["phase203_hk_us_store_backfill_preview"]["store_backfill_deferred_to_phase204"])

class TestCoverageRefresh(unittest.TestCase):
    def test_generated(self):
        r = build_packet_coverage_refresh_preview()
        self.assertTrue(r["phase203_packet_coverage_refresh_preview"]["packet_coverage_refresh_generated"])
    def test_target(self):
        r = build_packet_coverage_refresh_preview()
        self.assertEqual(r["phase203_packet_coverage_refresh_preview"]["target_ticker_coverage"], 8)
    def test_missing_after(self):
        r = build_packet_coverage_refresh_preview()
        self.assertEqual(r["phase203_packet_coverage_refresh_preview"]["missing_ticker_count_after_backfill"], 1)

class TestTickerReports(unittest.TestCase):
    def test_generated(self):
        r = build_hk_us_ticker_reports()
        self.assertTrue(r["phase203_hk_us_ticker_reports"]["ticker_reports_generated"])
    def test_count(self):
        r = build_hk_us_ticker_reports()
        self.assertEqual(r["phase203_hk_us_ticker_reports"]["ticker_count"], 4)
    def test_all_tickers_present(self):
        r = build_hk_us_ticker_reports()
        reports = r["phase203_hk_us_ticker_reports"]["reports"]
        for t in ["09988.HK", "00700.HK", "NVDA", "AVGO"]:
            self.assertIn(t, reports)

class TestBoard(unittest.TestCase):
    def test_generated(self):
        r = build_hk_us_expansion_board()
        self.assertTrue(r["phase203_hk_us_expansion_board"]["board_generated"])
    def test_not_trade_signal(self):
        r = build_hk_us_expansion_board()
        self.assertTrue(r["phase203_hk_us_expansion_board"]["board_not_trade_signal"])

class TestBrief(unittest.TestCase):
    def test_generated(self):
        r = build_hk_us_expansion_brief()
        self.assertTrue(r["phase203_hk_us_expansion_brief"]["brief_generated"])
    def test_not_trade_advice(self):
        r = build_hk_us_expansion_brief()
        self.assertTrue(r["phase203_hk_us_expansion_brief"]["brief_not_trade_advice"])

class TestBacklog(unittest.TestCase):
    def test_generated(self):
        r = build_backlog_update()
        self.assertTrue(r["phase203_backlog_update"]["backlog_generated"])

class TestGuard(unittest.TestCase):
    def test_pass(self):
        r = build_cannot_conclude_guard()
        self.assertTrue(r["phase203_cannot_conclude_guard"]["guard_pass"])
    def test_violations_zero(self):
        r = build_cannot_conclude_guard()
        self.assertEqual(r["phase203_cannot_conclude_guard"]["violations_count"], 0)

class TestQualityGate(unittest.TestCase):
    def test_pass(self):
        r = build_quality_gate()
        self.assertTrue(r["phase203_quality_gate"]["gate_pass"])
    def test_no_failed(self):
        r = build_quality_gate()
        self.assertEqual(len(r["phase203_quality_gate"]["failed_checks"]), 0)
    def test_preview_only(self):
        r = build_quality_gate()
        self.assertTrue(r["phase203_quality_gate"]["checks"]["preview_only"])

class TestDashboard(unittest.TestCase):
    def test_generated(self):
        r = build_dashboard()
        self.assertTrue(r["phase203_dashboard"]["dashboard_generated"])
    def test_safety_no_trade(self):
        r = build_dashboard()
        self.assertFalse(r["phase203_dashboard"]["safety"]["trade_recommendation_created"])
    def test_safety_no_packet(self):
        r = build_dashboard()
        self.assertFalse(r["phase203_dashboard"]["safety"]["formal_packet_updated"])

if __name__ == '__main__':
    unittest.main()
