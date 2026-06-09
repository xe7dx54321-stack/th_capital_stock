import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase204_hk_us_real_verification_store_backfill import *

class TestConfig(unittest.TestCase):
    def test_has_config(self): r = build_phase204_config(); self.assertIn("phase204_config", r)
    def test_target_count(self): r = build_phase204_config(); self.assertEqual(r["phase204_config"]["target_ticker_count"], 4)
    def test_write_gate(self): r = build_phase204_config(); self.assertTrue(r["phase204_config"]["write_store_requires_gate"])
    def test_no_mock(self): r = build_phase204_config(); self.assertFalse(r["phase204_config"]["mock_used"])

class TestPhase203Loader(unittest.TestCase):
    def test_loaded(self): r = build_phase203_loader(); self.assertTrue(r["phase204_phase203_loader"]["loaded"])
    def test_targets(self): r = build_phase203_loader(); self.assertEqual(r["phase204_phase203_loader"]["hk_count"], 2)

class TestPhase201Loader(unittest.TestCase):
    def test_loaded(self): r = build_phase201_store_loader(); self.assertTrue(r["phase204_phase201_store_loader"]["loaded"])
    def test_pre_count(self): r = build_phase201_store_loader(); self.assertEqual(r["phase204_phase201_store_loader"]["pre_backfill_total"], 84)

class TestAdditiveAudit(unittest.TestCase):
    def test_ifind_not_replacement(self): r = build_additive_source_audit(); self.assertFalse(r["phase204_additive_source_audit"]["ifind_replacement_detected"])
    def test_sources_preserved(self): r = build_additive_source_audit(); self.assertTrue(r["phase204_additive_source_audit"]["existing_sources_preserved"])
    def test_adapters_preserved(self): r = build_additive_source_audit(); self.assertTrue(r["phase204_additive_source_audit"]["existing_adapters_preserved"])

class TestVerificationTasks(unittest.TestCase):
    def test_count(self): r = build_hk_us_verification_tasks(); self.assertEqual(r["phase204_hk_us_verification_tasks"]["task_count"], 4)

class TestVerificationExecution(unittest.TestCase):
    def test_executed(self): r = build_hk_us_verification_execution(True); self.assertTrue(r["phase204_hk_us_verification_execution"]["verification_executed"])
    def test_verified_count(self): r = build_hk_us_verification_execution(True); self.assertEqual(r["phase204_hk_us_verification_execution"]["verified_support_count"], 4)
    def test_manual_zero(self): r = build_hk_us_verification_execution(True); self.assertEqual(r["phase204_hk_us_verification_execution"]["manual_review_count"], 0)
    def test_no_rejected(self): r = build_hk_us_verification_execution(True); self.assertEqual(r["phase204_hk_us_verification_execution"]["rejected_count"], 0)

class TestClassifier(unittest.TestCase):
    def test_count(self): r = build_verification_classifier(True); self.assertEqual(r["phase204_verification_classifier"]["classified_count"], 20)
    def test_clean_count(self): r = build_verification_classifier(True); self.assertEqual(r["phase204_verification_classifier"]["eligible_clean_candidate_count"], 12)
    def test_context_count(self): r = build_verification_classifier(True); self.assertEqual(r["phase204_verification_classifier"]["eligible_context_candidate_count"], 8)

class TestBackfillCandidates(unittest.TestCase):
    def test_count(self): r = build_store_backfill_candidates(True); self.assertEqual(r["phase204_store_backfill_candidates"]["backfill_candidate_count"], 20)
    def test_direct(self): r = build_store_backfill_candidates(True); self.assertEqual(r["phase204_store_backfill_candidates"]["direct_backfill_count"], 12)
    def test_context(self): r = build_store_backfill_candidates(True); self.assertEqual(r["phase204_store_backfill_candidates"]["context_backfill_count"], 8)

class TestBackfillWriter(unittest.TestCase):
    def test_no_write_default(self): r = build_store_backfill_writer(True, False); self.assertFalse(r["phase204_store_backfill_writer"]["store_backfill_written"])
    def test_with_flag(self): r = build_store_backfill_writer(True, True); self.assertTrue(r["phase204_store_backfill_writer"]["store_backfill_written"])
    def test_direct_count(self): r = build_store_backfill_writer(True, True); self.assertEqual(r["phase204_store_backfill_writer"]["direct_backfilled"], 12)
    def test_total(self): r = build_store_backfill_writer(True, True); self.assertEqual(r["phase204_store_backfill_writer"]["total_backfilled"], 20)
    def test_path_ignored(self): r = build_store_backfill_writer(True, True); self.assertTrue(r["phase204_store_backfill_writer"]["backfill_path_gitignored"])

class TestIntegrity(unittest.TestCase):
    def test_pass(self): r = build_store_backfill_integrity(False); self.assertTrue(r["phase204_store_backfill_integrity"]["integrity_pass"])

class TestRollback(unittest.TestCase):
    def test_generated(self): r = build_store_backfill_rollback(False); self.assertTrue(r["phase204_store_backfill_rollback"]["rollback_package_generated"])

class TestCoverageRefresh(unittest.TestCase):
    def test_generated(self): r = build_packet_coverage_refresh(True); self.assertTrue(r["phase204_packet_coverage_refresh"]["coverage_refresh_generated"])
    def test_missing(self): r = build_packet_coverage_refresh(True); self.assertEqual(r["phase204_packet_coverage_refresh"]["missing_ticker_count_after_phase204"], 1)

class TestTickerReports(unittest.TestCase):
    def test_count(self): r = build_hk_us_ticker_reports(True); self.assertEqual(r["phase204_hk_us_ticker_reports"]["ticker_count"], 4)
    def test_all_verified(self):
        r = build_hk_us_ticker_reports(True)
        for t in ["09988.HK", "00700.HK", "NVDA", "AVGO"]:
            self.assertEqual(r["phase204_hk_us_ticker_reports"]["reports"][t]["verification_status"], "verified_support")

class Test300394(unittest.TestCase):
    def test_cninfo(self): r = build_300394_report(); self.assertTrue(r["phase204_300394_report"]["300394_cninfo_limitation_retained"])

class TestBoard(unittest.TestCase):
    def test_generated(self): r = build_hk_us_verification_board(True); self.assertTrue(r["phase204_hk_us_verification_board"]["board_generated"])

class TestBrief(unittest.TestCase):
    def test_generated(self): r = build_hk_us_verification_brief(True); self.assertTrue(r["phase204_hk_us_verification_brief"]["brief_generated"])

class TestBacklog(unittest.TestCase):
    def test_generated(self): r = build_backlog_update(True); self.assertTrue(r["phase204_backlog_update"]["backlog_generated"])

class TestGuard(unittest.TestCase):
    def test_pass(self): r = build_cannot_conclude_guard(); self.assertTrue(r["phase204_cannot_conclude_guard"]["guard_pass"])
    def test_zero(self): r = build_cannot_conclude_guard(); self.assertEqual(r["phase204_cannot_conclude_guard"]["violations_count"], 0)

class TestQualityGate(unittest.TestCase):
    def test_pass(self): r = build_quality_gate(True); self.assertTrue(r["phase204_quality_gate"]["gate_pass"])
    def test_no_failed(self): r = build_quality_gate(True); self.assertEqual(len(r["phase204_quality_gate"]["failed_checks"]), 0)

class TestDashboard(unittest.TestCase):
    def test_generated(self): r = build_dashboard(True, False); self.assertTrue(r["phase204_dashboard"]["dashboard_generated"])
    def test_no_trade(self): r = build_dashboard(True, False); self.assertFalse(r["phase204_dashboard"]["safety"]["trade_recommendation_created"])

if __name__ == '__main__':
    unittest.main()
