import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConfig(unittest.TestCase):
    def test_load(self):
        from smr_phase78_chinese_keyword_config import load_config
        c=load_config();self.assertEqual(c["strategy"],"chinese_keyword_matching_repair")
    def test_validate(self):
        from smr_phase78_chinese_keyword_config import validate_config
        v=validate_config();self.assertTrue(v["all_pass"])
    def test_all_vars_have_chinese(self):
        from smr_phase78_chinese_keyword_config import load_config
        c=load_config()
        for vn,vc in c["variables"].items():
            self.assertGreater(len(vc.get("chinese_keywords",[])),0,f"{vn} missing chinese keywords")
    def test_keyword_hit_not_confirmed(self):
        from smr_phase78_chinese_keyword_config import load_config
        c=load_config();self.assertTrue(c["safety"]["keyword_hit_not_confirmed"])
    def test_legal_governance_exclusion(self):
        from smr_phase78_chinese_keyword_config import load_config
        c=load_config();self.assertTrue(c["safety"]["legal_governance_exclusion_required"])
if __name__=="__main__":unittest.main()
