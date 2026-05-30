import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestIRMHTMLQAParser(unittest.TestCase):
 def test_import(self):
  from smr_phase74_irm_html_qa_parser import parse_irm_html
  self.assertTrue(callable(parse_irm_html))
 def test_sh_unsupported(self):
  from smr_phase74_irm_html_qa_parser import parse_irm_html
  r=parse_irm_html("688041.SH");self.assertEqual(r["status"],"unsupported_sh")
 def test_skip_network(self):
  from smr_phase74_irm_html_qa_parser import parse_irm_html
  r=parse_irm_html("300394.SZ",skip_network=True);self.assertEqual(r["status"],"skipped")
 def test_no_mock(self):
  from smr_phase74_irm_html_qa_parser import parse_irm_html
  r=parse_irm_html("300394.SZ",skip_network=True)
  self.assertFalse(r.get("mock_used",True))
if __name__=="__main__":unittest.main()
