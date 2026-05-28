import unittest; from validate_phase51_candidate_quality_revalidation import revalidate
class Phase51RevalidationTests(unittest.TestCase):
    def test_pass(self):
        r = revalidate("300308.SZ")
        self.assertIn(r["real_source_candidate_revalidation"]["overall_status"], ("pass", "no_eligible"))
    def test_no_pending(self):
        r = revalidate("300308.SZ")
        self.assertEqual(r["real_source_candidate_revalidation"]["pending_created"], 0)
    def test_sensitive_false(self):
        r = revalidate("300308.SZ")
        self.assertFalse(r["real_source_candidate_revalidation"]["official_consensus_confirmed"])
        self.assertFalse(r["real_source_candidate_revalidation"]["supplier_share_confirmed"])
        self.assertFalse(r["real_source_candidate_revalidation"]["customer_allocation_confirmed"])
    def test_safety(self):
        r = revalidate("300308.SZ")
        self.assertFalse(r["safety"]["revalidation_creates_pending"])
        self.assertFalse(r["safety"]["revalidation_creates_order"])
if __name__ == "__main__": unittest.main()
