import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestMetricExtractor(unittest.TestCase):
    def test_extract(self):
        from smr_phase79_report_metric_text_extractor import extract_metrics_from_text
        from smr_phase79_quantitative_metric_schema import get_metric_aliases
        text="公司2024年实现营业收入68.52亿元同比增长52.3%毛利率52.3%研发费用12.8亿元"
        aliases=get_metric_aliases()
        r=extract_metrics_from_text(text,aliases,"2024年年度报告","annual_report")
        self.assertGreater(len(r),0)
    def test_revenue_matched(self):
        from smr_phase79_report_metric_text_extractor import extract_metrics_from_text
        from smr_phase79_quantitative_metric_schema import get_metric_aliases
        text="营业收入68.52亿元"
        r=extract_metrics_from_text(text,get_metric_aliases(),"2024年年度报告","annual_report")
        rev=[m for m in r if m["metric_name"]=="revenue"];self.assertEqual(len(rev),1)
    def test_percent_matched(self):
        from smr_phase79_report_metric_text_extractor import extract_metrics_from_text
        from smr_phase79_quantitative_metric_schema import get_metric_aliases
        text="毛利率52.3%研发费用率18.7%"
        r=extract_metrics_from_text(text,get_metric_aliases(),"2024年年度报告","annual_report")
        gm=[m for m in r if m["metric_name"]=="gross_margin"];self.assertEqual(len(gm),1)
if __name__=="__main__":unittest.main()
