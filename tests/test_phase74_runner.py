import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestPhase74Runner(unittest.TestCase):
 def test_dry_run(self):
  from run_phase74_fallback_html_parsing_and_text_extraction import run
  r=run("dry_run");s=r["phase74_fallback_html_parsing_and_text_extraction"]
  self.assertGreater(len(s.get("steps",[])),0)
 def test_execute(self):
  from run_phase74_fallback_html_parsing_and_text_extraction import run
  r=run("execute");s=r["phase74_fallback_html_parsing_and_text_extraction"]
  self.assertEqual(s["mode"],"execute")
 def test_skip_network(self):
  from run_phase74_fallback_html_parsing_and_text_extraction import run
  r=run("skip_network");s=r["phase74_fallback_html_parsing_and_text_extraction"]
  self.assertEqual(s["mode"],"skip_network")
 def test_no_mock(self):
  from run_phase74_fallback_html_parsing_and_text_extraction import run
  r=run("execute");s=r["phase74_fallback_html_parsing_and_text_extraction"]
  self.assertFalse(s.get("mock_used",True));self.assertFalse(s.get("fixture_used",True))
 def test_pending_zero(self):
  from run_phase74_fallback_html_parsing_and_text_extraction import run
  r=run("execute");s=r["phase74_fallback_html_parsing_and_text_extraction"]
  self.assertEqual(s.get("pending_created",-1),0)
if __name__=="__main__":unittest.main()
