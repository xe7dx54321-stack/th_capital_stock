import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestSeededURLFetch(unittest.TestCase):
 def test_dry_run(self):
  from run_phase73_seeded_url_controlled_fetch import run
  r=run("dry_run");self.assertIn("rows",r["phase73_seeded_url_fetch"])
 def test_empty_url_not_fetch(self):
  from run_phase73_seeded_url_controlled_fetch import fetch_url
  r=fetch_url("");self.assertEqual(r["error"],"empty_url")
 def test_no_raw_no_ocr(self):
  from run_phase73_seeded_url_controlled_fetch import run
  r=run("dry_run");self.assertFalse(r["phase73_seeded_url_fetch"].get("raw_saved",True))
  self.assertFalse(r["phase73_seeded_url_fetch"].get("ocr_used",True))
if __name__=="__main__":unittest.main()
