import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestHygonIRParser(unittest.TestCase):
 def test_import(self):
  from smr_phase74_hygon_ir_html_parser import parse_hygon_ir
  self.assertTrue(callable(parse_hygon_ir))
 def test_skip_network(self):
  from smr_phase74_hygon_ir_html_parser import parse_hygon_ir
  r=parse_hygon_ir(skip_network=True);self.assertEqual(r["status"],"skipped")
 def test_not_hygon(self):
  from smr_phase74_hygon_ir_html_parser import parse_hygon_ir
  r=parse_hygon_ir("300394.SZ");self.assertEqual(r["status"],"ticker_not_hygon")
if __name__=="__main__":unittest.main()
