import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase200_dirty_to_clean_classifier import *
class TestConfig(unittest.TestCase):
    def test_config(self):
        r = build_phase200_config()["phase200_config"]
        self.assertEqual(r["phase"], "phase200")
        self.assertTrue(r["clean_evidence_store_disabled"])
class TestP199Loader(unittest.TestCase):
    def test_loader(self):
        r = build_phase199_loader()["phase200_phase199_loader"]
        self.assertTrue(r["loaded"])
        self.assertEqual(r["candidate_input_count"], 126)
class TestConflictGate(unittest.TestCase):
    def test_gate(self):
        r = build_conflict_exclusion_gate()["phase200_conflict_exclusion_gate"]
        self.assertEqual(r["conflict_items_excluded"], 63)
        self.assertEqual(r["conflict_items_sent_to_classifier"], 0)
class TestEligibility(unittest.TestCase):
    def test_prefilter(self):
        r = build_candidate_eligibility_prefilter(True)["phase200_candidate_eligibility_prefilter"]
        self.assertEqual(r["candidates_input"], 126)
class TestEvidenceType(unittest.TestCase):
    def test_type(self):
        r = build_evidence_type_classifier(True)["phase200_evidence_type_classifier"]
        self.assertEqual(r["classified_count"], 126)
class TestClaimSupport(unittest.TestCase):
    def test_claim(self):
        r = build_claim_support_classifier(True)["phase200_claim_support_classifier"]
        self.assertEqual(r["classified_count"], 126)
class TestStrength(unittest.TestCase):
    def test_strength(self):
        r = build_evidence_strength_classifier(True)["phase200_evidence_strength_classifier"]
        self.assertEqual(r["classified_count"], 126)
class TestLineage(unittest.TestCase):
    def test_lineage(self):
        r = build_source_lineage(True)["phase200_source_lineage"]
        self.assertEqual(r["count"], 126)
class TestRisk(unittest.TestCase):
    def test_risk(self):
        r = build_evidence_risk_tagger(True)["phase200_evidence_risk_tagger"]
        self.assertEqual(r["count"], 126)
class TestContextPolicy(unittest.TestCase):
    def test_policy(self):
        r = build_context_only_policy()["phase200_context_only_policy"]
        self.assertFalse(r["context_only_eligible_for_clean_store"])
class Test300394(unittest.TestCase):
    def test_p394(self):
        r = build_300394_classifier_report(True)["phase200_300394_classifier_report"]
        self.assertTrue(r["300394_cninfo_limitation_retained"])
class TestPreview(unittest.TestCase):
    def test_preview(self):
        r = build_clean_evidence_candidate_preview(True)["phase200_clean_evidence_candidate_preview"]
        self.assertGreater(r["clean_candidate_count"], 0)
        self.assertTrue(r["clean_evidence_not_written"])
class TestStorePreview(unittest.TestCase):
    def test_store(self):
        r = build_phase201_store_input_preview(True)["phase200_phase201_store_input_preview"]
        self.assertTrue(r["store_write_not_executed"])
class TestManifest(unittest.TestCase):
    def test_manifest(self):
        r = build_classifier_manifest(True)["phase200_classifier_manifest"]
        self.assertTrue(r["manifest_generated"])
        self.assertTrue(r["clean_evidence_store_not_updated"])
class TestBoard(unittest.TestCase):
    def test_board(self):
        r = build_classifier_board(True)["phase200_classifier_board"]
        self.assertTrue(r["board_generated"])
class TestBrief(unittest.TestCase):
    def test_brief(self):
        r = build_classifier_brief(True)["phase200_classifier_brief"]
        self.assertTrue(r["brief_generated"])
class TestBacklog(unittest.TestCase):
    def test_backlog(self):
        r = build_backlog_update(True)["phase200_backlog_update"]
        self.assertTrue(r["backlog_generated"])
class TestGuard(unittest.TestCase):
    def test_guard(self):
        r = build_cannot_conclude_guard(True)["phase200_cannot_conclude_guard"]
        self.assertTrue(r["guard_pass"])
class TestGate(unittest.TestCase):
    def test_gate(self):
        r = build_quality_gate(True)["phase200_quality_gate"]
        self.assertTrue(r["gate_pass"])
class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard(True)["phase200_dashboard"]
        self.assertTrue(r["dashboard_generated"])
    def test_safety(self):
        r = build_dashboard(True)["phase200_dashboard"]
        s = r["safety"]
        self.assertFalse(s["clean_evidence_store_updated"])
        self.assertFalse(s["packet_updated"])
        self.assertFalse(s["trade_recommendation_created"])
if __name__ == '__main__': unittest.main()
