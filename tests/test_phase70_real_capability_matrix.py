import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestCapabilityMatrix(unittest.TestCase):
    def test_three_tickers(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        self.assertEqual(cm["tickers_checked"], 3)
    def test_no_pass_without_execute(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        self.assertTrue(cm["no_pass_without_execute"])
    def test_rows_have_basis(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        for row in cm["rows"]:
            self.assertIn("basis", row)
    def test_blocked_has_blocker(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        for row in cm["rows"]:
            if row["overall"] == "blocked":
                self.assertIn("blocker", row)
    def test_partial_has_reason(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        for row in cm["rows"]:
            if row["overall"] == "partial_chain_available":
                self.assertIn("partial_reason", row)
    def test_no_mock_fixture(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        self.assertFalse(cm.get("mock_used",True)); self.assertFalse(cm.get("fixture_used",True))
    def test_pending_zero(self):
        from build_phase70_real_capability_matrix import build
        r = build(); cm = r["phase70_real_capability_matrix"]
        self.assertEqual(cm.get("pending_created",-1),0)
        self.assertEqual(cm.get("paper_order_created",-1),0)
        self.assertEqual(cm.get("real_trade_created",-1),0)
if __name__ == "__main__": unittest.main()
