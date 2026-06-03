import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'reporting'))
from build_phase141_html_dashboard import build_full_html

class TestDashboardBuilder(unittest.TestCase):
    def test_builds_full_html(self):
        r = build_full_html()
        self.assertIn('phase141_html_dashboard', r)
        dash = r['phase141_html_dashboard']
        self.assertGreater(len(dash['html']), 1000)
        self.assertIn('<!DOCTYPE html>', dash['html'])
        self.assertIn('TH Capital Research Console', dash['html'])
        self.assertTrue(dash['static_html_only'])

    def test_safety_boundaries(self):
        r = build_full_html()
        dash = r['phase141_html_dashboard']
        self.assertFalse(dash['mock_used'])
        self.assertFalse(dash['fixture_used'])
        self.assertEqual(dash['pending_created'], 0)
        self.assertEqual(dash['paper_order_created'], 0)
        self.assertEqual(dash['real_trade_created'], 0)

    def test_quality_gate_passes(self):
        r = build_full_html()
        qg = r['phase141_html_dashboard']['quality_gate']
        self.assertEqual(qg['overall_status'], 'pass')

    def test_guard_passes(self):
        r = build_full_html()
        cg = r['phase141_html_dashboard']['cannot_conclude_guard']
        self.assertEqual(cg['overall_status'], 'pass')
        self.assertEqual(cg['violations'], 0)

    def test_all_sections_present(self):
        r = build_full_html()
        html = r['phase141_html_dashboard']['html']
        for s in ['ticker-cards','thesis-library','evidence-sources','daily-delivery','owner-actions','gap-risk','feedback-template','artifact-links']:
            self.assertIn(s, html)

    def test_no_trade_content_in_body(self):
        r = build_full_html()
        html = r['phase141_html_dashboard']['html']
        body = html.lower()
        footer_start = body.find('<footer')
        footer_end = body.find('</footer>')
        if footer_start >= 0 and footer_end >= 0:
            body = body[:footer_start] + body[footer_end + 9:]
        for term in ['buy recommendation', 'sell recommendation', 'entry point', 'exit point', 'place order', 'long position', 'short position']:
            self.assertNotIn(term.lower(), body)

    def test_300394_cninfo_preserved(self):
        r = build_full_html()
        html = r['phase141_html_dashboard']['html']
        self.assertIn('300394', html)
        self.assertIn('cninfo', html.lower())

    def test_688041_valuation_preserved(self):
        r = build_full_html()
        html = r['phase141_html_dashboard']['html']
        self.assertIn('688041', html)
        self.assertIn('derived', html.lower())

    def test_no_cdn_no_external(self):
        r = build_full_html()
        html = r['phase141_html_dashboard']['html']
        self.assertNotIn('cdn.', html.lower())
        self.assertNotIn('src="http', html)

if __name__ == '__main__':
    unittest.main()
