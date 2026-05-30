import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestResearchPacket(unittest.TestCase):
 def test_no_trade(self):
  from build_phase73_research_packet import build
  r=build();p=r["phase73_research_packet"]
  self.assertEqual(p.get("pending_created",-1),0)
 def test_blocked_has_blocker(self):
  from build_phase73_research_packet import build
  r=build();p=r["phase73_research_packet"]
  for t in p["tickers"]:
   if "blocked" in t.get("research_status",""):self.assertIn("blocker",t)
 def test_no_buy_sell(self):
  from build_phase73_research_packet import build
  r=build();text=str(r)
  for term in ["买入","卖出","目标价"]:self.assertNotIn(term,text)
if __name__=="__main__":unittest.main()
