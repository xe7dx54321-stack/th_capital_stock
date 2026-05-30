import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestNormalizer(unittest.TestCase):
    def test_wan_yuan(self):
        from smr_phase79_report_metric_text_extractor import normalize_unit
        v,u=normalize_unit("68.52亿元");self.assertEqual(u,"亿元")
    def test_percent(self):
        from smr_phase79_report_metric_text_extractor import normalize_unit
        v,u=normalize_unit("52.3%");self.assertEqual(u,"%")
    def test_period(self):
        from smr_phase79_report_metric_text_extractor import normalize_period
        p=normalize_period("2024年年度报告");self.assertEqual(p,"2024FY")
    def test_period_q3(self):
        from smr_phase79_report_metric_text_extractor import normalize_period
        p=normalize_period("2025年第三季度报告");self.assertEqual(p,"2025Q3_YTD")
    def test_normalize_metrics(self):
        from smr_phase79_metric_normalizer import normalize_metrics
        metrics=[{"metric_name":"revenue","period":"2024FY","period_type":"annual","value_normalized":68.52,"unit_normalized":"亿元","extraction_confidence":"medium"}]
        r=normalize_metrics(metrics);self.assertEqual(r["phase79_metric_normalization"]["metrics_normalized"],1)
    def test_low_confidence_excluded(self):
        from smr_phase79_metric_normalizer import normalize_metrics
        metrics=[{"metric_name":"revenue","period":"2024FY","value_normalized":None,"extraction_confidence":"low"}]
        r=normalize_metrics(metrics);self.assertEqual(r["phase79_metric_normalization"]["metrics_normalized"],0)
if __name__=="__main__":unittest.main()
