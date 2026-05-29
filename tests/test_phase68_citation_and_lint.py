import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestCitationMap(unittest.TestCase):
    def test_citation_map(self):
        from smr_brief_evidence_citation_map import build_citation_map
        from smr_evidence_claim_linkage_memory import build_claim_linkage
        ev = [{'evidence_id': 'e1', 'business_variable': '800G_product_signal', 'source_id': 's1',
               'source_type': 't', 'source_title': 'T', 'evidence_strength': 'financial_report_context',
               'confidence': 'low', 'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
               'requires_human_review': False}]
        cl = build_claim_linkage(ev)
        bd = {'supported_judgments': ['800G_signal_supported']}
        r = build_citation_map(bd, cl, ev)
        self.assertGreater(r['brief_sections'], 0)

class TestQualityLint(unittest.TestCase):
    def test_clean_brief_passes(self):
        from smr_internal_brief_quality_lint import lint_brief
        text = '# 老板摘要\n\n当前已看到的信息\n\n真实证据支撑\n\n不构成交易建议'
        r = lint_brief(text)
        self.assertEqual(r['overall_status'], 'pass')
        self.assertEqual(r['system_terms_found'], 0)
        self.assertEqual(r['trade_advice_terms_found'], 0)

    def test_system_terms_detected(self):
        from smr_internal_brief_quality_lint import lint_brief
        text = 'dashboard shows candidate pending validation'
        r = lint_brief(text)
        self.assertGreater(r['system_terms_found'], 0)

    def test_trade_terms_detected(self):
        from smr_internal_brief_quality_lint import lint_brief
        text = '建议买入 目标价100'
        r = lint_brief(text)
        self.assertGreater(r['trade_advice_terms_found'], 0)

    def test_teaching_detected(self):
        from smr_internal_brief_quality_lint import lint_brief
        text = '建议关注未来趋势'
        r = lint_brief(text)
        self.assertGreater(r['teaching_phrases_found'], 0)

if __name__ == '__main__': unittest.main()
