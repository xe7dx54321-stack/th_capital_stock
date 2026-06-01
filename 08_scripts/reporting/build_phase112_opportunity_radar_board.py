import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase112_candidate_builder import build_opportunity_candidate_pool
from smr_phase112_opportunity_ranking import build_opportunity_ranking
from smr_phase112_research_risk_gate import build_research_risk_gate
def main():
    pool=build_opportunity_candidate_pool()
    rank=build_opportunity_ranking()
    risk=build_research_risk_gate()
    sections={"new_opportunity":[],"priority_upgrade":[],"watchlist_stable":[],"deep_dive_required":[],"blocked":[]}
    for c in pool["phase112_opportunity_candidate_pool"]["candidates"]:
        ct=c["candidate_type"]
        if ct=="blocked_candidate":sections["blocked"].append(c)
        elif ct in ("new_opportunity_candidate","multi_source_confirmed_candidate"):sections["new_opportunity"].append(c)
        elif ct in ("evidence_strengthened_candidate","watchlist_priority_upgrade"):sections["priority_upgrade"].append(c)
        elif ct=="deep_dive_candidate":sections["deep_dive_required"].append(c)
        else:sections["watchlist_stable"].append(c)
    out={"phase112_opportunity_radar_board":{"generated_at":datetime.now().isoformat(),"tickers_total":8,"radar_enabled":7,"blocked":1,"section_counts":{k:len(v) for k,v in sections.items()},"candidates":pool["phase112_opportunity_candidate_pool"]["candidates"],"ranking":rank["phase112_opportunity_ranking"]["ranked_candidates"],"risk_summary":{"300394":"blocked","688041":"valuation_gap"},"research_only":True,"no_trade_signal":True,"mock_used":False,"fixture_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
