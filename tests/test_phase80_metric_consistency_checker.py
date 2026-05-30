import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConsistency(unittest.TestCase):
    def test_check(self):
        from smr_phase80_metric_consistency_checker import check_consistency
        rows=[{"metric_name":"revenue","comparison_status":"matched"},{"metric_name":"revenue","comparison_status":"matched"},{"metric_name":"gross_margin","comparison_status":"report_only"}]
        r=check_consistency(rows);rr=r["phase80_metric_consistency"]
        self.assertGreater(rr["consistent_metrics"],0)
    def test_can_use_flag(self):
        from smr_phase80_metric_consistency_checker import check_consistency
        rows=[{"metric_name":"revenue","comparison_status":"matched"},{"metric_name":"gross_margin","comparison_status":"mismatch"},{"metric_name":"gross_margin","comparison_status":"report_only"}]
        r=check_consistency(rows);crows=r["phase80_metric_consistency"]["rows"]
        for cr in crows:
            if cr["metric_name"]=="gross_margin":self.assertFalse(cr["can_use_for_time_series"])
    def test_insufficient(self):
        from smr_phase80_metric_consistency_checker import check_consistency
        r=check_consistency([]);self.assertEqual(r["phase80_metric_consistency"]["consistent_metrics"],0)
if __name__=="__main__":unittest.main()
