import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(J) not in sys.path: sys.path.insert(0, str(J))
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase75SeededURLRealExecute(unittest.TestCase):
    def test_dry_run(self):
        from run_phase75_seeded_url_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_seeded_url_html_real_execute"]["network_attempted"])
    def test_empty_url_no_fetch(self):
        from run_phase75_seeded_url_html_real_execute import fetch_and_extract
        r = fetch_and_extract("", "test")
        self.assertEqual(r["error"], "empty_url")
    def test_no_mock(self):
        from run_phase75_seeded_url_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_seeded_url_html_real_execute"]["mock_used"])

if __name__ == "__main__":
    unittest.main()
