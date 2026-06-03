import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase121_source_candidate_registry import build_source_candidate_registry
def load_pending_sources():
 registry=build_source_candidate_registry()
 sources=registry["phase121_source_candidate_registry"]["sources"]
 pending=[s for s in sources]
 extra={"id":"transcript_guidance_manual","type":"transcript_guidance","market":"HK_US","desc":"Earnings call transcript aggregation","access":"manual_required","tickers":["09988.HK","00700.HK","NVDA","AVGO"]}
 pending.append(extra)
 return {"phase128_pending_source_loader":{"total":len(pending),"sources":pending,"mock_used":False,"fixture_used":False}}
