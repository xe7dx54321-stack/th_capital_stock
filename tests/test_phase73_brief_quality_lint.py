import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBriefLint(unittest.TestCase):
 def test_lint_pass(self):
  from build_phase73_brief_quality_lint import build
  r=build();lt=r["phase73_brief_quality_lint"]
  self.assertEqual(lt["overall_status"],"pass")
 def test_system_zero(self):
  from build_phase73_brief_quality_lint import build
  r=build();lt=r["phase73_brief_quality_lint"]
  self.assertEqual(lt.get("system_terms_found",-1),0)
 def test_management_not_confirmed(self):
  from build_phase73_brief_quality_lint import build
  r=build();lt=r["phase73_brief_quality_lint"]
  self.assertTrue(lt.get("management_commentary_not_confirmed",False))
 def test_attempt_not_pass(self):
  from build_phase73_brief_quality_lint import build
  r=build();lt=r["phase73_brief_quality_lint"]
  self.assertTrue(lt.get("attempt_not_written_as_pass",False))
if __name__=="__main__":unittest.main()
