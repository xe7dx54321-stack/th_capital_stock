import phase54_helpers, unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from build_phase54_research_brief_quality_dashboard import build_dashboard

class Phase54QDashboardTests(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard()
        s = r['summary']
        self.assertEqual(s['pending_created'], 0)
        self.assertEqual(s['system_status_terms_found'], 0)

    def test_depth_pass(self):
        r = build_dashboard()
        s = r['summary']
        self.assertIn(s['depth_status'], ['pass', 'warning'])

    def test_has_observed_first_checks(self):
        r = build_dashboard()
        s = r['summary']
        self.assertTrue(s['has_current_observations'])
        self.assertTrue(s['has_cannot_conclude'])
        self.assertTrue(s['no_teaching_style'])

if __name__ == '__main__':
    unittest.main()
