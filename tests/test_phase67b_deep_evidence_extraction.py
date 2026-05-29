import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_deep_business_evidence_extractor import extract_deep_evidence
class TestPhase67bDeepEvidence(unittest.TestCase):
    def test_quoted_span_present(self):
        texts=[{"text":"公司800G光模块已批量出货，客户需求旺盛。"*10,"source_type":"investor_relations_record","source_id":"s1"}]
        de=extract_deep_evidence(texts)
        for ev in de["rows"]:
            self.assertTrue(ev.get("quoted_span"))
    def test_cannot_conclude_present(self):
        texts=[{"text":"公司800G光模块出货"*10,"source_type":"investor_relations_record","source_id":"s1"}]
        de=extract_deep_evidence(texts)
        for ev in de["rows"]:
            self.assertGreater(len(ev.get("cannot_conclude",[])),0)
    def test_800G_not_confirms_revenue_share(self):
        texts=[{"text":"800G产品出货顺利"*10,"source_type":"investor_relations_record","source_id":"s1"}]
        de=extract_deep_evidence(texts)
        for ev in de["rows"]:
            if ev.get("business_variable")=="800G_product_signal":
                self.assertIn("800G revenue share",ev.get("cannot_conclude",[]))
if __name__=="__main__":unittest.main()
