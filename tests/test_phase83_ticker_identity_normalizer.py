import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestIdentity(unittest.TestCase):
    def test_normalize(self):from smr_phase83_ticker_identity_normalizer import normalize_identities;r=normalize_identities();ti=r["phase83_ticker_identity"];self.assertEqual(ti["identity_normalized"],4)
    def test_hk_zero(self):from smr_phase83_ticker_identity_normalizer import normalize_identities;r=normalize_identities();rows=r["phase83_ticker_identity"]["rows"];hk=[row for row in rows if row["market"]=="HK"];self.assertEqual(len(hk),2);self.assertTrue(all("canonical"in row for row in hk))
    def test_us_canonical(self):from smr_phase83_ticker_identity_normalizer import normalize_identities;r=normalize_identities();rows=r["phase83_ticker_identity"]["rows"];us=[row for row in rows if row["market"]=="US"];self.assertEqual(len(us),2)
if __name__=="__main__":unittest.main()
