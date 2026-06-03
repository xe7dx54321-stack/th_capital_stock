import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase142_ticker_detail_page_generator import generate_ticker_detail_page
from smr_phase142_detail_css_extension import build_detail_css_extension

class TestPageGen(unittest.TestCase):
    def setUp(self):
        self.css = build_detail_css_extension()['phase142_detail_css_extension']['css']
        self.td = {'ticker':'NVDA','name':'NVIDIA','market':'US','currency':'USD','thesis':'AI GPU','thesis_status':'strengthened','confidence':'high','thesis_timeline':[],'evidence_chain':[],'deep_dives':[],'financial_snapshot':{},'source_limitations':[],'gaps':[],'owner_actions':[],'related_artifacts':[]}
    def test_generates_html(self):
        html = generate_ticker_detail_page(self.td, self.css)
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('NVDA', html)
        self.assertIn('Research-only', html)
    def test_no_trade(self):
        html = generate_ticker_detail_page(self.td, self.css)
        self.assertNotIn('buy recommendation', html.lower())

if __name__ == '__main__':
    unittest.main()
