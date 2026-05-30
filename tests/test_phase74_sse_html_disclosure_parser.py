import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestSSEHTMLParser(unittest.TestCase):
 def test_import(self):
  from smr_phase74_sse_html_disclosure_parser import parse_sse_html
  self.assertTrue(callable(parse_sse_html))
 def test_sz_unsupported(self):
  from smr_phase74_sse_html_disclosure_parser import parse_sse_html
  r=parse_sse_html("300394.SZ");self.assertEqual(r["status"],"unsupported_sz")
 def test_skip_network(self):
  from smr_phase74_sse_html_disclosure_parser import parse_sse_html
  r=parse_sse_html("688041.SH",skip_network=True);self.assertEqual(r["status"],"skipped")
if __name__=="__main__":unittest.main()
