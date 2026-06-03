import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_ticker_card_html_section import build_ticker_card_html_section

class TestTickerCards(unittest.TestCase):
    def test_cards_build(self):
        r = build_ticker_card_html_section()
        self.assertIn('phase141_ticker_card_html_section', r)
        self.assertEqual(r['phase141_ticker_card_html_section']['cards'], 8)
        self.assertTrue(r['phase141_ticker_card_html_section']['not_trade'])
        html = r['phase141_ticker_card_html_section']['html']
        self.assertIn('NVDA', html)
        self.assertIn('300394.SZ', html)
        self.assertIn('cninfo', html.lower())

    def test_no_mock(self):
        r = build_ticker_card_html_section()
        self.assertFalse(r['phase141_ticker_card_html_section']['mock_used'])

if __name__ == '__main__':
    unittest.main()
