import unittest; from upsert_phase51_tracking_support_candidates import build
class Phase51UpsertTests(unittest.TestCase):
    def test_dry_run(self):
        r = build(None, "300308.SZ", "dry-run")
        self.assertEqual(r["tracking_support_candidate_upsert"]["mode"], "dry-run")
    def test_execute(self):
        r = build(None, "300308.SZ", "execute")
        self.assertEqual(r["tracking_support_candidate_upsert"]["mode"], "execute")
    def test_no_pending(self):
        r = build(None, "300308.SZ", "execute")
        self.assertEqual(r["tracking_support_candidate_upsert"]["pending_created"], 0)
    def test_no_confirmed(self):
        r = build(None, "300308.SZ", "execute")
        self.assertEqual(r["tracking_support_candidate_upsert"]["confirmed_variables_added"], 0)
    def test_no_promotion(self):
        r = build(None, "300308.SZ", "execute")
        self.assertEqual(r["tracking_support_candidate_upsert"]["usable_for_promotion_true"], 0)
if __name__ == "__main__": unittest.main()
