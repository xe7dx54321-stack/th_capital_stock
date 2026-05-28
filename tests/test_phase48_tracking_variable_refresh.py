import unittest
from phase48_helpers import make_phase48_conn
from build_phase48_tracking_variable_refresh import build_payload

class Phase48TrackingVariableRefreshTests(unittest.TestCase):
    def test_variables_checked(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ")
        ref = p["tracking_variable_refresh"]
        self.assertEqual(ref["variables_checked"], 11)
    def test_touched_variables(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ")
        ref = p["tracking_variable_refresh"]
        self.assertIn("product_mix", ref["variables_touched_by_event"])
    def test_no_scenario_confirmation(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ")
        safety = p["safety"]
        self.assertTrue(safety["scenario_proxy_unconfirmed_preserved"])
        self.assertEqual(safety["pending_created"], 0)
if __name__ == "__main__": unittest.main()
