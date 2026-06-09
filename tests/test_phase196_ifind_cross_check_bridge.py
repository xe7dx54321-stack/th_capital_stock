# Tests for Phase196 iFinD Cross-check Bridge
import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase196_ifind_cross_check_bridge import (
    build_phase196_config, build_phase195_loader, build_phase188_loader,
    build_phase185_loader, build_bridge_domain_registry, build_bridge_matcher,
    build_source_independence_checker, build_source_diversity_checker,
    build_time_window_consistency, build_conflict_detector,
    build_verification_readiness_refresh, build_next_verification_task_queue,
    build_bridge_manifest, build_bridge_board, build_bridge_brief,
    build_backlog_update, build_cannot_conclude_guard, build_quality_gate,
    build_dashboard, MATCH_STRENGTHS
)

class TestPhase196Config(unittest.TestCase):
    def test_config_loaded(self):
        r = build_phase196_config()["phase196_config"]
        self.assertTrue(r["config_loaded"])
        self.assertEqual(r["phase"], "phase196")
    def test_strategy_correct(self):
        r = build_phase196_config()["phase196_config"]
        self.assertIn("cross_check_bridge", r["strategy"])
    def test_market_scope_warning(self):
        r = build_phase196_config()["phase196_config"]
        self.assertIn("market_scope_mismatch_warning", r)
    def test_safety_flags(self):
        r = build_phase196_config()["phase196_config"]
        self.assertTrue(r["clean_evidence_disabled"])
        self.assertFalse(r["mock_used"])

class TestPhase196Loaders(unittest.TestCase):
    def test_p195_loader(self):
        r = build_phase195_loader()["phase196_phase195_loader"]
        self.assertTrue(r["loaded"])
        self.assertGreater(r["dirty_item_count"], 0)
        self.assertEqual(r["market"], "CN_A")
    def test_p188_loader(self):
        r = build_phase188_loader()["phase196_phase188_loader"]
        self.assertTrue(r["loaded"])
        self.assertEqual(r["market"], "US")
    def test_p185_loader(self):
        r = build_phase185_loader()["phase196_phase185_loader"]
        self.assertTrue(r["loaded"])
        self.assertEqual(r["market"], "US")

class TestPhase196BridgeDomainRegistry(unittest.TestCase):
    def test_registry(self):
        r = build_bridge_domain_registry()["phase196_bridge_domain_registry"]
        self.assertTrue(r["registry_defined"])
        self.assertTrue(r["cross_market_bridge"])

class TestPhase196BridgeMatcher(unittest.TestCase):
    def test_matcher(self):
        r = build_bridge_matcher(True)["phase196_bridge_matcher"]
        self.assertGreaterEqual(r["match_count"], 0)
        self.assertIn("strong", r)
        self.assertIn("moderate", r)
        self.assertIn("weak", r)
        self.assertTrue(r["cross_market_bridge"])
    def test_matches_preview_only(self):
        r = build_bridge_matcher(True)["phase196_bridge_matcher"]
        self.assertTrue(r["all_matches_preview"])
        self.assertTrue(r["matches_not_verified"])
    def test_market_scope_noted(self):
        r = build_bridge_matcher(True)["phase196_bridge_matcher"]
        self.assertIn("market_scope_note", r)

class TestPhase196IndependenceChecker(unittest.TestCase):
    def test_checker(self):
        r = build_source_independence_checker(True)["phase196_source_independence_checker"]
        self.assertGreaterEqual(r["independent_count"], 0)
        self.assertTrue(r["independence_not_verified"])

class TestPhase196DiversityChecker(unittest.TestCase):
    def test_checker(self):
        r = build_source_diversity_checker(True)["phase196_source_diversity_checker"]
        self.assertGreaterEqual(r["diverse_count"], 0)
        self.assertTrue(r["diversity_not_verified"])

class TestPhase196TimeWindow(unittest.TestCase):
    def test_consistency(self):
        r = build_time_window_consistency(True)["phase196_time_window_consistency"]
        self.assertTrue(r["time_window_preview_only"])

class TestPhase196ConflictDetector(unittest.TestCase):
    def test_detector(self):
        r = build_conflict_detector(True)["phase196_conflict_detector"]
        self.assertGreaterEqual(r["conflict_count"], 0)

class TestPhase196VerificationReadiness(unittest.TestCase):
    def test_readiness(self):
        r = build_verification_readiness_refresh(True)["phase196_verification_readiness_refresh"]
        self.assertGreaterEqual(r["ready_for_real_cross_source_verification"], 0)
        self.assertTrue(r["classifier_not_executed"])

class TestPhase196NextVerificationTasks(unittest.TestCase):
    def test_task_queue(self):
        r = build_next_verification_task_queue(True)["phase196_next_verification_task_queue"]
        self.assertGreaterEqual(r["task_count"], 0)
        self.assertTrue(r["all_tasks_preview_only"])
        self.assertTrue(r["verification_not_executed"])

class TestPhase196BridgeManifest(unittest.TestCase):
    def test_manifest(self):
        r = build_bridge_manifest(True)["phase196_bridge_manifest"]
        self.assertTrue(r["manifest_generated"])
        self.assertFalse(r["clean_evidence_created"])
        self.assertTrue(r["classifier_not_executed"])

class TestPhase196BridgeBoard(unittest.TestCase):
    def test_board(self):
        r = build_bridge_board(True)["phase196_bridge_board"]
        self.assertTrue(r["board_generated"])
        self.assertTrue(r["board_not_clean_evidence"])

class TestPhase196BridgeBrief(unittest.TestCase):
    def test_brief(self):
        r = build_bridge_brief(True)["phase196_bridge_brief"]
        self.assertTrue(r["brief_generated"])
        self.assertIn("boss_summary", r)
    def test_no_trade_advice(self):
        r = build_bridge_brief(True)["phase196_bridge_brief"]
        self.assertTrue(r["brief_not_trade_advice"])

class TestPhase196BacklogUpdate(unittest.TestCase):
    def test_backlog(self):
        r = build_backlog_update(True)["phase196_backlog_update"]
        self.assertTrue(r["backlog_generated"])

class TestPhase196CannotConcludeGuard(unittest.TestCase):
    def test_guard_pass(self):
        r = build_cannot_conclude_guard(True)["phase196_cannot_conclude_guard"]
        self.assertTrue(r["guard_pass"])
        self.assertEqual(r["violations_count"], 0)

class TestPhase196QualityGate(unittest.TestCase):
    def test_gate_pass(self):
        r = build_quality_gate(True)["phase196_quality_gate"]
        self.assertTrue(r["gate_pass"])
    def test_gate_not_trade(self):
        r = build_quality_gate(True)["phase196_quality_gate"]
        self.assertTrue(r["gate_not_trade_signal"])

class TestPhase196Dashboard(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard(True)["phase196_dashboard"]
        self.assertTrue(r["dashboard_generated"])
        self.assertEqual(r["phase"], "phase196")
    def test_safety(self):
        r = build_dashboard(True)["phase196_dashboard"]
        s = r["safety"]
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["clean_evidence_created"])
        self.assertFalse(s["packet_updated"])
        self.assertFalse(s["trade_recommendation_created"])
        self.assertFalse(s["broker_api_called"])
        self.assertFalse(s["classifier_executed"])
        self.assertFalse(s["real_verification_executed"])

if __name__ == '__main__':
    unittest.main()
