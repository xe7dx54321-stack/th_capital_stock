import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestGuard(unittest.TestCase):
    def test_guard_pass(self):
        from build_phase79_metric_cannot_conclude_guard import build
        r=build();g=r["phase79_metric_cannot_conclude_guard"]
        self.assertEqual(g["guard_status"],"pass")
        self.assertEqual(g["violations"],0)
    def test_all_not_violated(self):
        from build_phase79_metric_cannot_conclude_guard import build
        r=build();checks=r["phase79_metric_cannot_conclude_guard"]["checks"]
        for c in checks:self.assertEqual(c["status"],"not_violated")
    def test_no_pending(self):
        from build_phase79_metric_cannot_conclude_guard import build
        r=build();g=r["phase79_metric_cannot_conclude_guard"]
        self.assertEqual(g["pending_created"],0)
if __name__=="__main__":unittest.main()
