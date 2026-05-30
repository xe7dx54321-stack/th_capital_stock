import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestQuantEvidence(unittest.TestCase):
    def test_build(self):
        from smr_phase79_quantitative_evidence_builder import build_quantitative_evidence
        metrics=[{"metric_name":"revenue","period":"2024FY","value_normalized":68.52,"unit_normalized":"亿元"}]
        r=build_quantitative_evidence(metrics);qe=r["phase79_quantitative_evidence"]
        self.assertGreater(qe["quantitative_evidence_created"],0)
    def test_each_has_limitation(self):
        from smr_phase79_quantitative_evidence_builder import build_quantitative_evidence
        metrics=[{"metric_name":"revenue","period":"2024FY","value_normalized":68.52,"unit_normalized":"亿元"},{"metric_name":"gross_margin","period":"2024FY","value_normalized":52.3,"unit_normalized":"%"}]
        r=build_quantitative_evidence(metrics);rows=r["phase79_quantitative_evidence"]["rows"]
        for row in rows:self.assertIn("limitation",row)
    def test_revenue_not_customer(self):
        from smr_phase79_quantitative_evidence_builder import build_quantitative_evidence
        metrics=[{"metric_name":"revenue","period":"2024FY","value_normalized":68.52,"unit_normalized":"亿元"}]
        r=build_quantitative_evidence(metrics);row=r["phase79_quantitative_evidence"]["rows"][0]
        self.assertIn("customer_share",row["cannot_conclude"])
if __name__=="__main__":unittest.main()
