import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestUniverse(unittest.TestCase):
    def test_three_tickers(self):
        from smr_multi_ticker_universe import load_universe, get_tickers
        u = load_universe()
        tickers = get_tickers()
        self.assertGreaterEqual(len(tickers), 3)
        self.assertIn('300308.SZ', tickers)

    def test_safety(self):
        from smr_multi_ticker_universe import get_safety
        s = get_safety()
        self.assertTrue(s['research_only'])
        self.assertFalse(s['pending_allowed'])

class TestIdentity(unittest.TestCase):
    def test_baseline_identity_no_regression(self):
        from smr_multi_ticker_disclosure_identity_resolver import resolve_multi_ticker_identities
        r = resolve_multi_ticker_identities()
        for row in r['rows']:
            if row['ticker'] == '300308.SZ':
                self.assertTrue(row['identity_found'])
                self.assertIn('9900022016', row.get('stock_param', ''))

    def test_no_org_id_reuse(self):
        from smr_multi_ticker_disclosure_identity_resolver import resolve_multi_ticker_identities
        r = resolve_multi_ticker_identities()
        ids = {}
        for row in r['rows']:
            if row.get('identity_found'):
                ids[row['ticker']] = row.get('org_id', '')
        # Each ticker should have unique org_id
        self.assertEqual(len(set(ids.values())), len(ids))

    def test_missing_has_reason(self):
        from smr_multi_ticker_disclosure_identity_resolver import resolve_multi_ticker_identities
        r = resolve_multi_ticker_identities()
        for row in r['rows']:
            if not row['identity_found']:
                self.assertIsNotNone(row.get('failure_reason'))

    def test_688041_resolved(self):
        from smr_multi_ticker_disclosure_identity_resolver import resolve_multi_ticker_identities
        r = resolve_multi_ticker_identities()
        for row in r['rows']:
            if row['ticker'] == '688041.SH':
                self.assertTrue(row['identity_found'])

if __name__ == '__main__': unittest.main()
