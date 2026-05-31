import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_depth_freshness_reliability_backlog import (
    build_source_depth_scores, build_freshness_audit,
    build_reliability_crosscheck, build_backlog_priority
)

class TestDepthScoring(unittest.TestCase):
    def test_sources_scored(self):
        result=build_source_depth_scores()
        self.assertGreater(result["phase91_source_depth_scoring"]["sources_scored"],15)
    def test_yfinance_top(self):
        result=build_source_depth_scores()
        yf=[s for s in result["phase91_source_depth_scoring"]["scores"] if s["source_id"]=="yfinance_financials"][0]
        self.assertGreaterEqual(yf["depth_score"],7)

class TestFreshness(unittest.TestCase):
    def test_audit_complete(self):
        result=build_freshness_audit()
        self.assertGreater(result["phase91_source_freshness_reality_audit"]["sources_audited"],5)
    def test_yfinance_low_staleness(self):
        result=build_freshness_audit()
        yf=[s for s in result["phase91_source_freshness_reality_audit"]["freshness_records"] if s["source_id"]=="yfinance_price"][0]
        self.assertEqual(yf["staleness_risk"],"very_low")

class TestReliability(unittest.TestCase):
    def test_gaps_found(self):
        result=build_reliability_crosscheck()
        self.assertGreater(result["phase91_reliability_vs_reality_crosscheck"]["reliability_gaps_found"],3)
    def test_catalog_flagged(self):
        result=build_reliability_crosscheck()
        catalog_claims=[c for c in result["phase91_reliability_vs_reality_crosscheck"]["crosscheck_records"] if "catalog" in c["registry_claim"]]
        self.assertGreater(len(catalog_claims),0)

class TestBacklog(unittest.TestCase):
    def test_10_items(self):
        result=build_backlog_priority()
        self.assertEqual(result["phase91_source_backlog_priority"]["backlog_items"],10)
    def test_order_contract_highest(self):
        result=build_backlog_priority()
        first=result["phase91_source_backlog_priority"]["priorities"][0]
        self.assertEqual(first["gap"],"order_contract_source")
        self.assertEqual(first["priority"],"highest")
    def test_has_phase92_96_recommendation(self):
        result=build_backlog_priority()
        self.assertIn("highest_priority",result["phase91_source_backlog_priority"]["phase92_96_recommendation"])
