import phase52_helpers
import unittest,json
from build_phase52_watchlist_intelligence_packet import build, _md

class Phase52PacketTests(unittest.TestCase):
    def test_packet_keys(self):
        r=build(None,"300308.SZ"); p=r["watchlist_intelligence_packet"]
        for k in ["aggregator","human_thesis_summary","tracking_decision","boundary"]:
            self.assertIn(k,p)
    def test_boundary(self):
        r=build(None,"300308.SZ"); b=r["watchlist_intelligence_packet"]["boundary"]
        self.assertEqual(b["pending_created"],0)
        self.assertEqual(b["paper_order_created"],0)
    def test_markdown_output(self):
        r=build(None,"300308.SZ"); md=_md(r)
        self.assertIn("Why Not Pending",md)
    def test_json_output(self):
        r=build(None,"300308.SZ")
        s=json.dumps(r,ensure_ascii=False)
        self.assertIn("continue_tracking",s)
if __name__=="__main__": unittest.main()
