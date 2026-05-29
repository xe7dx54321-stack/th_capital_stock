import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestWatchlistPacket(unittest.TestCase):
    def test_no_trade(self):
        from build_phase68_evidence_backed_watchlist_packet import build
        r = build('300308.SZ')
        pkt = r['evidence_backed_watchlist_packet']
        self.assertEqual(pkt['pending_created'], 0)
        self.assertEqual(pkt['paper_order_created'], 0)
        self.assertEqual(pkt['real_trade_created'], 0)

    def test_has_supported(self):
        from build_phase68_evidence_backed_watchlist_packet import build
        r = build('300308.SZ')
        pkt = r['evidence_backed_watchlist_packet']
        self.assertGreater(len(pkt['key_supported_judgments']), 0)

if __name__ == '__main__': unittest.main()
