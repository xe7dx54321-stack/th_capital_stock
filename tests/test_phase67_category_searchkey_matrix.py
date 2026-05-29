import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_cninfo_category_searchkey_matrix import run_matrix
class TestMatrix(unittest.TestCase):
    def test_dry_run(self):
        r=run_matrix("300308.SZ",mode="dry_run")
        self.assertEqual(r["category_searchkey_matrix"]["status"],"dry_run")
    def test_parameter_sets_limited(self):
        r=run_matrix("300308.SZ",mode="dry_run")
        mx=r["category_searchkey_matrix"]
        self.assertLessEqual(mx.get("parameter_sets_tested",999),30)
    def test_zero_results_recorded(self):
        r=run_matrix("300308.SZ",mode="dry_run")
        self.assertIn("zero_result_sets",r["category_searchkey_matrix"])
if __name__=="__main__":unittest.main()
