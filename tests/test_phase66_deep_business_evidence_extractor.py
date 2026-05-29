import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_deep_business_evidence_extractor import extract_deep_evidence

class TestDeepEvidenceExtractor(unittest.TestCase):
    def setUp(self):
        self.texts=[{"text":"公司800G光模块已批量出货，客户需求旺盛。" * 10,"source_type":"investor_relations_record","source_id":"s1"},
                    {"text":"1.6T产品研发进展顺利。" * 10,"source_type":"investor_relations_record","source_id":"s2"},
                    {"text":"营业收入增长。" * 50,"source_type":"annual_report","source_id":"s3"}]
        self.result=extract_deep_evidence(self.texts)
    def test_creates_evidence(self):
        self.assertGreater(self.result["evidence_created"],0)
    def test_quoted_span_present(self):
        for ev in self.result["rows"]:
            self.assertTrue(ev.get("quoted_span"),f"missing quoted_span for {ev.get('evidence_id')}")
    def test_limitation_present(self):
        for ev in self.result["rows"]:
            self.assertIn("limitation",ev)
            self.assertTrue(ev["limitation"],f"missing limitation for {ev.get('evidence_id')}")
    def test_cannot_conclude_present(self):
        for ev in self.result["rows"]:
            self.assertIn("cannot_conclude",ev)
            self.assertGreater(len(ev["cannot_conclude"]),0)
    def test_800G_not_confirms_revenue_share(self):
        for ev in self.result["rows"]:
            if ev.get("business_variable")=="800G_product_signal":
                self.assertIn("800G revenue share",ev.get("cannot_conclude",[]))
    def test_1_6T_not_confirms_mass_production(self):
        for ev in self.result["rows"]:
            if ev.get("business_variable")=="1_6T_product_signal":
                self.assertIn("1.6T revenue contribution",ev.get("cannot_conclude",[]))
    def test_demand_not_confirms_customer_share(self):
        for ev in self.result["rows"]:
            if ev.get("business_variable")=="customer_demand_signal":
                self.assertIn("customer share",ev.get("cannot_conclude",[]))
    def test_requires_human_review_present(self):
        for ev in self.result["rows"]:
            self.assertIn("requires_human_review",ev)
    def test_short_text_skipped(self):
        short=[{"text":"hi","source_type":"other","source_id":"s"}]
        r=extract_deep_evidence(short)
        self.assertEqual(r["evidence_created"],0)

if __name__=="__main__":unittest.main()
