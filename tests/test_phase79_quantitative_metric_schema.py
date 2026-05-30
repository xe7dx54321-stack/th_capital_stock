import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestMetricSchema(unittest.TestCase):
    def test_load(self):
        from smr_phase79_quantitative_metric_schema import load_schema, get_metric_count
        s=load_schema();self.assertGreater(get_metric_count(),10)
    def test_revenue_covered(self):
        from smr_phase79_quantitative_metric_schema import get_metric_aliases
        a=get_metric_aliases();self.assertIn("revenue",a)
    def test_gross_margin_covered(self):
        from smr_phase79_quantitative_metric_schema import get_metric_aliases
        a=get_metric_aliases();self.assertIn("gross_margin",a)
    def test_rd_covered(self):
        from smr_phase79_quantitative_metric_schema import get_metric_aliases
        a=get_metric_aliases();self.assertIn("R&D_expense",a)
    def test_cannot_conclude(self):
        from smr_phase79_quantitative_metric_schema import get_metric_cannot_conclude
        cc=get_metric_cannot_conclude();self.assertGreater(len(cc.get("revenue",[])),0)
if __name__=="__main__":unittest.main()
