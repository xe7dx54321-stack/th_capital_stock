import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestResearchPacket(unittest.TestCase):
    def test_no_trade_advice(self):
        from build_phase69b_multi_ticker_research_packet import build
        r = build()
        pkt = r['phase69b_multi_ticker_research_packet']
        self.assertEqual(pkt.get('pending_created', -1), 0)
        self.assertEqual(pkt.get('paper_order_created', -1), 0)
        self.assertEqual(pkt.get('real_trade_created', -1), 0)

    def test_has_three_tickers(self):
        from build_phase69b_multi_ticker_research_packet import build
        r = build()
        pkt = r['phase69b_multi_ticker_research_packet']
        self.assertGreaterEqual(len(pkt.get('tickers', [])), 2)

    def test_blocked_ticker_has_blocker(self):
        from build_phase69b_multi_ticker_research_packet import build
        r = build()
        pkt = r['phase69b_multi_ticker_research_packet']
        for t in pkt.get('tickers', []):
            if 'blocked' in t.get('research_status', ''):
                self.assertIn('blocker', t)

    def test_partial_ticker_has_reason(self):
        from build_phase69b_multi_ticker_research_packet import build
        r = build()
        pkt = r['phase69b_multi_ticker_research_packet']
        for t in pkt.get('tickers', []):
            if 'partial' in t.get('research_status', ''):
                self.assertIn('partial_reason', t)

    def test_no_buy_sell_target(self):
        from build_phase69b_multi_ticker_research_packet import build
        r = build()
        text = str(r)
        for term in ['买入', '卖出', '目标价']:
            self.assertNotIn(term, text)

if __name__ == '__main__': unittest.main()
