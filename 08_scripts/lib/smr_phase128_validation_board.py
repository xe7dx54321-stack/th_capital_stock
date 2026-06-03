import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_pending_network_closeout import build_pending_network_closeout

def build_validation_board(skip_network=False):
    classified=classify_availability(skip_network)["phase128_availability_classifier"]
    closeout=build_pending_network_closeout(skip_network)["phase128_pending_network_closeout"]
    sections={"available":[],"metadata_only":[],"blocked":[],"manual_required":[],"api_key_required":[],"unsupported":[],"degraded":[]}
    for c in classified["results"]:
        sec=c["classification"]
        if sec in sections:
            sections[sec].append({"source_id":c["source_id"],"market":c["market"],"tickers":c.get("tickers",[]),"note":c.get("note",""),"error":c.get("error")})
    return {"phase128_validation_board":{"tickers_total":8,"sources_probed":classified["total"],"sections":{k:{"count":len(v),"items":v} for k,v in sections.items() if v},"pending_before":closeout["pending_network_before"],"pending_after":closeout["pending_network_after"],"not_trade_board":True,"mock_used":False,"fixture_used":False}}
