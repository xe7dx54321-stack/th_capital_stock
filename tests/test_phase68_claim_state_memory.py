import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestClaimStateMemory(unittest.TestCase):
    def test_state_delta(self):
        from smr_claim_state_memory import build_claim_state
        rows = [
            {'claim_id': 'c1', 'claim_name': '800G_signal_supported', 'claim_status': 'supported',
             'supporting_evidence_count': 3, 'claim_limitation': 'test', 'cannot_conclude': [],
             'evidence_ids': ['e1']},
            {'claim_id': 'c2', 'claim_name': 'asp_trend_unconfirmed', 'claim_status': 'unconfirmed',
             'supporting_evidence_count': 0, 'claim_limitation': 'test', 'cannot_conclude': [],
             'evidence_ids': []},
        ]
        r = build_claim_state(rows)
        self.assertEqual(r['claims_total'], 2)
        self.assertEqual(r['newly_supported'], 1)
        self.assertEqual(r['still_unconfirmed'], 1)
        for c in r['rows']:
            if c['claim_name'] == '800G_signal_supported':
                self.assertEqual(c['status_delta'], 'newly_supported')

    def test_empty(self):
        from smr_claim_state_memory import build_claim_state
        r = build_claim_state([])
        self.assertEqual(r['claims_total'], 0)

if __name__ == '__main__': unittest.main()
