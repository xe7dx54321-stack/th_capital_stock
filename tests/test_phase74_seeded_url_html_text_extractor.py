import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestSeededExtractor(unittest.TestCase):
 def test_dry_run(self):
  from run_phase74_seeded_url_html_text_extract import run
  r=run("dry_run");d=r["phase74_seeded_url_html_text_extract"]
  self.assertGreaterEqual(d["seeded_urls_checked"],0)
 def test_empty_url(self):
  from run_phase74_seeded_url_html_text_extract import fetch_and_extract
  r=fetch_and_extract("","test");self.assertEqual(r["error"],"empty_url")
 def test_no_raw(self):
  from run_phase74_seeded_url_html_text_extract import run
  r=run("dry_run");d=r["phase74_seeded_url_html_text_extract"]
  self.assertFalse(d.get("raw_saved",True))
if __name__=="__main__":unittest.main()
