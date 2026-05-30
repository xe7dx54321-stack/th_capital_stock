import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestStructuredLoader(unittest.TestCase):
    def test_load(self):from smr_phase80_structured_financial_metric_loader import load_structured_metrics;r=load_structured_metrics();rr=r["phase80_structured_metric_loader"];self.assertGreater(rr["structured_metrics_loaded"],0)
    def test_no_mock(self):from smr_phase80_structured_financial_metric_loader import load_structured_metrics;r=load_structured_metrics();self.assertFalse(r["phase80_structured_metric_loader"]["mock_used"])
    def test_has_source(self):from smr_phase80_structured_financial_metric_loader import load_structured_metrics;r=load_structured_metrics();rows=r["phase80_structured_metric_loader"]["rows"];self.assertTrue(all("source" in row for row in rows))
if __name__=="__main__":unittest.main()
