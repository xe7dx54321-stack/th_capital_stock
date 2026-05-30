import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestCompanyIRSeeding(unittest.TestCase):
 def test_688041_has_site(self):
  from smr_phase73_company_ir_url_seeding import seed_company_ir
  r=seed_company_ir("688041.SH");self.assertTrue(r.get("official_site") or r.get("ir_page"))
 def test_300394_manual(self):
  from smr_phase73_company_ir_url_seeding import seed_company_ir
  r=seed_company_ir("300394.SZ");self.assertIn("manual",r.get("verification_status",""))
 def test_empty_not_verified(self):
  from smr_phase73_company_ir_url_seeding import seed_company_ir
  r=seed_company_ir("300394.SZ");self.assertFalse(r.get("official_site"))
 def test_no_mock(self):
  from smr_phase73_company_ir_url_seeding import seed_company_ir
  r=seed_company_ir("688041.SH")
  self.assertFalse(r.get("mock_used",True));self.assertFalse(r.get("fixture_used",True))
if __name__=="__main__":unittest.main()
