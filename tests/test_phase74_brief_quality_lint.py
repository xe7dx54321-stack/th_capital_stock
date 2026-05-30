import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBriefLint(unittest.TestCase):
 def test_lint_pass(self):
  from build_phase74_brief_quality_lint import build
  r=build();lt=r["phase74_brief_quality_lint"]
  self.assertEqual(lt["overall_status"],"pass")
 def test_system_zero(self):
  from build_phase74_brief_quality_lint import build
  r=build();lt=r["phase74_brief_quality_lint"]
  self.assertEqual(lt.get("system_terms_found",-1),0)
 def test_link_metadata_flag(self):
  from build_phase74_brief_quality_lint import build
  r=build();lt=r["phase74_brief_quality_lint"]
  self.assertTrue(lt.get("link_metadata_not_text",False))
 def test_attempt_not_pass(self):
  from build_phase74_brief_quality_lint import build
  r=build();lt=r["phase74_brief_quality_lint"]
  self.assertTrue(lt.get("attempt_not_written_as_pass",False))
if __name__=="__main__":unittest.main()
