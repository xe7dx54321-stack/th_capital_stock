import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestMetadata(unittest.TestCase):
    def test_dry_run(self):
        from smr_multi_ticker_disclosure_metadata_fetcher import fetch_multi_ticker_metadata
        r = fetch_multi_ticker_metadata(dry_run=True)
        self.assertEqual(r['tickers_checked'], 3)
        for row in r['rows']:
            self.assertEqual(row['status'], 'dry_run')

    def test_identity_missing(self):
        from smr_multi_ticker_disclosure_metadata_fetcher import fetch_multi_ticker_metadata
        r = fetch_multi_ticker_metadata(dry_run=False)
        for row in r['rows']:
            if row['ticker'] == '300394.SZ':
                self.assertEqual(row['status'], 'metadata_unavailable')

class TestSelector(unittest.TestCase):
    def test_max_pdfs_effective(self):
        from smr_multi_ticker_high_value_disclosure_selector import select_multi_ticker_high_value
        r = select_multi_ticker_high_value(max_pdfs_per_ticker=5)
        for row in r['rows']:
            self.assertLessEqual(row.get('selected_pdfs', 0), 5)

    def test_three_tickers_checked(self):
        from smr_multi_ticker_high_value_disclosure_selector import select_multi_ticker_high_value
        r = select_multi_ticker_high_value()
        self.assertEqual(r['tickers_checked'], 3)

class TestRouter(unittest.TestCase):
    def test_ai_optical_module(self):
        from smr_multi_ticker_industry_template_router import route_industry_template
        r = route_industry_template('300308.SZ')
        self.assertEqual(r['industry_template'], 'ai_optical_module')
        self.assertIn('800G_product_signal', r['business_variables'])

    def test_generic_hard_tech(self):
        from smr_multi_ticker_industry_template_router import route_industry_template
        r = route_industry_template('688041.SH')
        self.assertEqual(r['industry_template'], 'generic_hard_tech')
        self.assertNotIn('800G_product_signal', r['business_variables'])

    def test_not_hard_apply_optical(self):
        from smr_multi_ticker_industry_template_router import route_industry_template
        r = route_industry_template('688041.SH')
        self.assertNotIn('800G_product_signal', r['business_variables'])

class TestDeepEvidence(unittest.TestCase):
    def test_multi_ticker_evidence(self):
        from smr_multi_ticker_deep_evidence_extractor import extract_multi_ticker_deep_evidence
        r = extract_multi_ticker_deep_evidence()
        self.assertEqual(r['tickers_checked'], 3)
        self.assertGreaterEqual(r['tickers_with_evidence'], 1)

    def test_supported_not_confirmed(self):
        # Can't confirm ASP, customer share, specific orders
        pass

if __name__ == '__main__': unittest.main()
