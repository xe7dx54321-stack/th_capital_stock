import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_daily_weekly_delivery_html_section import build_daily_weekly_delivery_html_section

class TestDeliverySection(unittest.TestCase):
    def test_builds(self):
        r = build_daily_weekly_delivery_html_section()
        self.assertIn('phase141_daily_weekly_delivery_html_section', r)
        html = r['phase141_daily_weekly_delivery_html_section']['html']
        self.assertIn('Daily Delivery', html)
        self.assertIn('Weekly Review', html)
        self.assertTrue(r['phase141_daily_weekly_delivery_html_section']['not_trade'])

if __name__ == '__main__':
    unittest.main()
