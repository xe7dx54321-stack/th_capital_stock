import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
for p in [str(J), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)
class TestExchange(unittest.TestCase):
    def test_dry_run(self):
        from run_phase71_exchange_disclosure_fetch import run
        r = run(mode="dry_run"); self.assertEqual(r["status"], "dry_run")
    def test_execute_has_rows(self):
        from run_phase71_exchange_disclosure_fetch import run
        r = run(mode="execute"); rep = r.get("exchange_disclosure_report", r)
        self.assertGreaterEqual(len(rep.get("rows", [])), 2)
    def test_no_mock_fixture(self):
        from run_phase71_exchange_disclosure_fetch import run
        r = run(mode="execute"); rep = r.get("exchange_disclosure_report", r)
        self.assertFalse(rep.get("mock_used",True))
    def test_report_outputs(self):
        from build_phase71_exchange_disclosure_report import build
        r = build(); self.assertIsNotNone(r)
if __name__ == "__main__": unittest.main()
