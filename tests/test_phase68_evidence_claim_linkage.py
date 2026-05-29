import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestClaimLinkage(unittest.TestCase):
    def test_linkage(self):
        from smr_evidence_claim_linkage_memory import build_claim_linkage
        ev = [
            {'evidence_id': 'e1', 'business_variable': '800G_product_signal', 'source_id': 's1',
             'source_type': 't', 'title': 't', 'evidence_strength': 'financial_report_context',
             'confidence': 'low', 'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
             'requires_human_review': False},
            {'evidence_id': 'e2', 'business_variable': 'asp_price_signal', 'source_id': 's2',
             'source_type': 't', 'title': 't', 'evidence_strength': 'review_required',
             'confidence': 'low', 'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
             'requires_human_review': True},
        ]
        r = build_claim_linkage(ev)
        self.assertGreaterEqual(r['claims_checked'], 2)
        self.assertIn('asp_trend_unconfirmed', [c['claim_name'] for c in r['rows']])

    def test_supported_not_confirmed(self):
        from smr_evidence_claim_linkage_memory import build_claim_linkage
        ev = [{'evidence_id': 'e1', 'business_variable': '800G_product_signal', 'source_id': 's1',
               'source_type': 't', 'title': 't', 'evidence_strength': 'financial_report_context',
               'confidence': 'low', 'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
               'requires_human_review': False}]
        r = build_claim_linkage(ev)
        for c in r['rows']:
            if c['claim_name'] == '800G_signal_supported':
                self.assertEqual(c['claim_status'], 'supported')
                self.assertIn('不确认', c['claim_limitation'])

    def test_unconfirmed_retained(self):
        from smr_evidence_claim_linkage_memory import build_claim_linkage
        r = build_claim_linkage([])
        names = [c['claim_name'] for c in r['rows']]
        self.assertIn('customer_share_unconfirmed', names)

if __name__ == '__main__': unittest.main()
