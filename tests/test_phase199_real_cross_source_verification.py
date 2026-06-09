import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase199_real_cross_source_verification import *

class TestConfig(unittest.TestCase):
    def test_config(self):
        r = build_phase199_config()["phase199_config"]
        self.assertEqual(r["phase"], "phase199")
        self.assertTrue(r["clean_evidence_disabled"])

class TestP198Loader(unittest.TestCase):
    def test_loader(self):
        r = build_phase198_loader()["phase199_phase198_loader"]
        self.assertTrue(r["loaded"])
        self.assertEqual(r["verification_task_count"], 252)

class TestMetadataRevalidation(unittest.TestCase):
    def test_meta(self):
        r = build_metadata_revalidation(True)["phase199_metadata_revalidation"]
        self.assertEqual(r["tasks_checked"], 252)
        self.assertEqual(r["valid_count"], 252)

class TestURLReachability(unittest.TestCase):
    def test_url(self):
        r = build_url_reachability(True)["phase199_url_reachability"]
        self.assertEqual(r["tasks_checked"], 252)

class TestIndependenceVerification(unittest.TestCase):
    def test_indep(self):
        r = build_source_independence_verification(True)["phase199_source_independence_verification"]
        self.assertEqual(r["tasks_checked"], 252)

class TestContentConsistency(unittest.TestCase):
    def test_content(self):
        r = build_content_consistency(True)["phase199_content_consistency"]
        self.assertGreater(r["verified_support"], 0)
        self.assertGreater(r["verified_context_only"], 0)

class TestTimeWindow(unittest.TestCase):
    def test_time(self):
        r = build_time_window_verification(True)["phase199_time_window_verification"]
        self.assertEqual(r["tasks_checked"], 252)

class TestSourceCategory(unittest.TestCase):
    def test_cat(self):
        r = build_source_category_verification(True)["phase199_source_category_verification"]
        self.assertEqual(r["tasks_checked"], 252)

class TestDivergence(unittest.TestCase):
    def test_div(self):
        r = build_divergence_resolution(True)["phase199_divergence_resolution"]
        self.assertEqual(r["resolved"], 252)

class TestOutcomes(unittest.TestCase):
    def test_outcomes(self):
        r = build_verification_outcomes(True)["phase199_verification_outcomes"]
        self.assertEqual(r["total_verified"], 252)
        self.assertTrue(r["all_outcomes_preliminary"])

class TestDirtyToClean(unittest.TestCase):
    def test_candidates(self):
        r = build_dirty_to_clean_candidate_preview(True)["phase199_dirty_to_clean_candidate_preview"]
        self.assertGreater(r["candidate_count"], 0)
        self.assertTrue(r["classifier_not_executed"])

class TestManualReview(unittest.TestCase):
    def test_manual(self):
        r = build_manual_review_queue(True)["phase199_manual_review_queue"]
        self.assertGreaterEqual(r["queue_count"], 0)

class TestRejected(unittest.TestCase):
    def test_rejected(self):
        r = build_rejected_insufficient_queue(True)["phase199_rejected_insufficient_queue"]
        self.assertGreaterEqual(r["queue_count"], 0)

class Test300394(unittest.TestCase):
    def test_p394(self):
        r = build_300394_verification_report(True)["phase199_300394_verification_report"]
        self.assertTrue(r["300394_cninfo_limitation_retained"])

class TestManifest(unittest.TestCase):
    def test_manifest(self):
        r = build_verification_manifest(True)["phase199_verification_manifest"]
        self.assertTrue(r["manifest_generated"])
        self.assertFalse(r["clean_evidence_created"])

class TestBoard(unittest.TestCase):
    def test_board(self):
        r = build_verification_board(True)["phase199_verification_board"]
        self.assertTrue(r["board_generated"])

class TestBrief(unittest.TestCase):
    def test_brief(self):
        r = build_verification_brief(True)["phase199_verification_brief"]
        self.assertTrue(r["brief_generated"])

class TestBacklog(unittest.TestCase):
    def test_backlog(self):
        r = build_backlog_update(True)["phase199_backlog_update"]
        self.assertTrue(r["backlog_generated"])

class TestGuard(unittest.TestCase):
    def test_guard(self):
        r = build_cannot_conclude_guard(True)["phase199_cannot_conclude_guard"]
        self.assertTrue(r["guard_pass"])
        self.assertEqual(r["violations_count"], 0)

class TestQualityGate(unittest.TestCase):
    def test_gate(self):
        r = build_quality_gate(True)["phase199_quality_gate"]
        self.assertTrue(r["gate_pass"])

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard(True)["phase199_dashboard"]
        self.assertTrue(r["dashboard_generated"])
    def test_safety(self):
        r = build_dashboard(True)["phase199_dashboard"]
        s = r["safety"]
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["clean_evidence_created"])
        self.assertFalse(s["classifier_executed"])

if __name__ == '__main__':
    unittest.main()
