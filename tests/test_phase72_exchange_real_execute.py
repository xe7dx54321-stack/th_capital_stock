import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
for p in [str(J), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)
class TestExchangeRealExecute(unittest.TestCase):
    def test_dry_run(self):
        from run_phase72_exchange_real_execute import run
        r = run(mode="dry_run"); self.assertEqual(r["phase72_exchange_real_execute"]["mode"], "dry_run")
    def test_execute_has_metadata(self):
        from run_phase72_exchange_real_execute import run
        r = run(mode="execute"); d = r["phase72_exchange_real_execute"]
        self.assertIn("metadata_found", d)
    def test_no_mock(self):
        from run_phase72_exchange_real_execute import run
        r = run(mode="execute"); d = r["phase72_exchange_real_execute"]
        self.assertFalse(d.get("mock_used",True))
    def test_report_outputs(self):
        from build_phase72_exchange_real_execute_report import build
        r = build(); self.assertIsNotNone(r)
if __name__ == "__main__": unittest.main()
