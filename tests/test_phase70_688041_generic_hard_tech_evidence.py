import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class Test688041Evidence(unittest.TestCase):
    def test_outputs(self):
        from build_phase70_688041_generic_hard_tech_evidence_rerun import build
        r = build(); d = r["phase70_688041_generic_hard_tech_evidence_rerun"]
        self.assertEqual(d["overall_status"], "partial_chain_available")
    def test_no_optical_variables(self):
        from build_phase70_688041_generic_hard_tech_evidence_rerun import build
        r = build(); d = r["phase70_688041_generic_hard_tech_evidence_rerun"]
        bv = str(d.get("business_variables_attempted",[]))
        self.assertNotIn("800G", bv); self.assertNotIn("1.6T", bv)
    def test_no_mock_fixture(self):
        from build_phase70_688041_generic_hard_tech_evidence_rerun import build
        r = build(); d = r["phase70_688041_generic_hard_tech_evidence_rerun"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
    def test_pending_order_trade_zero(self):
        from build_phase70_688041_generic_hard_tech_evidence_rerun import build
        r = build(); d = r["phase70_688041_generic_hard_tech_evidence_rerun"]
        self.assertEqual(d.get("pending_created",-1),0)
if __name__ == "__main__": unittest.main()
