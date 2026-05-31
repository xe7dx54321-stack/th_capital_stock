import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_dimension_coverage import build_dimension_coverage_matrix

class TestDimensions(unittest.TestCase):
    def test_15_dimensions(self):
        result=build_dimension_coverage_matrix()
        self.assertEqual(result["phase91_information_dimension_coverage_matrix"]["dimensions_audited"],15)
    def test_gaps_exist(self):
        result=build_dimension_coverage_matrix()
        gap=result["phase91_hard_data_gap_report"]
        self.assertGreater(gap["total_gaps"],5)
    def test_order_contract_is_gap(self):
        result=build_dimension_coverage_matrix()
        gap_dims=[g["dimension"] for g in result["phase91_hard_data_gap_report"]["gaps"]]
        self.assertIn("order_contract",gap_dims)
    def test_300394_all_blocked(self):
        result=build_dimension_coverage_matrix()
        for d in result["phase91_information_dimension_coverage_matrix"]["dimension_coverage"]:
            if d["dimension"]!="price_daily": self.assertEqual(d["ticker_detail"].get("300394.SZ"),"blocked")
    def test_financial_structured_covered(self):
        result=build_dimension_coverage_matrix()
        for d in result["phase91_information_dimension_coverage_matrix"]["dimension_coverage"]:
            if d["dimension"]=="financial_structured":
                self.assertGreaterEqual(d["coverage"]["covered"],6)
