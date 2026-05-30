import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestKnownURLSeeding(unittest.TestCase):
 def test_688041_has_url(self):
  from smr_phase73_known_url_seeding import seed_known_urls
  urls=seed_known_urls("688041.SH");self.assertTrue(any(u.get("url") for u in urls))
 def test_300394_empty_url(self):
  from smr_phase73_known_url_seeding import seed_known_urls
  urls=seed_known_urls("300394.SZ");self.assertFalse(any(u.get("url") for u in urls))
 def test_nonempty_url_wont_be_verified_falsely(self):
  from smr_phase73_known_url_seeding import seed_known_urls
  urls=seed_known_urls("300394.SZ")
  for u in urls:
   if not u.get("url"):self.assertNotIn("verified",u.get("verification_status",""))
if __name__=="__main__":unittest.main()
