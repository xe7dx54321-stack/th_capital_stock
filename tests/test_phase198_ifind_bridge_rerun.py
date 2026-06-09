import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase198_ifind_bridge_rerun import (
    build_phase198_config, build_phase195_loader, build_phase197_loader,
    build_phase196_rules_loader, build_alignment_denoise, build_bridge_matcher,
    build_source_independence_checker, build_source_diversity_checker,
    build_time_window_consistency, build_topic_similarity,
    build_reliability_compatibility, build_conflict_preview,
    build_verification_readiness, build_verification_task_queue,
    build_300394_bridge_readiness, build_bridge_manifest, build_bridge_board,
    build_bridge_brief, build_backlog_update, build_cannot_conclude_guard,
    build_quality_gate, build_dashboard
)

class TestConfig(unittest.TestCase):
    def test_config(self):
        r = build_phase198_config()["phase198_config"]
        self.assertEqual(r["phase"], "phase198")
        self.assertTrue(r["same_market"])
        self.assertFalse(r["ifind_api_called"])
    def test_safety(self):
        r = build_phase198_config()["phase198_config"]
        self.assertTrue(r["clean_evidence_disabled"])

class TestLoaders(unittest.TestCase):
    def test_p195(self):
        r = build_phase195_loader()["phase198_phase195_loader"]
        self.assertTrue(r["loaded"])
    def test_p197(self):
        r = build_phase197_loader()["phase198_phase197_loader"]
        self.assertTrue(r.get("loaded"))
    def test_p196(self):
        r = build_phase196_rules_loader()["phase198_phase196_rules_loader"]
        self.assertTrue(r["loaded"])

class TestDenoise(unittest.TestCase):
    def test_denoise(self):
        r = build_alignment_denoise()["phase198_alignment_denoise"]
        self.assertGreater(r["input_alignments"], 0)
        self.assertGreaterEqual(r["candidate_count"], 0)

class TestBridgeMatcher(unittest.TestCase):
    def test_matcher(self):
        r = build_bridge_matcher(True)["phase198_bridge_matcher"]
        self.assertGreaterEqual(r["match_count"], 0)
        self.assertTrue(r["same_market"])
    def test_preview_only(self):
        r = build_bridge_matcher(True)["phase198_bridge_matcher"]
        self.assertTrue(r["matches_not_verified"])

class TestIndependence(unittest.TestCase):
    def test_indep(self):
        r = build_source_independence_checker(True)["phase198_source_independence"]
        self.assertGreaterEqual(r["independent_count"], 0)

class TestDiversity(unittest.TestCase):
    def test_diver(self):
        r = build_source_diversity_checker(True)["phase198_source_diversity"]
        self.assertGreaterEqual(r["diverse_count"], 0)

class TestTimeWindow(unittest.TestCase):
    def test_time(self):
        r = build_time_window_consistency(True)["phase198_time_window_consistency"]
        self.assertGreaterEqual(r["consistent_count"], 0)

class TestTopicSim(unittest.TestCase):
    def test_topic(self):
        r = build_topic_similarity(True)["phase198_topic_similarity"]
        self.assertGreaterEqual(r["scored_count"], 0)

class TestReliabilityComp(unittest.TestCase):
    def test_reliab(self):
        r = build_reliability_compatibility(True)["phase198_reliability_compatibility"]
        self.assertGreaterEqual(r["compatible_count"], 0)

class TestConflict(unittest.TestCase):
    def test_conflict(self):
        r = build_conflict_preview(True)["phase198_conflict_preview"]
        self.assertGreaterEqual(r["conflict_count"], 0)

class TestReadiness(unittest.TestCase):
    def test_readiness(self):
        r = build_verification_readiness(True)["phase198_verification_readiness"]
        self.assertTrue(r["classifier_not_executed"])

class TestTasks(unittest.TestCase):
    def test_tasks(self):
        r = build_verification_task_queue(True)["phase198_verification_task_queue"]
        self.assertGreaterEqual(r["task_count"], 0)
        self.assertTrue(r["all_tasks_not_executed"])

class Test300394(unittest.TestCase):
    def test_p394(self):
        r = build_300394_bridge_readiness(True)["phase198_300394_bridge_readiness"]
        self.assertTrue(r["300394_cninfo_limitation_retained"])

class TestManifest(unittest.TestCase):
    def test_manifest(self):
        r = build_bridge_manifest(True)["phase198_bridge_manifest"]
        self.assertTrue(r["manifest_generated"])
        self.assertFalse(r["clean_evidence_created"])

class TestBoard(unittest.TestCase):
    def test_board(self):
        r = build_bridge_board(True)["phase198_bridge_board"]
        self.assertTrue(r["board_generated"])

class TestBrief(unittest.TestCase):
    def test_brief(self):
        r = build_bridge_brief(True)["phase198_bridge_brief"]
        self.assertTrue(r["brief_generated"])

class TestBacklog(unittest.TestCase):
    def test_backlog(self):
        r = build_backlog_update(True)["phase198_backlog_update"]
        self.assertTrue(r["backlog_generated"])

class TestGuard(unittest.TestCase):
    def test_guard(self):
        r = build_cannot_conclude_guard(True)["phase198_cannot_conclude_guard"]
        self.assertTrue(r["guard_pass"])
        self.assertEqual(r["violations_count"], 0)

class TestQualityGate(unittest.TestCase):
    def test_gate(self):
        r = build_quality_gate(True)["phase198_quality_gate"]
        self.assertTrue(r["gate_pass"])

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard(True)["phase198_dashboard"]
        self.assertTrue(r["dashboard_generated"])
    def test_safety(self):
        r = build_dashboard(True)["phase198_dashboard"]
        s = r["safety"]
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["ifind_api_called"])
        self.assertFalse(s["clean_evidence_created"])
        self.assertFalse(s["classifier_executed"])

if __name__ == '__main__':
    unittest.main()
