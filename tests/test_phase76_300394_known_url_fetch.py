import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestKnownURLFetch(unittest.TestCase):
    def test_dry_run(self):
        from run_phase76_300394_known_url_fetch import run
        r = run("dry_run")
        f = r["phase76_300394_known_url_fetch"]
        self.assertFalse(f["network_attempted"])
    def test_skip_network(self):
        from run_phase76_300394_known_url_fetch import run
        r = run("skip_network")
        self.assertFalse(r["phase76_300394_known_url_fetch"]["network_attempted"])
    def test_no_mock(self):
        from run_phase76_300394_known_url_fetch import run
        r = run("dry_run")
        self.assertFalse(r["phase76_300394_known_url_fetch"]["mock_used"])

if __name__ == "__main__": unittest.main()
